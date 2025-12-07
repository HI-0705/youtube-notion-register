import os
import aiofiles
from fastapi import status

from ..core.config import DATA_DIR
from ..core.exceptions import APIException
from ..models.schemas import SessionInfo


class SessionService:
    """セッションファイル管理クラス"""

    def _get_session_file_path(self, session_id: str) -> str:
        """セッションIDに対応するファイルパスを取得"""
        return os.path.join(DATA_DIR, f"{session_id}.json")

    async def save_session(self, session_info: SessionInfo):
        """セッション情報をファイルに保存"""
        session_file_path = self._get_session_file_path(session_info.session_id)
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(DATA_DIR, exist_ok=True)
            async with aiofiles.open(session_file_path, "w", encoding="utf-8") as f:
                await f.write(session_info.model_dump_json(indent=4))

        except Exception as e:
            raise APIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to save session data: {e}",
                error_code="E007",
            )

    async def load_session(self, session_id: str) -> SessionInfo:
        """セッション情報をファイルから読み込み"""
        session_file_path = self._get_session_file_path(session_id)
        try:
            async with aiofiles.open(session_file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                return SessionInfo.model_validate_json(content)
        except FileNotFoundError:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Session ID '{session_id}' not found.",
                error_code="E007",
            )
        except Exception as e:
            raise APIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Failed to load session data: {e}",
                error_code="E007",
            )
