import os

# 環境変数からYOUTUBE_API_KEYの値を取得します
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# APIキーが設定されていなかった場合のガード処理
if not YOUTUBE_API_KEY:
    print("警告: 環境変数 'YOUTUBE_API_KEY' が設定されていません。")
