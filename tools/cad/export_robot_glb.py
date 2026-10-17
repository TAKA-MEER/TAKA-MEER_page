"""SolidWorks の統合アセンブリから、サイトの3Dビューア用 glb を書き出す。

Windows（SolidWorks あり）専用。pywin32 と numpy が必要。

    python tools/cad/export_robot_glb.py <統合設計.SLDASM のパス>

1. SolidWorks でアセンブリを読み取り専用で開き、glb で書き出す
2. 部品を「固定部 base / 昇降1段目 stage1 / 昇降2段目 stage2」に振り分ける（STAGES）
3. スマホ向けに軽量化する（テクスチャ削除、同形状メッシュの共有、頂点の量子化）
4. site/assets/models/robot.glb に保存する

CAD の部品構成が変わったら STAGES を直す。どれにも当たらない部品は base になる。
"""

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import struct
import sys
import tempfile

import numpy as np

# 部品の振り分け。パスは SolidWorks のツリー上の名前（Name2）で、* はワイルドカード。
# サブアセンブリに当たった場合は、その中身ごと同じグループになる。
STAGES = {
    # 1段目：中央の補助パーツと、それに付くレール・ブロック（距離制限2で固定部に対して動く）
    "stage1": [
        "後期本体設計-*/後期中央補助パーツ2-*",
        "後期本体設計-*/HFS5-2020-1200-1",
        "後期本体設計-*/HFS5-2020-1200-4",
        "後期本体設計-*/HFS5-2020-1200-5",
        "後期本体設計-*/後期設計1-*",
        "後期本体設計-*/後期設計4-*",
        "後期本体設計-*/後期設計5-*",
        "後期本体設計-*/後期設計7-*",
    ],
    # 2段目：1250mm レールと、それに付く部品（距離制限1で1段目に対して動く）
    "stage2": [
        "後期本体設計-*/HFS5-2020-1250-*",
        "後期設計3-*",
    ],
}

# 各段の伸び（m）。CAD の距離制限合致の最大値
TRAVEL = {"stage1": 0.988, "stage2": 0.996}

OUT_DEFAULT = os.path.join(os.path.dirname(__file__), "..", "..", "site", "assets", "models", "robot.glb")


# ---- SolidWorks ----

def export_from_solidworks(asm_path, glb_path):
    import pythoncom
    import win32com.client

    sw = win32com.client.Dispatch("SldWorks.Application")
    errors = win32com.client.VARIANT(16387, 0)  # VT_BYREF | VT_I4
    warnings = win32com.client.VARIANT(16387, 0)
    # swDocASSEMBLY = 2, swOpenDocOptions_Silent | ReadOnly = 1 | 2
    doc = sw.OpenDoc6(asm_path, 2, 3, "", errors, warnings)
    if doc is None:
        sys.exit(f"アセンブリを開けません: {asm_path}（エラー {errors.value}）")

    root = doc.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
    tree = component_tree(root)

    # 古い doc.SaveAs3 では、ミラー部品（片側のクローラー）の形状が空で書き出されるため Extension.SaveAs3 を使う
    # swSaveAsOptions_Silent | Copy = 1 | 2
    nothing = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
    ok = doc.Extension.SaveAs3(glb_path, 0, 3, nothing, nothing, errors, warnings)
    if not ok or not os.path.exists(glb_path):
        sys.exit(f"glb の書き出しに失敗しました（エラー {errors.value}）")
    return tree


def com_call(obj, name):
    """遅延バインディングでは引数なしのメソッドがプロパティとして返ることがあるので両方に対応する"""
    value = getattr(obj, name)
    return value() if callable(value) else value


def component_tree(comp):
    """表示される部品だけを、ツリーの順に (Name2, 子) で返す"""
    out = []
    for child in com_call(comp, "GetChildren") or []:
        if com_call(child, "IsSuppressed") or not child.Visible:
            continue
        out.append((child.Name2, component_tree(child)))
    return out


# ---- glb の読み書き ----

def read_glb(path):
    data = open(path, "rb").read()
    json_len = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + json_len])
    bin_start = 20 + json_len + 8
    return gltf, data[bin_start:]


def write_glb(path, gltf, binary):
    js = json.dumps(gltf, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(js) + 8 + len(binary)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(binary), 0x004E4942) + binary)


def accessor_array(gltf, binary, index):
    acc = gltf["accessors"][index]
    view = gltf["bufferViews"][acc["bufferView"]]
    dtype = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}[acc["componentType"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    offset = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride", 0) or np.dtype(dtype).itemsize * width
    raw = np.frombuffer(binary, np.uint8, count=stride * (acc["count"] - 1) + np.dtype(dtype).itemsize * width, offset=offset)
    rows = np.lib.stride_tricks.as_strided(raw, (acc["count"], np.dtype(dtype).itemsize * width), (stride, 1))
    return np.ascontiguousarray(rows).view(dtype).reshape(acc["count"], width).squeeze(-1 if width == 1 else None)


def node_matrix(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=np.float64).reshape(4, 4).T
    t = np.eye(4)
    t[:3, 3] = node.get("translation", [0, 0, 0])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    r = np.eye(4)
    r[:3, :3] = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    s = np.diag(list(node.get("scale", [1, 1, 1])) + [1])
    return t @ r @ s


# ---- 部品の振り分け ----

def classify(gltf, tree):
    """glb のメッシュノードごとに (ワールド行列, メッシュ番号, グループ, 部品名) を返す。

    SolidWorks の glb は日本語のノード名が文字化けするので、名前ではなく
    ツリーの並び順で SolidWorks の部品と対応づける。
    """
    nodes = gltf["nodes"]
    roots = [i for i in gltf["scenes"][gltf.get("scene", 0)]["nodes"] if "camera" not in nodes[i]]
    if len(roots) != 1:
        sys.exit(f"glb のルートノードが想定と違います（{len(roots)} 個）")

    def group_of(name, inherited):
        if inherited != "base":
            return inherited
        for group, patterns in STAGES.items():
            if any(fnmatch.fnmatchcase(name, p) for p in patterns):
                return group
        return "base"

    result = []
    hits = {p: 0 for patterns in STAGES.values() for p in patterns}

    def walk(node_index, comps, parent_matrix, inherited):
        node = nodes[node_index]
        children = node.get("children", [])
        if len(children) != len(comps):
            sys.exit(f"glb と SolidWorks の部品数が合いません: {node.get('name')}（{len(children)} と {len(comps)}）")
        for child_index, (name, sub) in zip(children, comps):
            child = nodes[child_index]
            glb_name = child.get("name", "")
            leaf = name.split("/")[-1]
            if glb_name.isascii() and not (glb_name == leaf or glb_name.endswith(leaf) or leaf.startswith(glb_name)):
                sys.exit(f"glb と SolidWorks の部品の並びが合いません: {glb_name} / {name}")
            group = group_of(name, inherited)
            for patterns in STAGES.values():
                for p in patterns:
                    if fnmatch.fnmatchcase(name, p):
                        hits[p] += 1
            matrix = parent_matrix @ node_matrix(child)
            if "mesh" in child:
                if gltf["meshes"][child["mesh"]]["primitives"]:
                    result.append((matrix, child["mesh"], group, name))
                else:
                    print(f"注意: {name} の形状が空で書き出されました（3D表示に出ません）", file=sys.stderr)
            walk(child_index, sub, matrix, group)

    walk(roots[0], tree, node_matrix(nodes[roots[0]]), "base")
    for p, n in hits.items():
        if n == 0:
            print(f"注意: STAGES の {p} に当たる部品がありません", file=sys.stderr)
    return result


# ---- 軽量化して組み立て直す ----

def build(gltf, binary, instances):
    out = {
        "asset": {"version": "2.0", "generator": "TAKA-MEER export_robot_glb.py"},
        "extensionsUsed": ["KHR_mesh_quantization"],
        "extensionsRequired": ["KHR_mesh_quantization"],
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [],
        "meshes": [],
        "materials": [],
        "accessors": [],
        "bufferViews": [],
        "buffers": [{"byteLength": 0}],
    }
    blob = bytearray()

    def add_view(array, target, stride=None):
        blob.extend(b"\0" * (-len(blob) % 4))
        view = {"buffer": 0, "byteOffset": len(blob), "byteLength": array.nbytes, "target": target}
        if stride:
            view["byteStride"] = stride
        blob.extend(array.tobytes())
        out["bufferViews"].append(view)
        return len(out["bufferViews"]) - 1

    # 材質は色・金属感・粗さだけ残す（テクスチャと透過の拡張は捨てる）
    material_map = {}

    def material(index):
        src = gltf["materials"][index] if index is not None else {}
        pbr = src.get("pbrMetallicRoughness", {})
        key = (
            tuple(round(c, 3) for c in pbr.get("baseColorFactor", [0.8, 0.8, 0.8, 1])[:3]),
            # ビューアは環境マップを使わないので、金属を強くすると黒く見える。上限を設ける
            round(min(pbr.get("metallicFactor", 0.0), 0.3), 2),
            round(pbr.get("roughnessFactor", 0.6), 2),
        )
        if key not in material_map:
            out["materials"].append({
                "pbrMetallicRoughness": {
                    "baseColorFactor": list(key[0]) + [1],
                    "metallicFactor": key[1],
                    "roughnessFactor": key[2],
                },
            })
            material_map[key] = len(out["materials"]) - 1
        return material_map[key]

    # 同じ形状のメッシュ（ブラケットなど）は1つにまとめて共有する
    mesh_cache = {}

    def quantized_mesh(mesh_index):
        src = gltf["meshes"][mesh_index]
        prims = []
        for p in src["primitives"]:
            pos = accessor_array(gltf, binary, p["attributes"]["POSITION"]).astype(np.float64)
            nrm = accessor_array(gltf, binary, p["attributes"]["NORMAL"]).astype(np.float64)
            idx = accessor_array(gltf, binary, p["indices"]) if "indices" in p else np.arange(len(pos))
            prims.append((pos, nrm, idx, p.get("material")))
        key = hashlib.md5(b"".join(a.tobytes() for pos, nrm, idx, m in prims for a in (pos, idx)) + repr([m for *_, m in prims]).encode()).hexdigest()
        if key in mesh_cache:
            return mesh_cache[key]

        all_pos = np.concatenate([pos for pos, *_ in prims])
        lo, hi = all_pos.min(axis=0), all_pos.max(axis=0)
        center = (lo + hi) / 2
        half = max(float((hi - lo).max()) / 2, 1e-9)  # 法線が歪まないよう等倍で量子化
        primitives = []
        for pos, nrm, idx, mat in prims:
            q = np.zeros((len(pos), 4), np.int16)
            q[:, :3] = np.round((pos - center) / half * 32767)
            n = np.zeros((len(nrm), 4), np.int8)
            n[:, :3] = np.round(nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9) * 127)
            idx = idx.astype(np.uint16 if len(pos) < 65536 else np.uint32)
            out["accessors"].append({
                "bufferView": add_view(q, 34962, 8), "componentType": 5122, "normalized": True,
                "count": len(pos), "type": "VEC3",
                "min": q[:, :3].min(axis=0).tolist(), "max": q[:, :3].max(axis=0).tolist(),
            })
            pos_acc = len(out["accessors"]) - 1
            out["accessors"].append({
                "bufferView": add_view(n, 34962, 4), "componentType": 5120, "normalized": True,
                "count": len(nrm), "type": "VEC3",
            })
            nrm_acc = len(out["accessors"]) - 1
            out["accessors"].append({
                "bufferView": add_view(idx, 34963), "componentType": 5123 if idx.dtype == np.uint16 else 5125,
                "count": len(idx), "type": "SCALAR",
            })
            primitives.append({
                "attributes": {"POSITION": pos_acc, "NORMAL": nrm_acc},
                "indices": len(out["accessors"]) - 1,
                "material": material(mat),
            })
        out["meshes"].append({"primitives": primitives})
        dequant = np.eye(4)
        dequant[:3, :3] *= half
        dequant[:3, 3] = center
        mesh_cache[key] = (len(out["meshes"]) - 1, dequant, lo, hi)
        return mesh_cache[key]

    # ロボット全体の外形を求め、床（最下端）を y=0、平面の中心を原点にそろえる
    corners = []
    for matrix, mesh_index, *_ in instances:
        _, _, lo, hi = quantized_mesh(mesh_index)
        box = np.array([[x, y, z, 1] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        corners.append((matrix @ box.T).T[:, :3])
    corners = np.concatenate(corners)
    lo, hi = corners.min(axis=0), corners.max(axis=0)
    shift = np.array([-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2])

    def add_node(node):
        out["nodes"].append(node)
        return len(out["nodes"]) - 1

    root = add_node({
        "name": "robot",
        "translation": shift.tolist(),
        "extras": {"travel": [TRAVEL["stage1"], TRAVEL["stage2"]], "size": (hi - lo).round(3).tolist(),
                   "exported": datetime.date.today().isoformat()},
        "children": [],
    })
    groups = {}
    for name in ("base", "stage1", "stage2"):
        groups[name] = add_node({"name": name, "children": []})
    out["nodes"][root]["children"] = [groups["base"], groups["stage1"]]
    out["nodes"][groups["stage1"]]["children"].append(groups["stage2"])

    counts = {name: 0 for name in groups}
    for matrix, mesh_index, group, _ in instances:
        mesh, dequant, *_ = quantized_mesh(mesh_index)
        m = matrix @ dequant
        out["nodes"][groups[group]]["children"].append(add_node({"mesh": mesh, "matrix": m.T.reshape(-1).tolist()}))
        counts[group] += 1

    out["buffers"][0]["byteLength"] = len(blob)
    return out, bytes(blob), counts, hi - lo


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("assembly", help="統合設計.SLDASM のパス")
    parser.add_argument("--out", default=OUT_DEFAULT, help="出力先（既定: site/assets/models/robot.glb）")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        raw_path = os.path.join(tmp, "raw.glb")
        tree = export_from_solidworks(os.path.abspath(args.assembly), raw_path)
        gltf, binary = read_glb(raw_path)
        raw_size = os.path.getsize(raw_path)

    instances = classify(gltf, tree)
    out, blob, counts, size = build(gltf, binary, instances)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    write_glb(args.out, out, blob)

    print(f"書き出し: {os.path.abspath(args.out)}")
    print(f"サイズ: {raw_size / 1e6:.1f} MB → {os.path.getsize(args.out) / 1e6:.2f} MB")
    print(f"外形（幅・高さ・奥行, m）: {size.round(3).tolist()}")
    print("部品数: " + ", ".join(f"{k} {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
