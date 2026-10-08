import asyncio
import random

from google import genai
from google.genai import types

from app.integrations.embeddings.base import EmbeddingError, validate_vectors


class GeminiEmbeddingProvider:
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-2",
        dimension: int = 768,
        max_attempts: int = 4,
    ) -> None:
        if not api_key:
            raise EmbeddingError("GEMINI_API_KEY is required for live embeddings")
        self.model = model
        self.dimension = dimension
        self.max_attempts = max_attempts
        self._client = genai.Client(api_key=api_key)

    async def _embed_one(self, text: str, instruction: str) -> list[float]:
        prompt = f"{instruction}\n\n{text}"
        for attempt in range(self.max_attempts):
            try:
                response = await asyncio.to_thread(
                    self._client.models.embed_content,
                    model=self.model,
                    contents=prompt,
                    config=types.EmbedContentConfig(output_dimensionality=self.dimension),
                )
                vectors = [list(item.values or []) for item in response.embeddings or []]
                validate_vectors(vectors, 1, self.dimension)
                return vectors[0]
            except EmbeddingError:
                raise
            except Exception as exc:
                if attempt + 1 >= self.max_attempts:
                    raise EmbeddingError("Embedding service failed after bounded retries") from exc
                await asyncio.sleep((2**attempt) + random.random())
        raise EmbeddingError("Embedding service failed")

    async def _embed(self, texts: list[str], instruction: str) -> list[list[float]]:
        if not texts or any(not text.strip() for text in texts):
            raise EmbeddingError("Embedding input must contain non-empty text")
        # Gemini's single-content endpoint may return one aggregate vector when
        # handed a list. Issue bounded individual requests so chunk/vector
        # cardinality is always explicit and verifiable.
        return [await self._embed_one(text, instruction) for text in texts]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(
            texts,
            "Represent this official agricultural evidence for retrieval. "
            "Preserve its technical meaning.",
        )

    async def embed_query(self, text: str) -> list[float]:
        return (
            await self._embed(
                [text],
                "Represent this farmer question for retrieving relevant agricultural evidence.",
            )
        )[0]
