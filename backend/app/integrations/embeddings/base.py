from typing import Protocol


class EmbeddingError(RuntimeError):
    """A safe embedding failure without credentials or response bodies."""


class EmbeddingProvider(Protocol):
    model: str
    dimension: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_query(self, text: str) -> list[float]: ...


def validate_vectors(vectors: list[list[float]], count: int, dimension: int) -> None:
    if len(vectors) != count:
        raise EmbeddingError("Embedding response count mismatch")
    if any(len(vector) != dimension for vector in vectors):
        raise EmbeddingError("Embedding response dimension mismatch")
