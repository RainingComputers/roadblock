from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone, timedelta
from colorama import Fore
from colorama import Style
from colorama.ansi import AnsiFore

LogLevel = Enum("LogLevel", ["INFO", "WARN", "ERROR"])


@dataclass
class Log:
    ts: str
    level: LogLevel
    message: str


logs: list[Log] = []

colors: dict[LogLevel, AnsiFore] = {
    LogLevel.INFO: Fore.GREEN,
    LogLevel.WARN: Fore.YELLOW,
    LogLevel.ERROR: Fore.RED,
}

tz = datetime.now(timezone(timedelta(0))).astimezone().tzinfo


def now() -> str:
    return datetime.now(tz=tz).isoformat(
        timespec="seconds",
    )


def print_log(log: Log) -> None:
    print(
        f"[{colors[log.level]}{log.level.name}@{log.ts}{Style.RESET_ALL}]:",
        log.message,
    )


def info(message: str) -> None:
    log = Log(now(), LogLevel.INFO, message)
    print_log(log)
    logs.append(log)


def warn(message: str) -> None:
    log = Log(now(), LogLevel.WARN, message)
    print_log(log)
    logs.append(log)


def error(message: str) -> None:
    log = Log(now(), LogLevel.ERROR, message)
    print_log(log)
    logs.append(log)
