import urwid
import requests
import time
from utils.database import db
from utils.config import Config
from utils.logger import Logger
from biliclear import getCsrf

headers = Config.get("headers")
waitRiskControl_TimeRemaining = float("nan")
waitingRiskControl = False
status_text = "按 q 退出"
offset = 0
content_text = r"""
  ____    _   _   _    ____   _                        __  __
 | __ )  (_) | | (_)  / ___| | |   ___    __ _   _ __  \ \/ /
 |  _ \  | | | | | | | |     | |  / _ \  / _` | | '__|  \  / 
 | |_) | | | | | | | | |___  | | |  __/ | (_| | | |     /  \ 
 |____/  |_| |_| |_|  \____| |_|  \___|  \__,_| |_|    /_/\_\
"""
status_bar = urwid.Text(status_text, align="center")
content_area = urwid.Text(content_text, align="center")


def avid2bvid(avid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?aid={avid}", headers=headers
    ).json()
    return result["data"]["bvid"]


def reqBiliReportReply(data: dict, rule: str | None):
    "调用B站举报评论API"
    result = requests.post(
        "https://api.bilibili.com/x/v2/reply/report",
        headers=headers,
        data={
            "type": 1,
            "oid": data["oid"],
            "rpid": data["rpid"],
            "reason": 0,
            "csrf": getCsrf(Config.get("cookie")),
            "content": f"""
程序匹配到的规则: {rule}
(此举报信息自动生成, 可能会存在误报)
""",
        },
    ).json()
    time.sleep(3.5)
    result_code = result["code"]
    if result_code not in (0, 12019, -352):
        Logger.error("b站举报评论 API 调用失败, 返回体：{}".format(result))
        yield "b站举报评论 API 调用失败, 返回体：{}".format(result)
    elif result_code == 12019:
        Logger.warning("举报过于频繁, 等待15s")
        yield "举报过于频繁, 等待15s"
        time.sleep(15)
        return reqBiliReportReply(data, rule)
    elif result_code == -352:
        Logger.critical(
            "举报评论的B站 API 调用失败, 返回 -352, 请尝试手动举报1次, {}".format(
                avid2bvid(data["oid"])
            )
        )
        yield "举报评论的B站 API 调用失败, 返回 -352, 请尝试手动举报1次, {}".format(
            avid2bvid(data["oid"])
        )
        global waitRiskControl_TimeRemaining, waitingRiskControl
        stopSt = time.time()
        stopMinute = 3
        waitRiskControl_TimeRemaining = 60 * stopMinute
        waitingRiskControl = True
        Logger.warning(
            f"Bili API 返回了非 JSON 格式数据, 可能被风控, 暂停{stopMinute}分钟..."
        )
        while time.time() - stopSt < 60 * stopMinute:
            waitRiskControl_TimeRemaining = 60 * stopMinute - (time.time() - stopSt)
            Logger.warning(
                f"由于可能被风控, BiliClear 暂停{stopMinute}分钟, 还剩余: {waitRiskControl_TimeRemaining:.2f}s"
            )
            yield f"由于可能被风控, BiliClear 暂停{stopMinute}分钟, 还剩余: {waitRiskControl_TimeRemaining:.2f}s"
            time.sleep(1.5)
        waitingRiskControl = False
        return reqBiliReportReply(data, rule)
    else:
        db.update('report', {'is_reported': 1}, f"rpid = {data['rpid']} AND oid = {data['oid']}")


def disable(button):
    button._w = urwid.AttrMap(urwid.Text(button.label), "disabled_button")


def enable(button):
    button._w = urwid.AttrMap(urwid.Text(button.label), "normal_button")


def on_comply(button):
    update_content("合规")


def on_skip(button):
    update_content("跳过")


def on_report(button):
    update_content("举报")


def update_status(new_status):
    global status_bar
    status_bar.set_text(f"[退出(q)] | {new_status}")


def update_content(new_content):
    global content_area
    content_area.set_text(new_content)


comply_button = urwid.Button("合规(c)", on_comply)
skip_button = urwid.Button("跳过(s)", on_skip)
report_button = urwid.Button("举报(r)", on_report)

palette = [
    ("header", "white", "dark blue"),
    ("footer", "white", "dark red"),
    ("comply_button", "white", "", "", "", "#55a7ff"),
    ("skip_button", "white", "", "", "", "g38"),
    ("report_button", "white", "", "", "black", "#a2e0ff"),
]


comply_button = urwid.AttrMap(comply_button, "comply_button")
skip_button = urwid.AttrMap(skip_button, "skip_button")
report_button = urwid.AttrMap(report_button, "report_button")

comply_button = urwid.Padding(comply_button, width=("relative", 100), align="center")
skip_button = urwid.Padding(skip_button, width=("relative", 100), align="center")
report_button = urwid.Padding(report_button, width=("relative", 100), align="center")

button_list = [comply_button, skip_button, report_button]

button_column = urwid.Columns(button_list, dividechars=1)

layout = urwid.Frame(
    body=urwid.Filler(content_area, "middle"),
    header=urwid.AttrMap(status_bar, "header"),
    footer=urwid.AttrMap(button_column, "footer"),
)


def handle_input(key):
    if isinstance(key, tuple):
        key = key[0]
    key = key.lower()
    if key == "q":
        raise urwid.ExitMainLoop()
    elif key == "c":
        on_comply(comply_button)
    elif key == "s":
        on_skip(skip_button)
    elif key == "r":
        on_report(report_button)


screen = urwid.display.raw.Screen()
screen.set_terminal_properties(colors=256)
loop = urwid.MainLoop(layout, palette, unhandled_input=handle_input, screen=screen)
loop.run()
