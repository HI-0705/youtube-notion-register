import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from ..core.config import GEMINI_API_KEY, MODEL
from ..core.exceptions import APIException
from ..core.logging import get_logger
from ..models import schemas

logger = get_logger(__name__)


class AnalysisService:
    """動画字幕分析クラス"""

    def __init__(self):
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY is not configured.")
            raise APIException(
                status_code=500,
                message="Gemini API key is not configured.",
                error_code="E010",
            )
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(MODEL)
        self.generation_config = GenerationConfig(
            temperature=0.8,
            response_mime_type="application/json",
        )
        logger.info(f"AnalysisService initialized successfully.")

    def _create_prompt(self, transcript: str) -> str:
        """プロンプトを作成"""

        prompt = f"""
        以下のYouTube動画の字幕テキストを分析し、内容を要約してJSON形式で回答してください：

        制約：
        - 要約は400-1000文字、Markdown形式
        - タイトルは30文字以内
        - 分類タグは最大3つ
        - 感情タグは1つのみ

        分類タグ選択肢: ["音楽", "動物", "スポーツ", "旅行", "ゲーム", "コメディ", "エンターテインメント", "教育", "科学", "映画", "アニメ", "クラシック", "ドキュメンタリー", "ドラマ", "ショートムービー", "その他"]
        感情タグ選択肢: ["感動", "愉快", "驚愕", "啓発", "考察", "癒着", "その他"]

        字幕テキスト:
        {transcript}

        回答は必ずJSON形式で、以下のキーを持つオブジェクトとしてください:
        {{
        "summary": "Markdown形式の要約",
        "suggested_titles": "提案タイトル",
        "categories": ["タグ1", "タグ2"],
        "emotions": "感情タグ"
        }}
        """
        return prompt

    async def analyze_transcript(self, transcript: str) -> schemas.AnalysisResult:
        """字幕テキストの分析結果を取得
        Args:
            transcript (str): 字幕テキスト
        Returns:
            schemas.AnalysisResult: 分析結果
        """
        prompt = self._create_prompt(transcript)

        try:
            logger.info("Sending analysis request to Gemini API.")
            response = await self.model.generate_content_async(
                prompt,
                generation_config=self.generation_config,
            )

            analysis_result = schemas.AnalysisResult.model_validate_json(response.text)
            logger.info("Analysis completed successfully.")
            return analysis_result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise APIException(
                status_code=502,
                message=f"An error occurred while communicating with the analysis service: {e}",
                error_code="E008",
            )
