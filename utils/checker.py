import re
import yaml
import unicodedata

from utils.logger import Logger
from utils.config import Root
from Levenshtein import ratio


class Checker:
    def __init__(self) -> None:
        try:
            with open(
                Root
                / "res"
                / "rules.yaml",
                "r",
                encoding="utf-8",
            ) as f:
                config = yaml.safe_load(f)
        except Exception as e:
            Logger.warning("无法加载规则文件,{}".format(e))
            config = {}

        self.rules_exact: list[str | list[str]] = config.get("rules_exact", [])
        self.rules_elastic = config.get("rules_elastic", [])

    def normalize_text(self, text: str) -> str:
        "将文本转换为小写、简体中文和英文符号"
        text = text.lower()
        text = unicodedata.normalize("NFKC", text)
        text = (
            text.replace("！", "!")
            .replace("。", ".")
            .replace("，", ",")
            .replace("“", '"')
            .replace("”", '"')
        )
        return text

    def check_v1(self, text: str):
        "检查字符串"
        text = self.normalize_text(text)

        for item in self.rules_exact:
            if isinstance(item, list):
                if all(
                    [
                        (keyword.replace("$-not ", "") not in text)
                        if keyword.startswith("$-not ")
                        else (keyword in text)
                        for keyword in item
                    ]
                ):
                    return True, str(item)
            elif isinstance(item, str):
                if re.search(item.lower(), text):
                    return True, item

        return False, "用户自定义规则命中"

    def check_v2(self, text: str, threshold: float = 0.7):
        "检查字符串, 并根据匹配程度进行判断 threshold: 匹配程度阈值"
        text = self.normalize_text(text)
        match_scores = []

        for item in self.rules_exact:
            if isinstance(item, list):
                if all(
                    [
                        (keyword.replace("$-not ", "") not in text)
                        if keyword.startswith("$-not ")
                        else (keyword in text)
                        for keyword in item
                    ]
                ):
                    match_scores.append(1.0)
            elif isinstance(item, str):
                matches = re.findall(item.lower(), text)
                score = len(matches) / len(text)
                match_scores.append(score)

        if match_scores:
            avg_score = sum(match_scores) / len(match_scores)
            return avg_score >= threshold, "规则匹配程度匹配"

        return False, ""

    def check_v3(self, text: str, threshold: float = 0.7):
        "检查字符串, 并根据相似程度进行判断 threshold: 相似程度阈值"
        text = self.normalize_text(text)
        match_scores = []

        for item in self.rules_elastic:
            if isinstance(item, str):
                similarity = ratio(item.lower(), text)
                match_scores.append(similarity)

        if match_scores:
            avg_score = sum(match_scores) / len(match_scores)
            return avg_score >= threshold, "规则相似程度匹配"

        return False, ""

    def check_v4(self, text: str, threshold: float = 0.7):
        "检查字符串, 计算跳词进行判断 threshold: 相似程度阈值"
        text = self.normalize_text(text)
        match_scores = []
        for item in self.rules_exact:
            sentence = []
            for keyword in item:
                pattern = r""
                if keyword != "" and len(keyword) >= 2:
                    for char in keyword:
                        if char != "":
                            pattern = pattern + char + r".*"
                if pattern != "" and len(pattern) > 2:
                    pattern = pattern[:-2]
                    sentence.append(pattern)
            if len(sentence) != 0 and all(
                "$" not in x and ".." not in x for x in sentence
            ):
                match_scores.append(sentence)
        value = 0.0
        for patterns in match_scores:
            allowadd = True
            count = 0
            start_char = ""
            end_char = ""
            for pattern in patterns:
                match = re.search(pattern, text)
                if match is None or match.group() == "":
                    allowadd = False
                    break
                value = value + len(pattern.replace(r".*", "")) / (
                    len(match.group()) * 1.25
                )
                if count < 1:
                    start_char = match.group()
                count = count + 1
                end_char = match.group()

            if allowadd:
                start_index = text.index(start_char) + len(start_char)
                end_index = text.rindex(end_char)
                vvalue = len(text[start_index:end_index]) / (
                    len(text) - (len(start_char) + len(end_char)) / 2
                )
                value = (vvalue * 1.25 + value) / 2
                break
            else:
                value = 0.0
                continue
        return (False, "") if (value < threshold) else (True, "跳词规则程度匹配")

    def check(self, text: str, threshold: float = 0.7):
        "使用使用方法检查字符串"
        checks: list[tuple[bool, str]] = [
            self.check_v1(text),
            self.check_v2(text, threshold),
            self.check_v3(text, threshold),
            self.check_v4(text, threshold),
        ]
        for isp, r in checks:
            if isp:
                return True, r
        return False, ""
