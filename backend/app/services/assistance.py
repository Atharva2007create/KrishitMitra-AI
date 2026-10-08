import logging
import re
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from time import perf_counter
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.ingestion.taxonomy import infer_topic
from app.integrations.ai import AIProvider, GenerationRequest
from app.integrations.ai.base import AIProviderError, GenerationEvidence
from app.integrations.ai.policy import has_prompt_injection
from app.integrations.government import LiveAgricultureDataService
from app.integrations.government.http import GovernmentSourceError
from app.models.entities import (
    ChatSession,
    CropCycle,
    Farm,
    FarmerProfile,
    ImageAnalysis,
    Message,
    MessageAttachment,
    ProblemCategory,
    ResponseCitation,
    User,
)
from app.models.enums import AttachmentStatus, EvidenceStatus, Language, RecordStatus, SenderType
from app.schemas.assistance import (
    AssistanceCategory,
    AssistanceResponse,
    FaqCitationResponse,
)
from app.services.retrieval import RetrievalService

logger = logging.getLogger(__name__)

LIVE_WEATHER_TERMS = (
    "today's weather",
    "weather today",
    "rain tomorrow",
    "will it rain",
    "आज मौसम",
    "कल बारिश",
    "आज पाऊस",
    "उद्या पाऊस",
)
LIVE_MARKET_TERMS = (
    "today's price",
    "current price",
    "mandi price",
    "market price",
    "आज भाव",
    "आजची किंमत",
    "बाजार भाव",
)
PESTICIDE_RESTRICTED_TERMS = (
    "dosage",
    "dose",
    "concentration",
    "waiting period",
    "application frequency",
    "how often",
    "कितनी मात्रा",
    "खुराक",
    "प्रमाण",
    "फवारणी किती",
)
IMAGE_TERMS = (
    "upload a photo",
    "upload image",
    "analyze photo",
    "analyse photo",
    "camera",
    "फोटो अपलोड",
    "चित्र अपलोड",
    "फोटो तपासा",
)
UNSUPPORTED_CROPS = (
    "rice",
    "wheat",
    "cotton",
    "soybean",
    "maize",
    "धान",
    "गेहूं",
    "कापूस",
    "सोयाबीन",
)
OUT_OF_SCOPE_TERMS = (
    "tractor gearbox",
    "laptop repair",
    "bitcoin",
    "लैपटॉप",
    "बिटकॉइन",
)


def contains_term(text: str, terms: tuple[str, ...]) -> bool:
    """Match complete words/phrases so `rice` does not accidentally match `price`."""
    return any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) for term in terms)


def detect_language(text: str, fallback: Language) -> Language:
    if not re.search(r"[\u0900-\u097f]", text):
        return fallback
    marathi_markers = ("आहे", "काय", "तूर", "पाऊस", "माझ", "सांगा", "करायचा")
    return Language.MR if any(marker in text for marker in marathi_markers) else Language.HI


def requires_live_data(text: str) -> bool:
    if contains_term(text, (*LIVE_WEATHER_TERMS, *LIVE_MARKET_TERMS)):
        return True
    current_markers = ("today", "current", "tomorrow", "आज", "कल", "उद्या")
    market_markers = ("price", "mandi", "market", "भाव", "किंमत")
    weather_markers = ("weather", "rain", "मौसम", "बारिश", "पाऊस")
    return any(marker in text for marker in current_markers) and any(
        marker in text for marker in (*market_markers, *weather_markers)
    )


SAFE_MESSAGES: dict[EvidenceStatus, dict[Language, str]] = {
    EvidenceStatus.INSUFFICIENT: {
        Language.EN: (
            "Verified information was not found in the currently available government "
            "Tur knowledge."
        ),
        Language.HI: "वर्तमान सरकारी अरहर ज्ञान में सत्यापित जानकारी नहीं मिली।",
        Language.MR: "सध्या उपलब्ध सरकारी तूर माहितीत पडताळलेली माहिती मिळाली नाही.",
    },
    EvidenceStatus.REQUIRES_LIVE_DATA: {
        Language.EN: "This question requires current live data, which is not connected in Phase 4.",
        Language.HI: "इस प्रश्न के लिए वर्तमान लाइव डेटा चाहिए, जो चरण 4 में जुड़ा नहीं है।",
        Language.MR: "या प्रश्नासाठी सध्याचा थेट डेटा आवश्यक आहे; तो टप्पा 4 मध्ये जोडलेला नाही.",
    },
    EvidenceStatus.REQUIRES_REGULATORY_VALIDATION: {
        Language.EN: (
            "Exact pesticide instructions require current regulatory validation before "
            "they can be provided safely."
        ),
        Language.HI: "सटीक कीटनाशक निर्देश देने से पहले वर्तमान नियामक सत्यापन आवश्यक है।",
        Language.MR: "अचूक कीटकनाशक सूचना देण्यापूर्वी सध्याची नियामक पडताळणी आवश्यक आहे.",
    },
    EvidenceStatus.REQUIRES_IMAGE_ANALYSIS: {
        Language.EN: (
            "Image analysis is still processing or needs a clearer Tur crop image."
        ),
        Language.HI: "चित्र विश्लेषण जारी है या अरहर की अधिक स्पष्ट तस्वीर चाहिए।",
        Language.MR: "प्रतिमा विश्लेषण सुरू आहे किंवा तूर पिकाचा अधिक स्पष्ट फोटो आवश्यक आहे.",
    },
    EvidenceStatus.LIVE_DATA_UNAVAILABLE: {
        Language.EN: "The official live source is currently unavailable. No value was estimated.",
        Language.HI: "आधिकारिक लाइव स्रोत अभी उपलब्ध नहीं है। कोई अनुमानित मान नहीं दिया गया।",
        Language.MR: "अधिकृत थेट स्रोत सध्या उपलब्ध नाही. कोणताही अंदाज दिलेला नाही.",
    },
}


class RateLimitExceeded(RuntimeError):
    pass


class AssistanceRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[UUID, deque[datetime]] = defaultdict(deque)

    def check(self, user_id: UUID, limit: int) -> None:
        now = datetime.now(UTC)
        cutoff = now - timedelta(minutes=1)
        bucket = self._requests[user_id]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            raise RateLimitExceeded("Personalized assistance rate limit exceeded")
        bucket.append(now)


rate_limiter = AssistanceRateLimiter()


class GuidedAssistanceService:
    def __init__(
        self,
        session: AsyncSession,
        retrieval: RetrievalService,
        ai: AIProvider,
        settings: Settings,
        live_data: LiveAgricultureDataService | None = None,
    ) -> None:
        self.session = session
        self.retrieval = retrieval
        self.ai = ai
        self.settings = settings
        self.live_data = live_data or LiveAgricultureDataService(settings)

    async def _persist_external_response(
        self,
        chat: ChatSession,
        category: ProblemCategory,
        question: str,
        language: Language,
        intent: str,
        answer: str,
        live_data: list[dict[str, object]],
        data_timestamp: datetime | None,
        safety_flags: list[str],
    ) -> AssistanceResponse:
        user_message = Message(
            chat_session_id=chat.id,
            sender_type=SenderType.USER,
            content=question,
            language=language,
            intent=intent,
        )
        assistant = Message(
            chat_session_id=chat.id,
            sender_type=SenderType.ASSISTANT,
            content=answer,
            language=language,
            intent=intent,
            evidence_status=EvidenceStatus.SUFFICIENT,
            metadata_json={
                "safety_flags": safety_flags,
                "live_data": live_data,
                "data_timestamp": data_timestamp.isoformat() if data_timestamp else None,
            },
        )
        chat.last_message_at = datetime.now(UTC)
        self.session.add_all([user_message, assistant])
        await self.session.commit()
        await self.session.refresh(assistant)
        return AssistanceResponse(
            message_id=assistant.id,
            session_id=chat.id,
            category=AssistanceCategory(
                code=category.code, title=str(getattr(category, f"display_name_{language.value}"))
            ),
            answer=answer,
            language=language,
            intent=intent,
            evidence_status=EvidenceStatus.SUFFICIENT,
            citations=[],
            live_data=live_data,
            data_timestamp=data_timestamp,
            safety_flags=safety_flags,
            created_at=assistant.created_at,
        )

    async def _answer_live_data(
        self,
        chat: ChatSession,
        category: ProblemCategory,
        profile: FarmerProfile | None,
        question: str,
        language: Language,
        intent: str,
        lowered: str,
        flags: list[str],
    ) -> AssistanceResponse:
        if profile is None:
            return await self._persist_safe_response(
                chat,
                question,
                language,
                intent,
                EvidenceStatus.LIVE_DATA_UNAVAILABLE,
                category,
                [*flags, "LOCATION_REQUIRED"],
            )
        try:
            if contains_term(lowered, LIVE_MARKET_TERMS) or any(
                marker in lowered for marker in ("price", "market", "mandi", "भाव", "किंमत")
            ):
                prices = await self.live_data.market_prices(
                    profile.state, profile.district, commodity="Pigeon Pea (Arhar Fali)"
                )
                latest = max(item.arrival_date for item in prices)
                lines = [
                    f"{item.market}: modal ₹{item.modal_price or 'not reported'} per quintal "
                    f"(min ₹{item.minimum_price or 'not reported'}, "
                    f"max ₹{item.maximum_price or 'not reported'}, {item.arrival_date.date()})"
                    for item in prices[:5]
                ]
                answer = "Official AGMARKNET records:\n" + "\n".join(lines)
                data = [item.model_dump(mode="json") for item in prices[:5]]
            else:
                observations = await self.live_data.weather(profile.state, profile.district)
                latest = max(item.observed_at for item in observations)
                lines = [
                    f"{item.station_name}: {item.temperature_c or 'temperature not reported'}°C, "
                    f"humidity {item.relative_humidity_percent or 'not reported'}%, "
                    f"24-hour rain {item.rainfall_24h_mm or 'not reported'} mm "
                    f"at {item.observed_at.isoformat()}"
                    for item in observations[:3]
                ]
                answer = "Official IMD observations:\n" + "\n".join(lines)
                data = [item.model_dump(mode="json") for item in observations[:3]]
            return await self._persist_external_response(
                chat, category, question, language, intent, answer, data, latest, flags
            )
        except GovernmentSourceError as exc:
            logger.warning("live_source_unavailable", extra={"source_error_code": exc.code})
            return await self._persist_safe_response(
                chat,
                question,
                language,
                intent,
                EvidenceStatus.LIVE_DATA_UNAVAILABLE,
                category,
                [*flags, exc.code],
            )

    async def _owned_context(
        self, user: User, session_id: UUID
    ) -> tuple[ChatSession, ProblemCategory, FarmerProfile | None, CropCycle | None, Farm | None]:
        chat = await self.session.scalar(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        )
        if chat is None or chat.problem_category_id is None:
            raise LookupError("Guided assistance session not found")
        category = await self.session.get(ProblemCategory, chat.problem_category_id)
        if category is None or not category.is_active:
            raise LookupError("Problem category is unavailable")
        profile = await self.session.scalar(
            select(FarmerProfile).where(FarmerProfile.user_id == user.id)
        )
        cycle = (
            await self.session.get(CropCycle, chat.crop_cycle_id) if chat.crop_cycle_id else None
        )
        farm = await self.session.get(Farm, cycle.farm_id) if cycle else None
        return chat, category, profile, cycle, farm

    @staticmethod
    def _context_text(
        profile: FarmerProfile | None, cycle: CropCycle | None, farm: Farm | None
    ) -> str:
        values: list[str] = []
        if profile:
            values.extend(
                [
                    f"State: {profile.state}",
                    f"District: {profile.district}",
                    f"Taluka: {profile.taluka}",
                ]
            )
        if farm:
            if farm.soil_type:
                values.append(f"Soil type: {farm.soil_type}")
            if farm.irrigation_type:
                values.append(f"Irrigation type: {farm.irrigation_type}")
        if cycle:
            values.extend([f"Crop: {cycle.crop_name}", f"Sowing date: {cycle.sowing_date}"])
            if cycle.crop_variety:
                values.append(f"Variety: {cycle.crop_variety}")
            if cycle.estimated_crop_stage:
                values.append(f"Crop stage: {cycle.estimated_crop_stage}")
        return "\n".join(values) or "No farmer or crop details were supplied."

    async def _recent_context(self, session_id: UUID) -> tuple[str, ...]:
        messages = list(
            await self.session.scalars(
                select(Message)
                .where(Message.chat_session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(6)
            )
        )
        return tuple(f"{item.sender_type.value}: {item.content}" for item in reversed(messages))

    async def _persist_safe_response(
        self,
        chat: ChatSession,
        question: str,
        language: Language,
        intent: str,
        evidence_status: EvidenceStatus,
        category: ProblemCategory,
        safety_flags: list[str],
        persist_user: bool = True,
    ) -> AssistanceResponse:
        user_message = Message(
            chat_session_id=chat.id,
            sender_type=SenderType.USER,
            content=question,
            language=language,
            intent=intent,
        )
        assistant = Message(
            chat_session_id=chat.id,
            sender_type=SenderType.ASSISTANT,
            content=SAFE_MESSAGES[evidence_status][language],
            language=language,
            intent=intent,
            evidence_status=evidence_status,
            metadata_json={"safety_flags": safety_flags},
        )
        chat.last_message_at = datetime.now(UTC)
        if persist_user:
            self.session.add(user_message)
        self.session.add(assistant)
        await self.session.commit()
        await self.session.refresh(assistant)
        title = str(getattr(category, f"display_name_{language.value}"))
        return AssistanceResponse(
            message_id=assistant.id,
            session_id=chat.id,
            category=AssistanceCategory(code=category.code, title=title),
            answer=assistant.content,
            language=language,
            intent=intent,
            evidence_status=evidence_status,
            citations=[],
            requires_follow_up=False,
            attachment_recommended=evidence_status == EvidenceStatus.REQUIRES_IMAGE_ANALYSIS,
            requires_live_data=evidence_status == EvidenceStatus.REQUIRES_LIVE_DATA,
            requires_regulatory_validation=(
                evidence_status == EvidenceStatus.REQUIRES_REGULATORY_VALIDATION
            ),
            safety_flags=safety_flags,
            created_at=assistant.created_at,
        )

    async def answer(
        self,
        user: User,
        session_id: UUID,
        question: str,
        requested_language: Language | None,
        attachment_ids: list[UUID],
    ) -> AssistanceResponse:
        rate_limiter.check(user.id, self.settings.assistance_rate_limit_per_minute)
        if len(question) > self.settings.assistance_max_question_length:
            raise ValueError("Question exceeds configured maximum length")
        chat, category, profile, cycle, farm = await self._owned_context(user, session_id)
        fallback_language = profile.preferred_language if profile else chat.language
        language = requested_language or detect_language(question, fallback_language)
        lowered = " ".join(question.lower().split())
        intent = infer_topic(question).value
        flags: list[str] = []
        if has_prompt_injection(question):
            flags.append("PROMPT_INJECTION_ATTEMPT")
        if contains_term(lowered, (*UNSUPPORTED_CROPS, *OUT_OF_SCOPE_TERMS)):
            flags.append("UNSUPPORTED_CROP")
            return await self._persist_safe_response(
                chat, question, language, intent, EvidenceStatus.INSUFFICIENT, category, flags
            )
        if requires_live_data(lowered):
            flags.append("LIVE_DATA_REQUIRED")
            return await self._answer_live_data(
                chat, category, profile, question, language, intent, lowered, flags
            )
        if contains_term(lowered, PESTICIDE_RESTRICTED_TERMS):
            flags.append("REGULATORY_VALIDATION_REQUIRED")
            return await self._persist_safe_response(
                chat,
                question,
                language,
                intent,
                EvidenceStatus.REQUIRES_REGULATORY_VALIDATION,
                category,
                flags,
            )
        if contains_term(lowered, IMAGE_TERMS) and not attachment_ids:
            flags.append("IMAGE_ANALYSIS_NOT_IMPLEMENTED")
            return await self._persist_safe_response(
                chat,
                question,
                language,
                intent,
                EvidenceStatus.REQUIRES_IMAGE_ANALYSIS,
                category,
                flags,
            )
        attachments: list[MessageAttachment] = []
        if attachment_ids:
            attachments = list(
                await self.session.scalars(
                    select(MessageAttachment).where(
                        MessageAttachment.id.in_(attachment_ids),
                        MessageAttachment.user_id == user.id,
                        MessageAttachment.chat_session_id == chat.id,
                        MessageAttachment.status.in_(
                            [
                                AttachmentStatus.UPLOADED,
                                AttachmentStatus.PENDING_ANALYSIS,
                                AttachmentStatus.PROCESSING,
                                AttachmentStatus.COMPLETED,
                            ]
                        ),
                    )
                )
            )
            if {item.id for item in attachments} != set(attachment_ids):
                raise LookupError("Attachment not found")
            image_context: list[str] = []
            for attachment in attachments:
                if attachment.attachment_type.value != "IMAGE":
                    continue
                analysis = await self.session.scalar(
                    select(ImageAnalysis).where(ImageAnalysis.attachment_id == attachment.id)
                )
                if analysis is None or analysis.status in (
                    RecordStatus.PENDING,
                    RecordStatus.PROCESSING,
                ):
                    return await self._persist_safe_response(
                        chat,
                        question,
                        language,
                        intent,
                        EvidenceStatus.REQUIRES_IMAGE_ANALYSIS,
                        category,
                        [*flags, "IMAGE_ANALYSIS_PENDING"],
                    )
                if analysis.status == RecordStatus.IMAGE_INSUFFICIENT:
                    return await self._persist_safe_response(
                        chat,
                        question,
                        language,
                        intent,
                        EvidenceStatus.REQUIRES_IMAGE_ANALYSIS,
                        category,
                        [*flags, "IMAGE_INSUFFICIENT"],
                    )
                if analysis.status == RecordStatus.FAILED:
                    return await self._persist_safe_response(
                        chat,
                        question,
                        language,
                        intent,
                        EvidenceStatus.REQUIRES_IMAGE_ANALYSIS,
                        category,
                        [*flags, "IMAGE_ANALYSIS_FAILED"],
                    )
                image_context.append(
                    f"Visual observations (non-authoritative): {analysis.observed_symptoms}; "
                    f"candidate issues (not diagnoses): {analysis.candidate_issues}"
                )
            if image_context:
                flags.append("IMAGE_OBSERVATION_USED_FOR_RETRIEVAL")

        user_message = Message(
            chat_session_id=chat.id,
            sender_type=SenderType.USER,
            content=question,
            language=language,
            intent=intent,
        )
        chat.last_message_at = datetime.now(UTC)
        self.session.add(user_message)
        await self.session.flush()
        for attachment in attachments:
            attachment.message_id = user_message.id
        await self.session.commit()

        retrieval_query = question
        if attachment_ids and "image_context" in locals() and image_context:
            retrieval_query = f"{question}\n" + "\n".join(image_context)
        if intent == "OTHER":
            retrieval_query = f"{question}\nProblem category: {category.display_name_en}"
        retrieval_started = perf_counter()
        result = await self.retrieval.retrieve_evidence(retrieval_query, crop="PIGEONPEA")
        retrieval_latency_ms = round((perf_counter() - retrieval_started) * 1000, 2)
        if not result.sufficient:
            return await self._persist_safe_response(
                chat,
                question,
                language,
                intent,
                EvidenceStatus.INSUFFICIENT,
                category,
                [*flags, "NO_VERIFIED_EVIDENCE"],
                persist_user=False,
            )

        gemini_started = perf_counter()
        try:
            generated = await self.ai.generate_grounded_answer(
                GenerationRequest(
                    question=retrieval_query,
                    language=language,
                    category=category.code,
                    intent=intent,
                    farmer_context=self._context_text(profile, cycle, farm),
                    recent_context=await self._recent_context(chat.id),
                    evidence=tuple(
                        GenerationEvidence(str(item.chunk_id), item.content)
                        for item in result.results
                    ),
                )
            )
        except AIProviderError:
            logger.exception("assistance_generation_failure", extra={"session_id": str(chat.id)})
            raise

        assistant = Message(
            chat_session_id=chat.id,
            sender_type=SenderType.ASSISTANT,
            content=generated.answer,
            language=language,
            intent=intent,
            evidence_status=EvidenceStatus.SUFFICIENT,
            metadata_json={
                "safety_flags": [*flags, *generated.safety_flags],
                "attachment_recommended": generated.attachment_recommended,
                "requires_follow_up": generated.requires_follow_up,
            },
        )
        self.session.add(assistant)
        await self.session.flush()
        for order, item in enumerate(result.results):
            self.session.add(
                ResponseCitation(
                    message_id=assistant.id,
                    knowledge_chunk_id=item.chunk_id,
                    citation_order=order,
                )
            )
        await self.session.commit()
        await self.session.refresh(assistant)
        logger.info(
            "guided_assistance_completed",
            extra={
                "session_id": str(chat.id),
                "problem_category": category.code,
                "intent": intent,
                "language": language.value,
                "evidence_status": EvidenceStatus.SUFFICIENT.value,
                "retrieval_latency_ms": retrieval_latency_ms,
                "gemini_latency_ms": round((perf_counter() - gemini_started) * 1000, 2),
                "citation_count": len(result.results),
            },
        )
        citations = [
            FaqCitationResponse(
                organization=item.citation.organization,
                document_title=item.citation.document_title,
                source_url=item.citation.source_url,
                page_start=item.citation.page_start,
                page_end=item.citation.page_end,
                section=item.citation.section,
            )
            for item in result.results
        ]
        title = str(getattr(category, f"display_name_{language.value}"))
        return AssistanceResponse(
            message_id=assistant.id,
            session_id=chat.id,
            category=AssistanceCategory(code=category.code, title=title),
            answer=assistant.content,
            language=language,
            intent=intent,
            evidence_status=EvidenceStatus.SUFFICIENT,
            citations=citations,
            requires_follow_up=generated.requires_follow_up,
            attachment_recommended=generated.attachment_recommended,
            safety_flags=[*flags, *generated.safety_flags],
            created_at=assistant.created_at,
        )
