import argparse
import asyncio
import json

from sqlalchemy import select, text

from app.core.settings import get_settings
from app.db.connection import SessionFactory, engine
from app.faq.catalog import FAQ_QUESTIONS
from app.integrations.ai import GeminiAIProvider
from app.integrations.embeddings import GeminiEmbeddingProvider
from app.integrations.embeddings.credentials import resolve_gemini_api_key
from app.models.entities import ProblemCategory
from app.services.faq import FaqCurationService
from app.services.retrieval import RetrievalService


async def run(category_slug: str | None, activate: bool) -> None:
    settings = get_settings()
    key = resolve_gemini_api_key(
        settings.gemini_api_key, settings.gemini_secret_arn, settings.aws_region
    )
    embeddings = GeminiEmbeddingProvider(
        key, settings.embedding_model, settings.embedding_dimension
    )
    ai = GeminiAIProvider(
        key,
        settings.gemini_model,
        settings.gemini_temperature,
        settings.gemini_max_output_tokens,
        settings.ai_request_timeout,
        settings.ai_max_retries,
        settings.gemini_fallback_model,
    )
    created = 0
    async with SessionFactory() as session:
        categories = list(
            await session.scalars(
                select(ProblemCategory).where(ProblemCategory.is_active.is_(True))
            )
        )
        for category in categories:
            if category_slug and category.slug != category_slug:
                continue
            service = FaqCurationService(
                session, RetrievalService(session, embeddings, settings), ai
            )
            for order, question in enumerate(FAQ_QUESTIONS.get(category.slug, ()), 1):
                faq = await service.generate(category, question, order, activate)
                if faq:
                    created += 1
                    print(f"{category.slug}: {faq.id} active={faq.is_active}")
    await engine.dispose()
    print(f"generated={created}")


async def audit() -> bool:
    async with SessionFactory() as session:
        categories = [
            dict(row)
            for row in (
                await session.execute(
                    text(
                        """
                        SELECT pc.slug, count(fi.id)::integer AS active_faqs
                        FROM problem_categories pc
                        LEFT JOIN faq_items fi
                          ON fi.problem_category_id = pc.id AND fi.is_active = true
                        WHERE pc.is_active = true
                        GROUP BY pc.display_order, pc.slug
                        ORDER BY pc.display_order
                        """
                    )
                )
            ).mappings()
        ]
        counts = dict(
            (
                await session.execute(
                    text(
                        """
                        SELECT
                          count(*) FILTER (WHERE is_active)::integer AS active_faqs,
                          count(*)::integer AS total_faqs,
                          count(*) FILTER (
                            WHERE is_active AND (
                              btrim(question_en) = '' OR btrim(question_hi) = '' OR
                              btrim(question_mr) = '' OR btrim(answer_en) = '' OR
                              btrim(answer_hi) = '' OR btrim(answer_mr) = ''
                            )
                          )::integer AS invalid_translations
                        FROM faq_items
                        """
                    )
                )
            )
            .mappings()
            .one()
        )
        invalid_citations = int(
            await session.scalar(
                text(
                    """
                    SELECT count(*)
                    FROM faq_items fi
                    WHERE fi.is_active = true
                      AND NOT EXISTS (
                        SELECT 1
                        FROM faq_citations fc
                        JOIN knowledge_chunks kc ON kc.id = fc.knowledge_chunk_id
                        JOIN source_documents sd
                          ON sd.id = fc.source_document_id
                         AND sd.id = kc.source_document_id
                        JOIN government_sources gs ON gs.id = sd.government_source_id
                        WHERE fc.faq_id = fi.id
                          AND kc.is_active = true
                          AND sd.is_active = true
                          AND sd.status::text = 'COMPLETED'
                          AND gs.is_active = true
                          AND gs.trust_status::text = 'APPROVED'
                      )
                    """
                )
            )
            or 0
        )
    await engine.dispose()
    result = {
        "active_categories": len(categories),
        **counts,
        "invalid_citations": invalid_citations,
        "by_category": categories,
    }
    print(json.dumps(result, sort_keys=True))
    return not counts["invalid_translations"] and invalid_citations == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate grounded multilingual Phase 4 FAQs")
    parser.add_argument("action", choices=("generate", "audit"), nargs="?", default="generate")
    parser.add_argument("--category")
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    if args.action == "audit":
        if not asyncio.run(audit()):
            raise SystemExit(1)
    else:
        asyncio.run(run(args.category, args.activate))


if __name__ == "__main__":
    main()
