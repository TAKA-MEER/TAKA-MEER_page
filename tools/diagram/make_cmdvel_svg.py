"""走行部の速度指令の流れ（site/assets/img/cmd-vel.svg）を書き出す。

中身を変えたら `python tools/diagram/make_cmdvel_svg.py` で書き出し直す。

根拠: th-system の docs/architecture.md「速度指令の排他制御（twist_mux → obstacle_limiter）」、
th_esp32_bridge/package.xml（/cmd_vel → 車輪指令）、site/move/tech.html の安全設計
"""

from svgkit import Diagram

W, H = 380, 482
COL_X = {1: 14, 2: 128, 3: 242}
LEFT, RIGHT, HALF_W = 14, 216, 150

d = Diagram(W, H, "走行部の速度指令の流れ")

d.group(8, 326, "PC 上の ROS 2 ノード", "th-system", x=4, w=372)

# 指令を出す側。数字が大きいほど優先
for col, title, sub, prio in (
    (1, "手動操作", "画面 → jog_gate", 30),
    (2, "教示再生", "replay_runner", 20),
    (3, "Nav2", "地図上の移動", 10),
):
    x = COL_X[col]
    d.box(x, 38, 100, title, sub)
    d.line([(x + 50, 78), (x + 50, 116)])
    d.text(x + 56, 101, f"優先 {prio}", "lbl", "start")

d.box(LEFT, 116, 352, "twist_mux", "いちばん優先度の高い指令だけを通す", ctrl=True)

d.box(LEFT, 194, HALF_W, "safety_monitor", "故障・非常停止を検知", ctrl=True)
d.line([(89, 194), (89, 156)])
d.text(95, 179, "全指令を止めるロック", "lbl acc", "start")

d.box(RIGHT, 194, HALF_W, "obstacle_limiter", "障害物の手前で減速・停止", ctrl=True)
d.line([(291, 156), (291, 194)])

d.box(RIGHT, 272, HALF_W, "th_esp32_bridge", "左右の車輪の速度に変換", ctrl=True)
d.line([(291, 234), (291, 272)])
d.text(285, 257, "/cmd_vel（20Hz）", "lbl", "end")

# 機体側
d.box(LEFT, 350, HALF_W, "RPLIDAR S1", "Raspberry Pi 4 経由で配信")
d.line([(60, 350), (60, 234)])
d.line([(164, 370), (190, 370), (190, 214), (216, 214)])

d.box(RIGHT, 350, HALF_W, "ESP32", "ウォッチドッグ 600ms", ctrl=True)
d.line([(291, 312), (291, 350)])
d.text(285, 342, "Raspberry Pi 4 経由", "lbl", "end")

d.box(RIGHT, 428, HALF_W, "クローラー", "左右モーター")
d.line([(291, 390), (291, 428)])

d.text(14, 444, "駆動へ速度を送れるのは", "lbl acc", "start")
d.text(14, 457, "obstacle_limiter だけ", "lbl acc", "start")

d.write("cmd-vel.svg")
