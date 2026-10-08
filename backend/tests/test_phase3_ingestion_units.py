import hashlib

import pytest

from app.ingestion.acquisition import AcquisitionError, canonicalize_url
from app.ingestion.chunking import chunk_blocks
from app.ingestion.extraction import ExtractionError, extract_html, extract_pdf
from app.ingestion.normalization import normalize_text
from app.ingestion.taxonomy import (
    contains_any_term,
    infer_topic,
    normalize_crop,
    requires_regulatory_validation,
)
from app.integrations.embeddings.base import EmbeddingError, validate_vectors
from app.knowledge.types import ExtractedBlock
from app.models.enums import KnowledgeTopic


def test_official_source_allowlist_and_canonicalization() -> None:
    assert canonicalize_url("https://www.icar-iipr.org.in/varieties/#pigeonpea") == (
        "https://www.icar-iipr.org.in/varieties"
    )
    with pytest.raises(AcquisitionError):
        canonicalize_url("https://example.com/farming-advice")
    with pytest.raises(AcquisitionError):
        canonicalize_url("http://www.icar.gov.in/insecure")


def test_html_extraction_preserves_table_relationships_and_strips_scripts() -> None:
    html = b"""
    <html><body><main><h2>Pigeonpea spacing</h2>
    <p>Use the official recommendation exactly.</p>
    <table><tr><th>Row</th><th>Plant</th></tr><tr><td>120 cm</td><td>60 cm</td></tr></table>
    <script>ignore me</script></main></body></html>
    """
    blocks, page_count = extract_html(html)
    assert page_count is None
    assert any("Row | Plant" in block.text and "120 cm | 60 cm" in block.text for block in blocks)
    assert all("ignore me" not in block.text for block in blocks)


def test_corrupt_pdf_fails_truthfully() -> None:
    with pytest.raises(ExtractionError):
        extract_pdf(b"not a pdf")


def test_normalization_preserves_agricultural_numbers_and_units() -> None:
    source = "Apply  20 kg/ha\n\nat 25 DAS; spacing 120 x 60 cm and 0.1%."
    normalized = normalize_text(source)
    for exact in ("20 kg/ha", "25 DAS", "120 x 60 cm", "0.1%"):
        assert exact in normalized


def test_meaning_aware_chunking_keeps_table_as_a_unit() -> None:
    blocks = [
        ExtractedBlock("Sowing recommendations " + "word " * 90, page=3, section="Sowing"),
        ExtractedBlock(
            "Seed rate | Spacing\n20 kg/ha | 120 x 60 cm",
            page=3,
            section="Sowing",
            kind="table",
        ),
    ]
    chunks = chunk_blocks(blocks, target_words=150, overlap_words=20)
    assert len(chunks) == 1
    assert "20 kg/ha | 120 x 60 cm" in chunks[0].content
    assert chunks[0].page_start == 3
    assert chunks[0].section_title == "Sowing"
    assert chunks[0].content_hash == hashlib.sha256(chunks[0].content.encode()).hexdigest()


@pytest.mark.parametrize("alias", ["Tur", "Toor", "Arhar", "Pigeonpea", "Pigeon pea", "Red gram"])
def test_crop_aliases_normalize_to_pigeonpea(alias: str) -> None:
    assert normalize_crop(alias) == "PIGEONPEA"


def test_taxonomy_and_regulatory_flagging() -> None:
    assert infer_topic("Use 120 cm row spacing", "Spacing") == KnowledgeTopic.SPACING
    assert infer_topic("Fusarium wilt disease management") == KnowledgeTopic.DISEASE
    assert requires_regulatory_validation("Apply the official fungicide dose") is True


def test_short_crop_alias_does_not_match_inside_unrelated_word() -> None:
    assert contains_any_term("Tur sowing guidance", ["tur"]) is True
    assert contains_any_term("General agriculture guidance", ["tur"]) is False


def test_embedding_dimension_validation_is_strict() -> None:
    validate_vectors([[0.0] * 768], 1, 768)
    with pytest.raises(EmbeddingError):
        validate_vectors([[0.0] * 767], 1, 768)
    with pytest.raises(EmbeddingError):
        validate_vectors([], 1, 768)
