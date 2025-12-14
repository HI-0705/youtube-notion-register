import secrets


def generate_secure_token(length: int = 32) -> str:
    """ランダムトークンを生成する"""
    return secrets.token_hex(length)
