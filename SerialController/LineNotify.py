from __future__ import annotations

from configparser import ConfigParser
from logging import DEBUG, Logger, NullHandler, getLogger
from os import path

import cv2
import linenotify as ln


def _get_encoding(filename):
    """
    utf-8 ファイルが BOM ありかどうかを判定する
    """
    with open(filename, encoding='utf-8') as f:
        return 'utf-8-sig' if f.readline()[0] == '\ufeff' else 'utf-8'


def _load_tokens(filename: str, logger: Logger):
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
        logger.debug(f"Open token file \"{filename}\" as \"{encoding}\"")

        parser = ConfigParser(comment_prefixes='#', allow_no_value=True)
        parser.read(filename, encoding)
        return dict(parser['LINE'])

    except Exception as e:
        logger.error(f"Failed to open token file: {str(e)}")
        return {}

    except:
        logger.error(f"Failed to open token file: unknown error has occurred")
        return {}


class LineNotify:
    def __init__(self, filename: str = path.join(path.dirname(__file__), "line_token.ini")) -> None:

        self.__logger = getLogger(__name__)
        self.__logger.addHandler(NullHandler())
        self.__logger.setLevel(DEBUG)
        self.__logger.propagate = True

        self.__tokens = _load_tokens(filename, self.__logger)

    def notify(self, key: str, message: str, attachment: cv2.Mat | None = None):
        """
        トークンをキーで指定して送信する。

        Args:
            key (str): `line_token.ini`に登録されたトークンのキー
            message (str): 送信するメッセージ
            attachment (cv2.Mat | None, optional): 画像。Defaults to None.
        """
        target = {
            "stdout": f"テキスト{'' if attachment is None else 'と画像'}",
            "log": f"{'' if attachment is None else 'image with '}text"
        }
        try:
            ln.Service(self.__tokens[key]).notify(message, attachment)

        except KeyError:
            print('token名が間違っています')
            self.__logger.error('Using the wrong token')
            return

        except:
            print(f"[LINE]{target['stdout']}の送信に失敗しました。")
            self.__logger.error(f"Failed to send {target['log']}")
            return

        print(f"[LINE]{target['stdout']}を送信しました。")
        self.__logger.info(f"Send {target['log']}")

    def check_tokens(self):
        """
        トークンの利用可否を検証する。

        Returns:
            str: トークンの利用可否を列挙する、人間可読の文字列。

            すべてのトークンが利用可能な場合"LINE Token Check ALL-OK!"、1つでも利用不可のものがあるか、1つもトークンがない場合"LINE Token Check FAILED."から始まる。
        """
        all_ok = True if len(self.__tokens) != 0 else False
        ret = "----------\n" + ("" if len(self.__tokens)
                                != 0 else "No token found.\n")

        for key, token in self.__tokens.items():
            try:
                service = ln.Service(token)
                _ = service.status

            except ln.LINENotifyException:
                all_ok = False
                ret += f"{key}: [Invalid]\n"
                self.__logger.warning(f"{key}: Invalid token")
                continue

            ret += f"{key}: [Valid]\n"
            self.__logger.info(f"{key}: Valid token")

        return ("LINE Token Check ALL-OK!\n" if all_ok else "LINE Token Check FAILED.\n") + ret + "----------"

    def get_rate_limit(self):
        """
        トークンの利用状況を、標準出力とLoggerに出力する。
        """
        statuses: dict[str, ln.Status | Exception] = {}
        for key, token in self.__tokens.items():
            try:
                service = ln.Service(token)
                statuses[key] = service.status

            except ln.LINENotifyException as e:
                statuses[key] = e

        for key, status in statuses.items():

            print(f"For \"{key}\"")

            if isinstance(status, Exception):
                print(f"  {str(status)}")
                self.__logger.warning(f"{key}: {str(status)}")
            else:
                print(f"  X-RateLimit-Limit: {status.limit}")
                print(f"  X-RateLimit-ImageLimit: {status.image_limit}")
                print(f"  X-RateLimit-Remaining: {status.remaining}")
                print(
                    f"  X-RateLimit-ImageRemaining: {status.image_remaining}")
                print(f"  X-RateLimit-Reset: {status.reset}")

                self.__logger.info(f"{key}: LINE API - Limit: {status.limit}")
                self.__logger.info(
                    f"{key}: LINE API - Remaining: {status.image_limit}")
                self.__logger.info(
                    f"{key}: LINE API - ImageLimit: {status.remaining}")
                self.__logger.info(
                    f"{key}: LINE API - ImageRemaining: {status.image_remaining}")
                self.__logger.info(f"{key}: LINE API - Reset: {status.reset}")
            print()


if __name__ == "__main__":

    line = LineNotify()
    print(line.check_tokens() + "\n")
    line.get_rate_limit()
