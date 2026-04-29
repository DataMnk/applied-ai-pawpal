import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

KNOWLEDGE_DIR = Path(__file__).resolve().parent / "knowledge"
TOP_K = 3
FALLBACK_MESSAGE = "Care insight unavailable right now."
MODEL_NAME = "gpt-4o-mini"


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


def get_care_insight(
    pet_name: str, health_conditions: list[str], schedule_context: str
) -> tuple[str, list[str]]:
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

    sources = list(dict.fromkeys(chunk["source"] for chunk in retrieved))

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[RAG] OpenAI API call failed: OPENAI_API_KEY not set")
        return FALLBACK_MESSAGE, sources

    context_blocks = "\n\n---\n\n".join(chunk["text"] for chunk in retrieved) or "No relevant context retrieved."
    prompt = f"""
You are PawPal+, a helpful pet care assistant.
Use the provided context to generate a personalized care insight.
Match the PawPal+ voice: practical, calm, and safety-first.
Follow the same sectioned output style shown in the examples.

Example 1
Input:
Pet name: Tobi
Health conditions: hip dysplasia
Schedule context: morning walk at 07:00

Output:
Morning:
- Keep the walk short and gentle (10-15 minutes) on soft ground.
- Do a 3-5 minute warm-up at a slow pace before stairs or hills.

Midday:
- Encourage low-impact movement and avoid jumping onto furniture.
- Offer a supportive rest area to reduce hip strain between activities.

Evening:
- Use a calm leash walk and watch for limping or stiffness after activity.
- If discomfort increases, reduce intensity and contact the vet for plan adjustments.

Example 2
Input:
Pet name: Luna
Health conditions: diabetes
Schedule context: insulin injection at 08:00

Output:
Insulin Schedule:
- Give insulin at consistent times each day, paired with meals.
- Record dose time and appetite to spot routine changes early.

Monitoring:
- Track thirst, urination, appetite, and energy for daily trends.
- If weakness, vomiting, or disorientation appears, contact a vet urgently.

Diet:
- Keep meal portions and carbohydrate profile consistent.
- Avoid unplanned treats that can destabilize glucose control.

Now respond for this request:
Pet name: {pet_name}
Health conditions: {conditions_text}
Schedule context: {schedule_context}

Retrieved knowledge context:
{context_blocks}

Provide a short, practical, and safe care insight for this pet owner.
"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        insight = (response.choices[0].message.content or "").strip()
        if not insight:
            print("[RAG] OpenAI API call failed: empty response")
            return FALLBACK_MESSAGE, sources

        print("[RAG] OpenAI API call succeeded")
        return insight, sources
    except Exception as exc:
        print(f"[RAG] OpenAI API call failed: {exc}")
        return FALLBACK_MESSAGE, sources


def agentic_get_care_insight(
    pet_name: str, health_conditions: list[str], schedule_context: str
) -> tuple[str, list[str]]:
    conditions_text = ", ".join(health_conditions) if health_conditions else "general wellness"
    sources: list[str] = []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[AGENT] OpenAI API call failed: OPENAI_API_KEY not set")
        return FALLBACK_MESSAGE, sources

    client = OpenAI(api_key=api_key)

    # Step 1 — Analyze
    print(f"[AGENT] Step 1 - Analyzing conditions: {conditions_text}")
    analysis_prompt = f"""
You are a veterinary care planning assistant.
Analyze the pet profile below and identify the top 2 care priorities.
Return exactly two concise bullet points and include practical focus areas.

Pet name: {pet_name}
Health conditions: {conditions_text}
Schedule context: {schedule_context}
"""
    try:
        analysis_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=300,
        )
        analysis = (analysis_response.choices[0].message.content or "").strip()
        if not analysis:
            print("[AGENT] OpenAI API call failed during analysis: empty response")
            return FALLBACK_MESSAGE, sources
    except Exception as exc:
        print(f"[AGENT] OpenAI API call failed during analysis: {exc}")
        return FALLBACK_MESSAGE, sources

    # Step 2 — Plan
    planning_query = (
        f"pet name {pet_name} health conditions {conditions_text} "
        f"schedule context {schedule_context} priorities {analysis}"
    )
    print(f"[AGENT] Step 2 - Planning retrieval query: {planning_query}")
    retrieved = _retrieve_chunks(query=planning_query, chunks=KNOWLEDGE_CHUNKS, top_k=TOP_K)
    sources = list(dict.fromkeys(chunk["source"] for chunk in retrieved))

    # Step 3 — Generate
    print(
        f"[AGENT] Step 3 - Generating insight with {len(retrieved)} chunks from "
        f"{sources if sources else 'none'}"
    )
    context_blocks = "\n\n---\n\n".join(chunk["text"] for chunk in retrieved) or "No relevant context retrieved."
    generation_prompt = f"""
You are PawPal+, a helpful pet care assistant.
Use the provided context to generate a personalized care insight.
Match the PawPal+ voice: practical, calm, and safety-first.
Follow the same sectioned output style shown in the examples.

Example 1
Input:
Pet name: Tobi
Health conditions: hip dysplasia
Schedule context: morning walk at 07:00

Output:
Morning:
- Keep the walk short and gentle (10-15 minutes) on soft ground.
- Do a 3-5 minute warm-up at a slow pace before stairs or hills.

Midday:
- Encourage low-impact movement and avoid jumping onto furniture.
- Offer a supportive rest area to reduce hip strain between activities.

Evening:
- Use a calm leash walk and watch for limping or stiffness after activity.
- If discomfort increases, reduce intensity and contact the vet for plan adjustments.

Example 2
Input:
Pet name: Luna
Health conditions: diabetes
Schedule context: insulin injection at 08:00

Output:
Insulin Schedule:
- Give insulin at consistent times each day, paired with meals.
- Record dose time and appetite to spot routine changes early.

Monitoring:
- Track thirst, urination, appetite, and energy for daily trends.
- If weakness, vomiting, or disorientation appears, contact a vet urgently.

Diet:
- Keep meal portions and carbohydrate profile consistent.
- Avoid unplanned treats that can destabilize glucose control.

Use this analysis of top care priorities:
{analysis}

Now respond for this request:
Pet name: {pet_name}
Health conditions: {conditions_text}
Schedule context: {schedule_context}

Retrieved knowledge context:
{context_blocks}

Provide a short, practical, and safe care insight for this pet owner.
"""
    try:
        generation_response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": generation_prompt}],
            max_tokens=1024,
        )
        insight = (generation_response.choices[0].message.content or "").strip()
        if not insight:
            print("[AGENT] OpenAI API call failed during generation: empty response")
            return FALLBACK_MESSAGE, sources

        print("[AGENT] OpenAI API call succeeded")
        return insight, sources
    except Exception as exc:
        print(f"[AGENT] OpenAI API call failed during generation: {exc}")
        return FALLBACK_MESSAGE, sources


def baseline_get_care_insight(
    pet_name: str, health_conditions: list[str], schedule_context: str
) -> tuple[str, list[str]]:
    conditions_text = ", ".join(health_conditions) if health_conditions else "general wellness"
    sources: list[str] = []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[RAG-BASELINE] OpenAI API call failed: OPENAI_API_KEY not set")
        return FALLBACK_MESSAGE, sources

    prompt = f"""
You are a pet care assistant.
Help with {pet_name} who has {conditions_text}.
Schedule context: {schedule_context}.
Provide a short, practical, and safe care insight for this pet owner.
"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        insight = (response.choices[0].message.content or "").strip()
        if not insight:
            print("[RAG-BASELINE] OpenAI API call failed: empty response")
            return FALLBACK_MESSAGE, sources

        print("[RAG-BASELINE] OpenAI API call succeeded")
        return insight, sources
    except Exception as exc:
        print(f"[RAG-BASELINE] OpenAI API call failed: {exc}")
        return FALLBACK_MESSAGE, sources
