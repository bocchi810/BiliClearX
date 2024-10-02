import requests
import time
import re
from utils.database import SQlite
from utils.config import CFG
from utils.logger import LOG
import customtkinter as ctk  # 使用 customtkinter

# 设置 customtkinter 的外观模式和默认颜色主题
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# 初始化数据库、配置和日志模块
db = SQlite()
Config = CFG()
Logger = LOG()

# 获取请求头
headers = Config.get("headers")

# 初始化变量
waitRiskControl_TimeRemaining = float("nan")
waitingRiskControl = False
status_text = "Banner"
offset = 0
content_text = """
BiliClearX - github.com/molanp/BiliClearX
"""

def getCsrf(cookie: str | None):
    if cookie is None:
        Logger.critical("cookie 为空，请先运行一次主程序并扫码登陆")
        raise ValueError("cookie 为空，请先运行一次主程序并扫码登陆")
    try:
        return re.findall(r"bili_jct=(.*?);", cookie)[0]
    except IndexError:
        Logger.warning("无法获取 csrf")
        return ""

def avid2bvid(avid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?aid={avid}", headers=headers
    ).json()
    return result["data"]["bvid"]

def reqBiliReportReply(data: dict, rule: str | None):
    """调用B站举报评论API"""
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
        return "b站举报评论 API 调用失败, 返回体：{}".format(result)
    elif result_code == 12019:
        Logger.warning("举报过于频繁, 等待15s")
        return "举报过于频繁, 等待15s"
    elif result_code == -352:
        Logger.critical(
            "举报评论的B站 API 调用失败, 返回 -352, 请尝试手动举报1次, {}".format(
                avid2bvid(data["oid"])
            )
        )
        return "举报评论的B站 API 调用失败, 返回 -352, 请尝试手动举报1次, {}".format(
            avid2bvid(data["oid"])
        )
    else:
        db.update('report', {'is_reported': 1}, f"rpid = {data['rpid']} AND oid = {data['oid']}")
        return "举报成功"

def disable(button):
    button.configure(state=ctk.DISABLED)

def enable(button):
    button.configure(state=ctk.NORMAL)

def on_comply(button):
    update_content("合规")

def on_skip(button):
    update_content("跳过")

def on_report(button):
    update_content("举报")

def update_status(new_status):
    global status_label
    status_label.configure(text=new_status)

def update_content(new_content):
    global content_label
    content_label.configure(state=ctk.NORMAL)  # 设置为可编辑状态
    content_label.delete("0.0", ctk.END)  # 清空原有内容
    content_label.insert("0.0", new_content)  # 插入新内容
    content_label.configure(state=ctk.DISABLED)  # 设置回只读状态


def create_button(master, text, command):
    button = ctk.CTkButton(master, text=text, command=lambda: command(button))
    button.pack(pady=5, padx=10, fill=ctk.X)
    return button

def main():
    root = ctk.CTk()  # 使用CTk代替Tk
    root.title("BiliClearX 评论审核工具")
    root.geometry("500x400")

    # 创建状态栏
    global status_label
    status_label = ctk.CTkLabel(root, text=status_text, font=("Arial", 12))
    status_label.pack(fill=ctk.X)

    # 创建内容区域
    global content_label
    content_label = ctk.CTkTextbox(root, font=("Arial", 12), wrap="word")  # 使用CTkTextbox
    content_label.insert("0.0", content_text)
    content_label.configure(state=ctk.DISABLED)  # 设置为只读状态
    content_label.pack(pady=10, padx=10, fill=ctk.BOTH, expand=True)

    # 创建按钮
    global comply_button, skip_button, report_button
    comply_button = create_button(root, "合规(c)", on_comply)
    skip_button = create_button(root, "跳过(s)", on_skip)
    report_button = create_button(root, "举报(r)", on_report)

    # 主循环
    root.mainloop()

if __name__ == "__main__":
    main()