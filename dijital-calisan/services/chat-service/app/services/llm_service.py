import logging

from huggingface_hub import InferenceClient

from app.config import HF_LLM_PROVIDER, HF_TIMEOUT_SECONDS, HF_TOKEN, LLM_MAX_TOKENS, LLM_MODEL
from app.schemas.chat_schema import SourceResponse

logger = logging.getLogger("officeiq.chat")

SYSTEM_PROMPT = """Sen OfficeIQ kurumsal bilgi asistanısın. Görevin şirket çalışanlarının sorularını yalnızca sağlanan doküman parçalarına dayanarak yanıtlamak.

KURALLAR:
- Yalnızca verilen doküman parçalarındaki bilgileri kullan, tahmin etme.
- Cevabı net, anlaşılır ve doğrudan yaz. Gereksiz giriş cümlesi kullanma ("Tabii ki", "Elbette" gibi).
- Her önemli bilgiyi hangi kaynaktan aldığını [1], [2] şeklinde belirt.
- Eğer sorunun cevabı dokümanlarda yoksa: "Bu konuda şirket dokümanlarında yeterli bilgi bulunamadı." de ve tahmin etme.
- Türkçe yaz. Madde madde açıkla, gerektiğinde liste kullan.
- Cevabı 3-5 cümleyle sınırla, çok uzun yazma.

ÖRNEK YAPI:
Yıllık izin hakkı [1] numaralı dokümana göre 14 iş günüdür. İzin kullanmak için en az 3 gün önceden yöneticiye bildirim yapılması gerekmektedir [1]."""


def fallback(sources: list[SourceResponse]) -> str:
    if not sources:
        return "Bu konuda şirket dokümanlarında yeterli bilgi bulamadım."
    return f"{sources[0].content}\n\nKaynak: {sources[0].document_name}"


def answer(question: str, sources: list[SourceResponse], history: list[dict], system_prompt: str | None) -> str:
    if not sources or not HF_TOKEN:
        return fallback(sources)
    context = "\n\n".join(
        f"[{index}] Kaynak: {source.document_name}\n{source.content}"
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
            temperature=0.05,
            max_tokens=LLM_MAX_TOKENS,
        )
        return response.choices[0].message.content.strip() or fallback(sources)
    except Exception:
        logger.exception("LLM yanıtı üretilemedi; kaynak özeti döndürülüyor.")
        return fallback(sources)
