"""システム構成図（site/assets/img/system.svg）を書き出す。

スマホで読める縦長の図にするため、手で座標を決めている。
中身を変えたら `python tools/diagram/make_system_svg.py` で書き出し直す。

根拠:
- 走行部（th）: reference/images/tmシステム構成図.png、site/move/tech.html の表
- 昇降部（hf）・カメラ部（ve）: hve-system の redesign/v2 ブランチ
  docs/plan/spec/Spec.md §5、docs/plan/detailed/DetailedDesign.md §2、DetailedDesign-hardware.md
"""

from svgkit import Diagram

W, H = 380, 760
COL_X = {1: 14, 2: 128, 3: 242}  # 箱の左端
BOX_W = 100

d = Diagram(W, H, "高見舎 TAKA-MEER のシステム構成図")
text, box, line, group = d.text, d.box, d.line, d.group
parts = d.parts


def cbox(col, y, title, sub, ctrl=False):
    box(COL_X[col], y, BOX_W, title, sub, ctrl)


# 凡例
LEG_Y = 14
line([(14, LEG_Y), (38, LEG_Y)], end=False)
text(44, LEG_Y + 4, "有線", "leg", "start")
line([(80, LEG_Y), (104, LEG_Y)], cls="wifi")
text(110, LEG_Y + 4, "Wi-Fi", "leg", "start")
line([(152, LEG_Y), (176, LEG_Y)], cls="mech")
text(182, LEG_Y + 4, "機械", "leg", "start")
parts.append(f'<rect x="218" y="{LEG_Y - 6}" width="18" height="12" rx="2" class="box ctrl"/>')
text(242, LEG_Y + 4, "コンピュータ・マイコン", "leg", "start")

# 機体の外
box(14, 34, 162, "PC", "ROS 2・走行の処理", ctrl=True)
box(190, 34, 152, "操作端末", "ブラウザで操作画面を開く")
line([(150, 74), (150, 122)], cls="wifi")
line([(206, 74), (206, 122)], cls="wifi")
text(178, 88, "Wi-Fi", "lbl")

# 走行部 th
group(94, 312, "走行部", "th", "電源：機体の24V系統")
R1, R2, R3 = 122, 186, 250
cbox(1, R1, "RPLIDAR S1", "2D-LiDAR・全周")
box(COL_X[2], R1, 112, "Raspberry Pi 4", "Wi-Fi AP・中継", ctrl=True)
cbox(1, R2, "IMU", "BNO055")
cbox(2, R2, "ESP32", "走行の速度制御", ctrl=True)
cbox(1, R3, "非常停止ボタン", "駆動の電源を切る")
cbox(2, R3, "MD10C ×2", "モータードライバ")
cbox(3, R3, "クローラー", "左右モーター")
line([(114, R1 + 20), (128, R1 + 20)])
line([(114, R2 + 20), (128, R2 + 20)])
line([(178, R1 + 40), (178, R2)], start=True)
text(184, R1 + 56, "USBシリアル", "lbl", "start")
line([(178, R2 + 40), (178, R3)])
line([(228, R3 + 20), (242, R3 + 20)])
line([(114, R3 + 20), (128, R3 + 20)])
line([(292, R3), (292, R2 + 20), (228, R2 + 20)])
text(288, R2 + 54, "エンコーダ", "lbl", "end")

# Wi-Fi の幹線（Raspberry Pi 4 のアクセスポイントから昇降部・カメラ部へ）
RAIL = 366
L1, C1 = 364, 544
line([(240, R1 + 20), (RAIL, R1 + 20), (RAIL, C1 + 20), (248, C1 + 20)], cls="wifi")
line([(RAIL, 324), (64, 324), (64, L1)], cls="wifi")
text(370, 330, "Wi-Fi（アクセスポイント経由）", "lbl", "start", ' transform="rotate(90 370 330)"')

# 昇降部 hf
group(336, 490, "昇降部", "hf ／ hve-system", "電源：機体の24V系統（モーターは非常停止で切れる）")
L2 = L1 + 64
cbox(1, L1, "ESP32", "昇降制御・画面", ctrl=True)
cbox(2, L1, "MD10C", "モータードライバ")
cbox(3, L1, "昇降モーター", "パワーウィンドウ用")
cbox(1, L2, "下端スイッチ", "リミットスイッチ")
cbox(2, L2, "エンコーダ", "E6A2-CW3C・高さ")
line([(114, L1 + 20), (128, L1 + 20)])
line([(228, L1 + 20), (242, L1 + 20)])
line([(40, L2), (40, L1 + 40)])
line([(160, L2), (160, L2 - 12), (90, L2 - 12), (90, L1 + 40)])
line([(292, L1 + 40), (292, L2 + 20), (228, L2 + 20)], cls="mech")
text(298, L2 + 4, "ロープの", "lbl", "start")
text(298, L2 + 15, "巻き取り軸", "lbl", "start")

text(352, 507, "カメラ部 ⇄ 昇降部：昇降の命令と天井の距離 ／ 高さと状態", "lbl acc", "end")

# カメラ部 ve
group(516, 744, "カメラ部", "ve ／ hve-system", "電源：モバイルバッテリー（非常停止で切れない）")
C2, C3 = C1 + 64, C1 + 128
box(108, C1, 140, "M5Stack UnitV2", "カメラ・映像配信・画面", ctrl=True)
box(108, C2, 140, "Arduino UNO", "向きの制御・距離の計測", ctrl=True)
cbox(1, C3, "28BYJ-48", "ヨー（左右）")
cbox(2, C3, "MG996R", "ピッチ（上下）")
cbox(3, C3, "SRF02", "天井までの距離")
line([(178, C1 + 40), (178, C2)], start=True)
text(184, C1 + 56, "UART", "lbl", "start")
line([(178, C2 + 40), (178, C3)])
line([(178, C2 + 52), (64, C2 + 52), (64, C3)])
line([(178, C2 + 52), (292, C2 + 52), (292, C3)], end=False)
text(70, C2 + 48, "ULN2003経由", "lbl", "start")
text(286, C2 + 48, "I2C", "lbl", "end")

d.write("system.svg")
