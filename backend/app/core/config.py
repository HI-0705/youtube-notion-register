import os
import re

# 環境変数からYOUTUBE_API_KEYの値を取得します
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# APIキーが設定されていなかった場合のガード処理
if not YOUTUBE_API_KEY:
    print("警告: 環境変数 'YOUTUBE_API_KEY' が設定されていません。")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def parse_duration(duration: str) -> int:
    """
    ISO 8601形式の期間文字列を秒数に変換。
    """
    match = re.match((r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"), duration)
    if not match:
        return 0
    hours, minutes, seconds = match.groups(default="0")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
