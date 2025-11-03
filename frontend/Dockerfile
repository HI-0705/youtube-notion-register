FROM node:18-alpine

WORKDIR /app

# package.jsonとlockファイルを先にコピーして、変更がない場合はキャッシュを利用する
COPY package*.json ./
RUN npm install

# アプリケーションコードをコピー
COPY . .

EXPOSE 5173
