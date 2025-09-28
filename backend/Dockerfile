FROM python:3.10-slim

WORKDIR /app

# requirements.txtを先にコピーして、変更がない場合はキャッシュを利用する
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .
