# デプロイ手順書

このドキュメントは、`youtube-notion-register` アプリケーションをサーバーにデプロイする手順を説明します。

## 1. 前提条件

デプロイ先のサーバーには、以下のソフトウェアがインストールされている必要があります。

- Docker
- Docker Compose
- Git

## 2. 環境設定

アプリケーションの動作には、いくつかのAPIキーと設定が必要です。これらは `.env` ファイルを通じて環境変数として提供されます。

1.  プロジェクトのルートディレクトリにある `.env.example` ファイルをコピーして `.env` ファイルを作成します。
    ```bash
    cp .env.example .env
    ```

2.  作成した `.env` ファイルをエディタで開き、各変数の値を設定します。
    ```env
    # YouTube Data API
    # Google Cloud Consoleで取得
    YOUTUBE_API_KEY=your-youtube-api-key-here

    # Google Gemini API
    # Google AI Studioで取得
    GEMINI_API_KEY=your-gemini-api-key-here

    # Notion API
    # Notionのインテグレーションページ (my-integrations) で取得
    NOTION_API_KEY=your-notion-integration-token-here
    NOTION_DATABASE_ID=your-database-id-here

    # フロントエンドからのアクセスを許可するオリジン（通常は変更不要）
    CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
    ```
    - 本番環境では、`CORS_ORIGINS` に実際のドメイン名（例: `https://your-domain.com`）を追加する必要があります。
    - **注意**: `.env` ファイルにはAPIキーなどの機密情報が含まれるため、このファイルをGitリポジトリにコミットしないでください。プロジェクトの `.gitignore` ファイルに `.env` が含まれていることを確認してください。

## 3. デプロイ手順

このプロジェクトは `docker-compose` を使って簡単にデプロイできます。

1.  **プロジェクトをサーバーにクローンします。**
    ```bash
    git clone https://github.com/HI-0705/youtube-notion-register.git
    cd youtube-notion-register
    ```

2.  **前述の手順で `.env` ファイルを作成・編集します。**

3.  **Dockerコンテナをビルドし、バックグラウンドで起動します。**
    ```bash
    docker-compose up --build -d
    ```
    `--build` オプションは、イメージを強制的に再ビルドします。初回起動時やコードを更新した際に使用してください。
    `-d` オプションは、コンテナをバックグラウンドで実行（デタッチモード）します。

## 4. 動作確認

デプロイが成功したかを確認するには、以下のコマンドを使用します。

- **コンテナの状態確認:**
  ```bash
  docker-compose ps
  ```
  `frontend` と `backend` の両方のコンテナが `Up` 状態であることを確認します。

- **ログの確認:**
  ```bash
  # すべてのログをストリーミング表示
  docker-compose logs -f

  # バックエンドのみのログを表示
  docker-compose logs -f backend
  ```

- **アプリケーションへのアクセス:**
  ブラウザで `http://<サーバーのIPアドレス>:5173` にアクセスし、フロントエンドが表示されることを確認します。

## 5. 本番環境での考慮事項

### HTTPS化
実際の公開環境では、セキュリティのためにHTTPS通信が必須です。Nginxなどのリバースプロキシを `docker-compose` で起動したコンテナの前段に配置し、SSL/TLS証明書（例: Let's Encrypt）を適用してHTTPS化することを強く推奨します。

Nginxは、ポート `5173` をフロントエンドに、ポート `8000` をバックエンドにプロキシするように設定します。
