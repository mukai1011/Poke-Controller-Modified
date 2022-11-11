from __future__ import annotations

from configparser import ConfigParser
from logging import DEBUG, Logger, NullHandler, getLogger
from os import path

import linenotify as ln


def _get_encoding(filename):
    """
    utf-8 ファイルが BOM ありかどうかを判定する
    """
    with open(filename, encoding='utf-8') as f:
        return 'utf-8-sig' if f.readline()[0] == '\ufeff' else 'utf-8'


def get_tokens(filename: str = path.join(path.dirname(__file__), "line_token.ini"), logger: Logger | None = None):
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
            print(f"\t{str(status)}")
            if logger is not None:
                logger.warning(f"{key}: {str(status)}")
        else:
            print(f"\tX-RateLimit-Limit: {status.limit}")
            print(f"\tX-RateLimit-ImageLimit: {status.image_limit}")
            print(f"\tX-RateLimit-Remaining: {status.remaining}")
            print(f"\tX-RateLimit-ImageRemaining: {status.image_remaining}")
            print(f"\tX-RateLimit-Reset: {status.reset}")

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

    logger = getLogger(__name__)
    logger.addHandler(NullHandler())
    logger.setLevel(DEBUG)
    logger.propagate = True

    tokens = get_tokens(logger=logger)
    
    print(check_tokens(tokens, logger) + "\n")
    get_rate_limit(tokens, logger)
