import re
import unicodedata

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.ai import AIProvider
from app.integrations.ai.base import GenerationEvidence
from app.models.entities import FaqCitation, FaqItem, KnowledgeChunk, ProblemCategory
from app.models.enums import EvidenceStatus
from app.services.retrieval import RetrievalService

NUMERIC_TOKEN = re.compile(
    r"(?P<number>\d+(?:\.\d+)?)(?:\s*(?P<unit>%|kg/ha|kg|cm|mm|days?|DAS))?",
    re.I,
)


def _ascii_digits(value: str) -> str:
    return "".join(str(unicodedata.digit(char)) if char.isdigit() else char for char in value)


def validate_numeric_fidelity(evidence: str, *outputs: str) -> None:
    allowed_values: set[str] = set()
    allowed_with_units: set[tuple[str, str]] = set()
    for match in NUMERIC_TOKEN.finditer(evidence):
        number = _ascii_digits(match.group("number"))
        unit = (match.group("unit") or "").lower()
        allowed_values.add(number)
        if unit:
            allowed_with_units.add((number, unit))
    unsupported: set[str] = set()
    for output in outputs:
        for match in NUMERIC_TOKEN.finditer(output):
            number = _ascii_digits(match.group("number"))
            unit = (match.group("unit") or "").lower()
            if number not in allowed_values or (unit and (number, unit) not in allowed_with_units):
                unsupported.add(match.group(0))
    if unsupported:
        raise ValueError(
            "Generated FAQ introduced unsupported numeric values: " + ", ".join(sorted(unsupported))
        )


class FaqCurationService:
    def __init__(self, session: AsyncSession, retrieval: RetrievalService, ai: AIProvider) -> None:
        self.session = session
        self.retrieval = retrieval
        self.ai = ai

    async def generate(
        self, category: ProblemCategory, question: str, display_order: int, activate: bool
    ) -> FaqItem | None:
        result = await self.retrieval.retrieve_evidence(question, crop="PIGEONPEA", limit=5)
        if not result.sufficient:
            return None
        evidence = tuple(
            GenerationEvidence(str(item.chunk_id), item.content) for item in result.results
        )
        generated = await self.ai.generate_grounded_faq(question, evidence)
        evidence_text = "\n".join(item.content for item in result.results)
        validate_numeric_fidelity(
            evidence_text, generated.answer_en, generated.answer_hi, generated.answer_mr
        )
        faq = await self.session.scalar(
            select(FaqItem).where(
                FaqItem.problem_category_id == category.id,
                FaqItem.canonical_question == question,
            )
        )
        if faq is None:
            faq = FaqItem(
                problem_category_id=category.id,
                canonical_question=question,
                question_en=generated.question_en,
                question_hi=generated.question_hi,
                question_mr=generated.question_mr,
                answer_en=generated.answer_en,
                answer_hi=generated.answer_hi,
                answer_mr=generated.answer_mr,
                evidence_status=EvidenceStatus.SUFFICIENT,
                is_active=activate,
                display_order=display_order,
                metadata_json={"generation": "controlled-phase4"},
            )
            self.session.add(faq)
            await self.session.flush()
        else:
            faq.question_en = generated.question_en
            faq.question_hi = generated.question_hi
            faq.question_mr = generated.question_mr
            faq.answer_en = generated.answer_en
            faq.answer_hi = generated.answer_hi
            faq.answer_mr = generated.answer_mr
            faq.evidence_status = EvidenceStatus.SUFFICIENT
            faq.is_active = activate
            faq.display_order = display_order
            await self.session.execute(delete(FaqCitation).where(FaqCitation.faq_id == faq.id))
        chunks = list(
            await self.session.scalars(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.id.in_([item.chunk_id for item in result.results]),
                    KnowledgeChunk.is_active.is_(True),
                )
            )
        )
        by_id = {chunk.id: chunk for chunk in chunks}
        if len(by_id) != len({item.chunk_id for item in result.results}):
            raise ValueError("FAQ citation evidence became inactive")
        for order, item in enumerate(result.results):
            chunk = by_id[item.chunk_id]
            self.session.add(
                FaqCitation(
                    faq_id=faq.id,
                    knowledge_chunk_id=chunk.id,
                    source_document_id=chunk.source_document_id,
                    citation_order=order,
                )
            )
        await self.session.commit()
        await self.session.refresh(faq)
        return faq
