import os
import re

# 環境変数からAPI_KEYの値を取得
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 使用するモデルの指定
MODEL = "gpt-4o"

# APIキーが設定されていない場合のガード処理
_required = {"YOUTUBE_API_KEY": YOUTUBE_API_KEY, "OPENAI_API_KEY": OPENAI_API_KEY}
_missing = [k for k, v in _required.items() if not v]
if _missing:
    raise RuntimeError(f"必須環境変数が設定されていません: {', '.join(_missing)}")

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
