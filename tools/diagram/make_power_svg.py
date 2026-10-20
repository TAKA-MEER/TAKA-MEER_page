"""電源構成図（site/assets/img/power.svg）を書き出す。

中身を変えたら `python tools/diagram/make_power_svg.py` で書き出し直す。

根拠:
- reference/images/電源構成図.png（モータドライバ1〜3、「TH ラズパイ」「HF ESP32」）
- ドライバ3台の割り当て（走行の左右・昇降）: system.svg と同じ（走行 MD10C ×2、昇降 MD10C）
- カメラ部はモバイルバッテリー給電で非常停止の対象外: reference/robot-overview.md
"""

from svgkit import Diagram

W, H = 380, 524
COL_X = {1: 14, 2: 128, 3: 242}  # 下段の3列の左端
LEFT, RIGHT, HALF_W = 14, 217, 150  # 上段の2列

d = Diagram(W, H, "高見舎 TAKA-MEER の電源構成図")

d.box(30, 14, 140, "電源", "機体の24V系統")
d.box(210, 14, 140, "スイッチ", "電源を入れる")
d.box(115, 78, 150, "電源基板", "系統を分ける")
d.line([(100, 54), (100, 66), (170, 66), (170, 78)])
d.line([(280, 54), (280, 66), (210, 66), (210, 78)])

# 左：制御系（非常停止で切れない）
d.box(LEFT, 142, HALF_W, "DCDCコンバータ", "電圧を下げる")
d.line([(160, 118), (160, 130), (89, 130), (89, 142)])
d.box(40, 206, 124, "Raspberry Pi 4", "走行部", ctrl=True)
d.box(40, 270, 124, "ESP32", "昇降部の制御", ctrl=True)
d.line([(26, 182), (26, 226), (40, 226)])
d.line([(26, 226), (26, 290), (40, 290)])

# 右：駆動系（非常停止ボタンを通る）
d.box(RIGHT, 142, HALF_W, "非常停止ボタン", "押すと下の電源を切る")
d.line([(220, 118), (220, 130), (292, 130), (292, 142)])
d.box(RIGHT, 206, HALF_W, "分岐ケーブル", "3台に分ける")
d.line([(292, 182), (292, 206)])

d.parts.append('<rect x="4" y="322" width="372" height="164" rx="8" class="grp"/>')
d.text(14, 340, "非常停止ボタンで電源が切れる", "gname", "start")
d.line([(292, 246), (292, 352)], end=False)
d.line([(64, 352), (292, 352)], end=False)
for col, (role, motor, motor_sub) in zip(
    (1, 2, 3),
    (("走行・左", "クローラー", "左モーター"),
     ("走行・右", "クローラー", "右モーター"),
     ("昇降", "昇降モーター", "パワーウィンドウ用")),
):
    x = COL_X[col]
    cx = x + 50
    d.line([(cx, 352), (cx, 364)])
    d.box(x, 364, 100, "MD10C", role)
    d.line([(cx, 404), (cx, 428)])
    d.box(x, 428, 100, motor, motor_sub)

d.text(14, 502, "昇降モーターはウォームギアで位置を保つので、電源が切れても落ちない", "lbl", "start")
d.text(14, 515, "カメラ部はモバイルバッテリーで動き、非常停止では止まらない", "lbl", "start")

d.write("power.svg")
