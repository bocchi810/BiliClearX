import os
import logging
import threading
import datetime
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from io import StringIO
from utils.config import ROOT, Config


console_log_level = Config.get('console_log_level')
file_log_level = Config.get('file_log_level')

log_level_map = {
    'DEBUG': DEBUG,
    'INFO': INFO,
    'WARNING': WARNING,
    'ERROR': ERROR,
    'CRITICAL': CRITICAL
}

console_log_level_int = log_level_map.get(console_log_level.upper(), DEBUG)
file_log_level_int = log_level_map.get(file_log_level.upper(), INFO)


class LOG:
    def __init__(self, log_file_prefix=ROOT / "logs"):
        os.makedirs(log_file_prefix, exist_ok=True)
        self.log_file_prefix = log_file_prefix
        self.logger = logging.getLogger("Custom Logger")
        self.logger.setLevel(logging.NOTSET)

        # 创建控制台输出的handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_log_level_int)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 初始化文件handler为None，以便在首次记录日志时创建
        self.file_handler = None
        self.current_log_date = None
        self.lock = threading.Lock()

        # 创建一个 StringIO 对象来捕获日志输出
        self.log_stream = StringIO()

    def _ensure_log_file_created(self):
        """确保日志文件在首次记录日志时创建，或在新的一天开始时创建新文件。"""
        today = datetime.datetime.now().date()
        if self.file_handler is None or today != self.current_log_date:
            with self.lock:
                if self.file_handler is not None and today != self.current_log_date:
                    self.logger.removeHandler(self.file_handler)
                    self.file_handler.close()

                self.current_log_date = today
                self.log_file = os.path.join(
                    self.log_file_prefix, f"{today}.log")
                self.file_handler = logging.FileHandler(
                    self.log_file, encoding='utf-8')
                self.file_handler.setLevel(file_log_level_int)
                self.file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
                self.logger.addHandler(self.file_handler)

    def debug(self, message: str) -> None:
        self._ensure_log_file_created()
        with self.lock:
            self.logger.debug(message)

    def info(self, message: str) -> None:
        self._ensure_log_file_created()
        with self.lock:
            self.logger.info(message)

    def warning(self, message: str) -> None:
        self._ensure_log_file_created()
        with self.lock:
            self.logger.warning(message)

    def error(self, message: str) -> None:
        self._ensure_log_file_created()
        with self.lock:
            self.logger.error(message)

    def critical(self, message: str) -> None:
        self._ensure_log_file_created()
        with self.lock:
            self.logger.critical(message)

    def _generate_log_output(self):
        """生成器函数，用于生成日志输出。"""
        while True:
            log_content = self.log_stream.getvalue()
            if log_content:
                self.log_stream.seek(0)
                self.log_stream.truncate(0)  # 清空日志缓冲区
                yield log_content
            else:
                yield ""

Logger = LOG()