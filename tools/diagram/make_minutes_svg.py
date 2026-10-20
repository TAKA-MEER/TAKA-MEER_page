"""議事録システムの構成図（site/assets/img/minutes.svg）を書き出す。

中身を変えたら `python tools/diagram/make_minutes_svg.py` で書き出し直す。

根拠: site/records/tech.html の「議事録システムの構成」「音声処理の流れ」「話者判定」、
site/records/index.html の「会話の内容を外に出さない」
"""

from svgkit import Diagram

W, H = 380, 490
LEFT, RIGHT, HALF_W = 14, 216, 150

d = Diagram(W, H, "議事録システムの構成図")

d.box(RIGHT, 14, HALF_W, "ワイヤレスイヤホン", "自社側の人が付ける")

d.group(74, 404, "試験場の PC", "Windows・Docker", x=4, w=372)

d.box(LEFT, 104, HALF_W, "ブラウザ 1", "内蔵マイクで録音")
d.box(RIGHT, 104, HALF_W, "ブラウザ 2", "イヤホンで録音（話者判定）")
d.line([(291, 54), (291, 104)])

d.box(LEFT, 190, 352, "minutes-app", "FastAPI・faster-whisper large-v3・議事録の組み立て", ctrl=True)
d.line([(89, 144), (89, 190)], start=True)
d.line([(291, 144), (291, 190)], start=True)
d.text(95, 170, "音声／文字起こし", "lbl", "start")
d.text(297, 170, "WebSocket", "lbl", "start")

d.box(LEFT, 276, 170, "minutes-ollama", "Ollama・qwen3.5:9b", ctrl=True)
d.line([(99, 230), (99, 276)], start=True)
d.text(105, 256, "議事録を生成", "lbl", "start")

d.box(RIGHT, 276, HALF_W, "議事録", "Word（docx）・PDF に変換可")
d.line([(291, 230), (291, 276)])

d.box(LEFT, 350, 170, "GPU", "VRAM 8GB・交互に使う")
d.line([(99, 316), (99, 350)], cls="mech")
d.line([(200, 230), (200, 370), (184, 370)], cls="mech")

d.line([(291, 404), (291, 436)], cls="mech")
d.text(291, 426, "×", "x")
d.box(RIGHT, 436, HALF_W, "インターネット", "会話の内容は送らない")
d.text(14, 452, "録音・文字起こし・要約は", "lbl acc", "start")
d.text(14, 465, "すべてこの PC の中で処理する", "lbl acc", "start")

d.write("minutes.svg")
