from io import BytesIO

from bs4 import BeautifulSoup, Tag
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.knowledge.types import ExtractedBlock


class ExtractionError(RuntimeError):
    pass


def extract_pdf(content: bytes) -> tuple[list[ExtractedBlock], int]:
    try:
        reader = PdfReader(BytesIO(content))
    except PdfReadError as exc:
        raise ExtractionError("Corrupt or unreadable PDF") from exc
    blocks: list[ExtractedBlock] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text(extraction_mode="layout") or ""
        if text.strip():
            blocks.append(ExtractedBlock(text=text, page=page_number, kind="page"))
    if not blocks:
        raise ExtractionError("PDF contains no extractable text; OCR review required")
    return blocks, len(reader.pages)


def _table_text(table: Tag) -> str:
    rows: list[str] = []
    for row in table.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def extract_html(content: bytes) -> tuple[list[ExtractedBlock], None]:
    soup = BeautifulSoup(content, "html.parser")
    for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "form"]):
        node.decompose()
    root = soup.find("main") or soup.find("article") or soup.body
    if root is None:
        raise ExtractionError("HTML has no readable body")
    blocks: list[ExtractedBlock] = []
    section: str | None = None
    for node in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "table"]):
        if node.name in {"h1", "h2", "h3", "h4"}:
            section = node.get_text(" ", strip=True) or section
            continue
        text = _table_text(node) if node.name == "table" else node.get_text(" ", strip=True)
        if text:
            blocks.append(
                ExtractedBlock(
                    text=text,
                    section=section,
                    kind="table" if node.name == "table" else "paragraph",
                )
            )
    if not blocks:
        raise ExtractionError("HTML contains no extractable official content")
    return blocks, None


def extract(content: bytes, mime_type: str) -> tuple[list[ExtractedBlock], int | None]:
    if mime_type == "application/pdf":
        return extract_pdf(content)
    if mime_type in {"text/html", "application/xhtml+xml"}:
        return extract_html(content)
    raise ExtractionError(f"Unsupported extraction MIME type: {mime_type}")
