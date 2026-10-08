import re

from app.models.enums import KnowledgeTopic

CROP_ALIASES = {"tur", "toor", "arhar", "pigeonpea", "pigeon pea", "red gram", "cajanus cajan"}
TOPIC_KEYWORDS: dict[KnowledgeTopic, tuple[str, ...]] = {
    KnowledgeTopic.SOIL: ("soil", "ph ", "soil type"),
    KnowledgeTopic.VARIETY: ("variety", "varieties", "cultivar", "hybrid"),
    KnowledgeTopic.SEED_TREATMENT: ("seed treatment", "treat the seed", "g/kg seed"),
    KnowledgeTopic.SOWING: ("sowing", "sown", "planting time"),
    KnowledgeTopic.SPACING: ("spacing", "row-to-row", "plant-to-plant"),
    KnowledgeTopic.INTERCROPPING: ("intercrop", "intercropping", "mixed cropping"),
    KnowledgeTopic.FERTILIZER: ("fertilizer", "fertiliser", "kg n", "phosphorus"),
    KnowledgeTopic.IRRIGATION: ("irrigation", "water requirement"),
    KnowledgeTopic.DRAINAGE: ("drainage", "waterlogging", "water logging"),
    KnowledgeTopic.WEED_MANAGEMENT: ("weed", "herbicide"),
    KnowledgeTopic.PEST: ("insect", "pest", "pod borer", "pod fly", "helicoverpa"),
    KnowledgeTopic.DISEASE: ("disease", "wilt", "sterility mosaic", "phytophthora"),
    KnowledgeTopic.HARVEST: ("harvest", "maturity", "mature"),
    KnowledgeTopic.POST_HARVEST: ("post-harvest", "post harvest"),
    KnowledgeTopic.STORAGE: ("storage", "stored", "bruchid"),
    KnowledgeTopic.PROCESSING: ("processing", "processed"),
    KnowledgeTopic.MILLING: ("milling", "dal mill", "dehulling"),
    KnowledgeTopic.CLIMATE: ("climate", "rainfall", "temperature"),
    KnowledgeTopic.LAND_PREPARATION: ("land preparation", "tillage", "ploughing"),
    KnowledgeTopic.NUTRIENT_MANAGEMENT: ("nutrient", "micronutrient"),
}


def normalize_crop(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value.strip().lower())
    if cleaned not in CROP_ALIASES:
        raise ValueError(f"Unsupported Phase 3 crop: {value}")
    return "PIGEONPEA"


def contains_any_term(text: str, terms: list[str]) -> bool:
    """Match complete terms so the alias ``tur`` cannot match ``agriculture``."""
    lowered = text.lower()
    return any(re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", lowered) for term in terms)


def infer_topic(text: str, section: str | None = None) -> KnowledgeTopic:
    haystack = f"{section or ''} {text}".lower()
    matches = [
        (topic, sum(haystack.count(keyword) for keyword in keywords))
        for topic, keywords in TOPIC_KEYWORDS.items()
    ]
    topic, count = max(matches, key=lambda item: item[1], default=(KnowledgeTopic.OTHER, 0))
    return topic if count else KnowledgeTopic.OTHER


def requires_regulatory_validation(text: str) -> bool:
    lowered = text.lower()
    return any(
        value in lowered
        for value in (
            "insecticide",
            "pesticide",
            "fungicide",
            "herbicide",
            "carbendazim",
            "imidacloprid",
        )
    )
