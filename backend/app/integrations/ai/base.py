from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from app.models.enums import Language


class AIProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerationEvidence:
    chunk_id: str
    content: str


@dataclass(frozen=True)
class GenerationRequest:
    question: str
    language: Language
    category: str
    intent: str
    farmer_context: str
    recent_context: tuple[str, ...]
    evidence: tuple[GenerationEvidence, ...]


class GeneratedAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=8000)
    requires_follow_up: bool = False
    attachment_recommended: bool = False
    safety_flags: list[str] = Field(default_factory=list, max_length=10)


class GeneratedFaq(BaseModel):
    question_en: str = Field(min_length=1, max_length=1000)
    question_hi: str = Field(min_length=1, max_length=1000)
    question_mr: str = Field(min_length=1, max_length=1000)
    answer_en: str = Field(min_length=1, max_length=4000)
    answer_hi: str = Field(min_length=1, max_length=4000)
    answer_mr: str = Field(min_length=1, max_length=4000)


class AIProvider(Protocol):
    async def generate_grounded_answer(self, request: GenerationRequest) -> GeneratedAnswer: ...

    async def generate_grounded_faq(
        self, question: str, evidence: tuple[GenerationEvidence, ...]
    ) -> GeneratedFaq: ...
