import logging

from huggingface_hub import InferenceClient

from app.config import HF_LLM_PROVIDER, HF_TIMEOUT_SECONDS, HF_TOKEN, LLM_MAX_TOKENS, LLM_MODEL
from app.schemas.chat_schema import SourceResponse

logger = logging.getLogger("officeiq.chat")

SYSTEM_PROMPT = """Sen OfficeIQ kurumsal bilgi asistanısın.
Yalnızca verilen şirket dokümanı parçalarındaki bilgileri kullan.
Bağlamda cevap yoksa yeterli bilgi bulunmadığını söyle ve tahmin etme.
Türkçe, açık ve kısa cevap ver; kaynakları [1], [2] biçiminde belirt."""


def fallback(sources: list[SourceResponse]) -> str:
    if not sources:
        return "Bu konuda şirket dokümanlarında yeterli bilgi bulamadım."
    return f"{sources[0].content}\n\nKaynak: {sources[0].document_name}"


def answer(question: str, sources: list[SourceResponse], history: list[dict], system_prompt: str | None) -> str:
    if not sources or not HF_TOKEN:
        return fallback(sources)
    context = "\n\n".join(
        f"[{index}] {source.document_name}\n{source.content}"
        for index, source in enumerate(sources, 1)
    )
    try:
        response = InferenceClient(
            provider=HF_LLM_PROVIDER, api_key=HF_TOKEN, timeout=HF_TIMEOUT_SECONDS
        ).chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": f"Soru: {question}\n\nDokümanlar:\n{context}"},
            ],
            temperature=0.1,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip() or fallback(sources)
    except Exception:
        logger.exception("LLM yanıtı üretilemedi; kaynak özeti döndürülüyor.")
        return fallback(sources)
