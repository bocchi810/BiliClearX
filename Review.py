import tkinter
import requests
import time
import _ssl
import re
import sys
import asyncio
from utils.config import Config
from utils.database import Database
from utils.logger import Logger
import customtkinter as ctk
import tkinter.messagebox

# 设置 customtkinter 的外观模式和默认颜色主题
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# 获取请求头
headers = Config.get("headers")

# 初始化变量
waitRiskControl_TimeRemaining = float("nan")
waitingRiskControl = False
offset = 0


def get_data():
    return Database.select_where("report", "need_report = 1 AND is_reported = 0")


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


async def reqBiliReportReply(data: dict, rule: str | None):
    """调用B站举报评论API"""
    result = requests.post(
        "https://api.bilibili.com/x/v2/reply/report",
        headers=headers,
        data={
            "type": 1,
            "oid": data["oid"],
            "rpid": data["rpid"],
            "reason": 0,
            "csrf": Csrf,
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
        Database.update(
            "report",
            {"is_reported": 1},
            f"rpid = {data['rpid']} AND oid = {data['oid']}",
        )
        return True


def disable(button):
    button.configure(state=ctk.DISABLED)


def enable(button):
    button.configure(state=ctk.NORMAL)


def on_comply(button):
    global index
    Database.update("report", {"need_report": 0}, f"id = {data[index]['id']}")
    index += 1
    update_status(index)
    update_content(index)


def on_skip(button):
    global index
    index += 1
    update_status(index)
    update_content(index)


def on_report(button):
    global index
    disable(report_button)
    msg = asyncio.run(reqBiliReportReply(data[index], data[index]["rule"]))
    if msg is not True:
        tkinter.messagebox.showwarning("警告", msg)
        return
    tkinter.messagebox.showinfo("提示", "举报成功")
    Database.update("report", {"is_reported": 1}, f"id = {data[index]['id']}")
    enable(report_button)
    index += 1
    update_status(index)
    update_content(index)


def on_reflash(button):
    global data, all_report
    data = get_data()
    all_report = len(data)
    update_status(index)
    update_content(index)


def update_status(index):
    global status_label
    status = "ID: {}    已审:{}     未审:{}     违规率:{}%".format(
        data[index]["id"],
        is_reported,
        all_report - is_reported,
        is_reported / all_report * 100,
    )
    status_label.configure(text=status)


def update_content(index):
    global content_label
    content = "匹配规则:{}\n内容:\n\n{}".format(
        data[index]["rule"], data[index]["content"]
    )
    content_label.configure(state=ctk.NORMAL)  # 设置为可编辑状态
    content_label.delete("0.0", ctk.END)  # 清空原有内容
    content_label.insert("0.0", content)  # 插入新内容
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
    status_label = ctk.CTkLabel(root, font=("Arial", 12))
    status_label.pack(fill=ctk.X)
    update_status(index)

    # 创建内容区域
    global content_label
    content_label = ctk.CTkTextbox(
        root, font=("Arial", 12), wrap="word"
    )  # 使用CTkTextbox
    update_content(index)
    content_label.pack(pady=10, padx=10, fill=ctk.BOTH, expand=True)

    # 创建按钮
    global comply_button, skip_button, report_button, reflash_button
    comply_button = create_button(root, "合规", on_comply)
    skip_button = create_button(root, "跳过", on_skip)
    reflash_button = create_button(root, "重载数据", on_reflash)
    report_button = create_button(root, "举报", on_report)

    # 主循环
    root.mainloop()


if __name__ == "__main__":
    data = get_data()
    index = 0
    is_reported = 0
    all_report = len(data)
    if all_report == 0:
        tkinter.messagebox.showinfo("提示", "暂无违规评论")
        sys.exit(0)
    try:
        Csrf = getCsrf(Config.get("cookie"))
    except ValueError as e:
        tkinter.messagebox.showerror("错误", str(e))
    else:
        main()
