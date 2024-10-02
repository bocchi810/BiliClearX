import ujson as json
import re
import time
import asyncio
import requests
import biliauth
from requests.packages import urllib3  # type: ignore
from utils import checker
from compatible_getpass import getpass
from os import environ
from utils.config import Config
from utils.database import db
from utils.logger import Logger


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
loaded = False
headers = {}


def checkRuleUpdate():
    pass


#    try:
#        new_rules = requests.get(open(
#            "./RULE_SOURCE", "r", encoding="utf-8").read(), verify=False).content.decode("utf-8")
#        with open("./res/rules.yaml", "w", encoding="utf-8") as f:
#            f.write(new_rules)
#    except Exception as e:
#        with open("update_rule_err.txt", "w", encoding="utf-8") as f:
#            f.write(f"{datetime.now()}\n{e}")


# Thread(target=checkRuleUpdate, daemon=True).start()


def putConfigVariables():
    global bili_report_api, csrf, headers
    global reply_limit
    global enable_check_user

    headers = Config.get("headers")
    bili_report_api = Config.get("bili_report_api", True)
    csrf = getCsrf(headers.get("Cookie"))
    reply_limit = Config.get("reply_limit", 100)
    enable_check_user = Config.get("enable_check_user", False)
    if reply_limit <= 20:
        reply_limit = 100


def getCsrf(cookie: str | None):
    if cookie is None:
        return ""
    try:
        return re.findall(r"bili_jct=(.*?);", cookie)[0]
    except IndexError:
        Logger.warning("无法获取 csrf")
        return ""


def getCookieFromUser():
    if not environ.get("gui", False):
        if "n" in input("是否使用二维码登录B站(Y/n): ").lower():
            return getpass("Please input Bilibili cookie: ")
        else:
            return biliauth.biliLogin()
    else:
        return biliauth.biliLogin()


def checkCookie():
    result = requests.get(
        "https://passport.bilibili.com/x/passport-login/web/cookie/info",
        headers=headers,
        data={"csrf": csrf},
    ).json()
    return result["code"] == 0 and not result.get("data", {}).get("refresh", True)


def getVideos():
    "获取推荐视频列表"
    return [
        i["param"]
        for i in requests.get(
            "https://app.bilibili.com/x/v2/feed/index", headers=headers
        ).json()["data"]["items"]
        if i.get("can_play", 0)
    ]


def getReplys(avid: str | int):
    "获取评论"
    maxNum = reply_limit
    page = 1
    replies = []
    while page * 20 <= maxNum:
        time.sleep(0.4)
        result = requests.get(
            f"https://api.bilibili.com/x/v2/reply?type=1&oid={avid}&nohot=1&pn={page}&ps=20",
            headers=headers,
        ).json()
        try:
            if not result["data"]["replies"]:
                break
            replies += result["data"]["replies"]
        except Exception:
            break
        page += 1
    return replies


def _checkUser(uid: int | str):
    "检查用户是否需要举报 (用于检测)"
    user_crad = requests.get(
        f"https://api.bilibili.com/x/web-interface/card?mid={uid}", headers=headers
    ).json()["data"]["card"]

    if user_crad["spacesta"] == -2:
        return False  # 封了, 没必要

    # if user_crad["level_info"]["current_level"] != 2:
    #    return False  # 不是 lv.2, 没必要

    dynamics = [
        i["modules"]["module_dynamic"]
        for i in requests.get(
            f"https://api.bilibili.com/x/polymer/web-dynamic/v1/feed/all?host_mid={uid}",
            headers=headers,
        ).json()["data"]["items"]
    ]

    for dynamic in dynamics:
        if dynamic["desc"] is None:
            continue

        text = dynamic["desc"]["text"]
        if isPorn(text):
            return True

        if dynamic["major"] is None:
            continue
        elif dynamic["major"]["type"] != "MAJOR_TYPE_DRAW":
            continue

    return False


async def reqBiliReportUser(uid: int | str):
    "调用B站举报用户API"
    result = requests.post(
        "https://space.bilibili.com/ajax/report/add",
        headers=headers,
        data={"mid": int(uid), "reason": "1, 2, 3", "reason_v2": 1, "csrf": csrf},
    ).json()
    time.sleep(3.5)
    result_code = result["code"]
    if result_code not in (0, 12019):
        Logger.error("b站举报用户uid: {} 失败, 返回体：{}".format(uid, result))
    elif result_code == 12019:
        Logger.warning("举报过于频繁, 等待 15s")
        time.sleep(15)
        return reqBiliReportUser(uid)


async def processUser(uid: int | str):
    "处理用户"
    if _checkUser(uid):
        Logger.info(f"用户{uid}违规")
        await reqBiliReportUser(uid)


async def isPorn(text: str):
    "判断评论是否为色情内容 (使用规则, rules.yaml)"
    return text_checker.check(text)


async def replyIsViolations(reply: dict):
    "判断评论是否违规, 返回: (是否违规, 违规原因) 如果没有违规, 返回 (False, None)"
    global enable_gpt

    reply_msg = reply["content"]["message"]
    isp, r = await isPorn(reply_msg)

    if "doge" in reply_msg:
        return False, None

    return isp, r


async def processReply(reply: dict):
    "处理评论并举报"
    global replyCount, violationsReplyCount

    replyCount += 1
    isp, r = await replyIsViolations(reply)

    if isp:
        violationsReplyCount += 1
        db.insert(
            "report",
            {
                "rpid": reply["rpid"],
                "oid": reply["oid"],
                "mid": reply["mid"],
                "need_report": 1,
                "content": reply["content"]["message"],
                "rule": r,
            },
        )

    checkedReplies.insert(0, (reply["rpid"], reply["content"]["message"], time.time()))
    db.insert(
        "report",
        {
            "rpid": reply["rpid"],
            "oid": reply["oid"],
            "mid": reply["mid"],
            "need_report": 0,
            "content": reply["content"]["message"],
            "rule": r,
        },
    )
    return isp, r


def _setMethod():
    global method
    method = None
    method_choices = {
        "1": "自动获取推荐视频评论",
        "2": "获取指定视频评论",
        "3": "检查指定UID",
    }

    Logger.info("请选择操作: ")
    while method not in method_choices.keys():
        if method is not None:
            Logger.warning("输入错误")

        for k, v in method_choices.items():
            Logger.info(f"{k}. {v}")
        method = input("选择: ")


def bvid2avid(bvid: str):
    result = requests.get(
        f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}", headers=headers
    ).json()
    return result["data"]["aid"]


videoCount = 0
replyCount = 0
violationsReplyCount = 0
waitRiskControl_TimeRemaining = float("nan")
waitingRiskControl = False
checkedVideos = []
checkedReplies = []
violationsReplies = []


async def _checkVideo(avid: str | int):
    for reply in getReplys(avid):
        if enable_check_user:
            await processUser(reply["mid"])
        await processReply(reply)


async def checkNewVideos():
    global videoCount, replyCount, violationsReplyCount, checkedVideos

    Logger.info(
        "".join([("\n" if videoCount != 0 else ""), "开始检查新一轮推荐视频..."])
    )
    Logger.info(f"已检查视频: {videoCount}")
    Logger.info(f"已检查评论: {replyCount}")
    Logger.info(
        f"已举报评论: {violationsReplyCount} 评论违规率: {((violationsReplyCount / replyCount * 100) if replyCount != 0 else 0.0):.5f}%"
    )
    Logger.info("---------")

    for avid in getVideos():
        Logger.info("开始检查视频: av{}".format(avid))
        await _checkVideo(avid)
        videoCount += 1
        checkedVideos.insert(0, (avid, time.time()))
        checkedVideos = checkedVideos[:1500]
    time.sleep(1.25)


async def checkVideo(bvid: str):
    global videoCount, checkedVideos

    avid = bvid2avid(bvid)
    await _checkVideo(avid)
    videoCount += 1
    checkedVideos.insert(0, (avid, time.time()))
    checkedVideos = checkedVideos[:1500]
    time.sleep(1.25)


async def waitRiskControl(output: bool = True):
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
        if output:
            Logger.warning(
                f"由于可能被风控, BiliClear 暂停{stopMinute}分钟, 还剩余: {waitRiskControl_TimeRemaining:.2f}s"
            )
            time.sleep(1.5)
        else:
            time.sleep(0.005)
    waitingRiskControl = False


if __name__ == "__main__":
    Logger.info("BiliClearX - github.com/molanp/BiliClearX")

    putConfigVariables()
    if not checkCookie():
        Logger.warning("Bilibili cookie 已失效, 请重新登录")
        headers["Cookie"] = getCookieFromUser()
        Config.save()
        csrf = getCsrf(headers["Cookie"])

    text_checker = checker.Checker()
    _setMethod()
    while True:
        try:
            match method:
                case "1":
                    asyncio.run(checkNewVideos())
                case "2":
                    asyncio.run(checkVideo(input("输入视频 bvid: ")))
                case "3":
                    asyncio.run(processUser(input("输入用户 UID: ")))
                case _:
                    assert False, "Unknow method."
        except Exception as e:
            Logger.error(repr(e))
            if isinstance(e, json.JSONDecodeError):
                asyncio.run(waitRiskControl())
