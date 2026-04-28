import os
import re
from pathlib import Path

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
TOP_K = 3
FALLBACK_MESSAGE = "Care insight unavailable right now."
MODEL_NAME = "gemini-1.5-flash"


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


def _load_knowledge_chunks(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    if not knowledge_dir.exists():
        print(f"[RAG] Knowledge directory missing: {knowledge_dir}")
        return chunks

    for md_file in sorted(knowledge_dir.glob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[RAG] Failed to read {md_file.name}: {exc}")
            continue

        paragraph_chunks = [part.strip() for part in content.split("\n\n") if part.strip()]
        for idx, paragraph in enumerate(paragraph_chunks):
            chunks.append(
                {
                    "source": md_file.name,
                    "chunk_id": f"{md_file.stem}-{idx}",
                    "text": paragraph,
                }
            )

    print(f"[RAG] Loaded {len(chunks)} chunks from {knowledge_dir}")
    return chunks


KNOWLEDGE_CHUNKS = _load_knowledge_chunks()


def _retrieve_chunks(query: str, chunks: list[dict[str, str]], top_k: int = TOP_K) -> list[dict[str, str]]:
    query_tokens = _tokenize(query)
    if not query_tokens or not chunks:
        return []

    scored_chunks: list[tuple[int, dict[str, str]]] = []
    for chunk in chunks:
        overlap_score = len(query_tokens.intersection(_tokenize(chunk["text"])))
        if overlap_score > 0:
            scored_chunks.append((overlap_score, chunk))

    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored_chunks[:top_k]]


def get_care_insight(pet_name: str, health_conditions: list[str], schedule_context: str) -> str:
    conditions_text = ", ".join(health_conditions) if health_conditions else "general wellness"
    query = (
        f"pet name {pet_name} health conditions {conditions_text} "
        f"schedule context {schedule_context}"
    )

    retrieved = _retrieve_chunks(query=query, chunks=KNOWLEDGE_CHUNKS, top_k=TOP_K)
    print("[RAG] Retrieved chunks:")
    if retrieved:
        for i, chunk in enumerate(retrieved, start=1):
            preview = chunk["text"].replace("\n", " ")[:120]
            print(f"  {i}. [{chunk['source']} | {chunk['chunk_id']}] {preview}...")
    else:
        print("  (none)")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[RAG] Gemini API call failed: GEMINI_API_KEY not set")
        return FALLBACK_MESSAGE

    context_blocks = "\n\n---\n\n".join(chunk["text"] for chunk in retrieved) or "No relevant context retrieved."
    prompt = f"""
You are PawPal+, a helpful pet care assistant.
Use the provided context to generate a personalized care insight.

Pet name: {pet_name}
Health conditions: {conditions_text}
Schedule context: {schedule_context}

Retrieved knowledge context:
{context_blocks}

Provide a short, practical, and safe care insight for this pet owner.
"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        insight = (response.text or "").strip()
        if not insight:
            print("[RAG] Gemini API call failed: empty response")
            return FALLBACK_MESSAGE

        print("[RAG] Gemini API call succeeded")
        return insight
    except Exception as exc:
        print(f"[RAG] Gemini API call failed: {exc}")
        return FALLBACK_MESSAGE
