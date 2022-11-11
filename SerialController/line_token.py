from __future__ import annotations

from configparser import ConfigParser
from logging import Logger
from os import path

import cv2
import linenotify as ln


def notify(key: str, message: str, attachment: cv2.Mat | None = None, logger: Logger | None = None):
    """
    keyを指定して送信する。

    Args:
        key (str): トークンの辞書のkey
        message (str): 送信するテキスト
        attachment (cv2.Mat | None, optional): 添付する画像。Defaults to None.
        logger (Logger | None, optional): `Logger`オブジェクト。Defaults to None.
    """
    try:
        token = load_tokens(logger=logger)[key]

    except:
        print('token名が間違っています')
        if logger is not None:
            logger.error('Using the wrong token')
        return

    a = attachment is None
    try:
        service = ln.Service(token)
        service.notify(message, attachment)

    except:
        print(f"[LINE]テキスト{'' if a else 'と画像'}の送信に失敗しました。")
        if logger is not None:
            logger.error(f"Failed to send {'' if a else 'image with '}text")
        return

    print(f"[LINE]テキスト{'' if a else 'と画像'}を送信しました。")
    if logger is not None:
        logger.info(f"Send {'' if a else 'image with '}text")


def _get_encoding(filename):
    """
    utf-8 ファイルが BOM ありかどうかを判定する
    """
    with open(filename, encoding='utf-8') as f:
        return 'utf-8-sig' if f.readline()[0] == '\ufeff' else 'utf-8'


def load_tokens(filename: str = path.join(path.dirname(__file__), "line_token.ini"), logger: Logger | None = None):
    """
    トークンを記載したファイルを読み込む。

    ファイルはconfigparserで解析できる`*.ini`形式であり、`[LINE]`を含むと仮定する。

    正常に解析できない場合、空の辞書を返す。

    Args:
        filename (str, optional): ファイル名。Defaults to path.join(path.dirname(__file__), "line_token.ini").
        logger (Logger | None, optional): `Logger`オブジェクト。Defaults to None.

    Returns:
        dict[str, str]: トークンの辞書
    """
    try:
        encoding = _get_encoding(filename)
        if logger is not None:
            logger.debug(f"Open token file \"{filename}\" as \"{encoding}\"")

        parser = ConfigParser(comment_prefixes='#', allow_no_value=True)
        parser.read(filename, encoding)
        return dict(parser['LINE'])

    except Exception as e:
        if logger is not None:
            logger.error(f"Failed to open token file: {str(e)}")
        return {}

    except:
        if logger is not None:
            logger.error(
                f"Failed to open token file: unknown error has occurred")
        return {}


def check_tokens(tokens: dict[str, str], logger: Logger | None = None):
    """
    トークンの利用可否を検証する。

    Args:
        tokens (dict[str, str]): `get_tokens`から取得したトークンの辞書
        logger (Logger | None, optional): `Logger`オブジェクト。Defaults to None.

    Returns:
        str: トークンの利用可否を列挙する、人間可読の文字列。

        すべてのトークンが利用可能な場合"LINE Token Check ALL-OK!"、1つでも利用不可のものがあるか、1つもトークンがない場合"LINE Token Check FAILED."から始まる。
    """
    all_ok = True if len(tokens) != 0 else False
    ret = "----------\n" + ("" if len(tokens) != 0 else "No token found.\n")

    for key, token in tokens.items():
        try:
            service = ln.Service(token)
            _ = service.status

        except ln.LINENotifyException:
            all_ok = False
            ret += f"{key}: [Invalid]\n"
            if logger is not None:
                logger.warning(f"{key}: Invalid token")
            continue

        ret += f"{key}: [Valid]\n"
        if logger is not None:
            logger.info(f"{key}: Valid token")

    return ("LINE Token Check ALL-OK!\n" if all_ok else "LINE Token Check FAILED.\n") + ret + "----------"


def get_rate_limit(tokens: dict[str, str], logger: Logger | None = None):
    """
    トークンの利用状況を、標準出力とLoggerに出力する。

    Args:
        tokens (dict[str, str]): `get_tokens`から取得したトークンの辞書
        logger (Logger | None, optional): `Logger`オブジェクト。Defaults to None.
    """
    statuses: dict[str, ln.Status | Exception] = {}
    for key, token in tokens.items():
        try:
            service = ln.Service(token)
            statuses[key] = service.status

        except ln.LINENotifyException as e:
            statuses[key] = e

    for key, status in statuses.items():

        print(f"For \"{key}\"")

        if isinstance(status, Exception):
            print(f"  {str(status)}")
            if logger is not None:
                logger.warning(f"{key}: {str(status)}")
        else:
            print(f"  X-RateLimit-Limit: {status.limit}")
            print(f"  X-RateLimit-ImageLimit: {status.image_limit}")
            print(f"  X-RateLimit-Remaining: {status.remaining}")
            print(f"  X-RateLimit-ImageRemaining: {status.image_remaining}")
            print(f"  X-RateLimit-Reset: {status.reset}")

            if logger is not None:
                logger.info(f"{key}: LINE API - Limit: {status.limit}")
                logger.info(
                    f"{key}: LINE API - Remaining: {status.image_limit}")
                logger.info(
                    f"{key}: LINE API - ImageLimit: {status.remaining}")
                logger.info(
                    f"{key}: LINE API - ImageRemaining: {status.image_remaining}")
                logger.info(f"{key}: LINE API - Reset: {status.reset}")
        print()


if __name__ == "__main__":

    tokens = load_tokens()
    print(check_tokens(tokens) + "\n")
    get_rate_limit(tokens)
