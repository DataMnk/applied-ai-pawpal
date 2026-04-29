# 🐾 PawPal+ Applied AI System

**PawPal+** is a smart pet care scheduling app extended with a RAG (Retrieval-Augmented Generation) AI system. It helps busy pet owners organize daily care tasks, detect scheduling conflicts, and receive personalized AI care insights based on each pet's health conditions.

---

## 📋 Base Project

This project extends **PawPal+ (Module 2 — CodePath AI110)**. The original app was a Python + Streamlit scheduling system for pet owners. It allowed users to add pets and tasks, generate a prioritized daily schedule, detect time conflicts, and persist data to JSON. It included 24 automated pytest tests, all passing, and four optional challenges completed (next available slot, data persistence, priority sorting, custom UI theme).

The new version adds a full RAG pipeline that generates personalized veterinary care insights directly inside the app.

---

## ✨ Features

- **AI Care Insights** — After generating a schedule, the app calls the RAG engine for each pet with health conditions and displays a personalized care insight with the knowledge sources used.
- **RAG Engine** — Retrieves the top 3 relevant chunks from a veterinary knowledge base using keyword overlap scoring, then calls OpenAI to generate a structured insight.
- **Few-shot specialization** — The prompt includes 2 examples that teach the model to respond in PawPal+'s voice: practical, calm, safety-first, with Morning/Midday/Evening sections.
- **Agentic workflow** — A 3-step Analyze → Plan → Generate pipeline with observable intermediate steps in the logs.
- **Test harness** — `evaluation.py` runs 4 predefined test cases and prints a pass/fail summary with confidence scores.
- **Time-based sorting** — Tasks ordered chronologically with priority tie-breaking.
- **Conflict warnings** — Flags overlapping tasks and suggests the next available slot.
- **Data persistence** — Pets and tasks saved to `data.json` automatically.
- **Custom UI theme** — Nunito font, purple-green gradient header, priority emojis 🔴🟡🟢.

---

## 🏗️ System Architecture

```
Pet Owner
    ↓ adds pets & tasks
PawPal+ Streamlit UI (app.py)
    ↓ health_conditions + schedule context
RAG Engine (rag_engine.py)
    ↓ keyword query
Knowledge Base (knowledge/*.md — 4 veterinary docs)
    ↓ top 3 relevant chunks
OpenAI GPT-4o-mini
    ↓ care insight + sources
PawPal+ Streamlit UI → displays 🧠 AI Care Insights

evaluation.py → runs 4 test cases → 4/4 PASS, confidence 1.00
```

See `assets/system_architecture.png` for the full diagram.

**Core files:**
- `pawpal_system.py` — backend: Owner, Pet, Task, Scheduler classes
- `rag_engine.py` — RAG engine: retrieval, OpenAI call, agentic workflow, baseline
- `app.py` — Streamlit UI
- `evaluation.py` — automated test harness
- `knowledge/` — 4 veterinary markdown documents
- `assets/` — system architecture diagram and screenshots

---

## 🚀 Getting Started

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### Configure API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### Run the app

```bash
streamlit run app.py
```

### Run the CLI demo

```bash
python main.py
```

### Run the AI evaluation harness

```bash
python evaluation.py
```

---

## 💬 Sample AI Interactions

**Input 1:** Pet "Tobi", conditions: ["hip dysplasia"], schedule: morning walk at 07:00

**Output:**
```
Morning:
- Keep the walk short and gentle (10-15 minutes) on soft ground.
- Conduct a quick mobility check before heading out.

Midday:
- Offer a short potty break with minimal walking.
- Incorporate gentle stretching to keep muscles flexible.

Evening:
- Use a calm leash walk, monitoring for limping or stiffness.
- Engage in light range-of-motion play indoors.

Sources: hip_dysplasia.md, senior_pet_care.md
```

---

**Input 2:** Pet "Luna", conditions: ["diabetes"], schedule: insulin injection at 08:00

**Output:**
```
Insulin Schedule:
- Give insulin at consistent times each day, paired with meals.
- Record dose time and appetite to spot routine changes early.

Monitoring:
- Track thirst, urination, appetite, and energy for daily trends.
- If weakness or disorientation appears, contact a vet urgently.

Sources: diabetes_in_cats.md, general_pet_care.md
```

---

**Input 3:** Pet "Max", conditions: [] (no conditions — general wellness)

**Output:**
```
For Max, maintaining a consistent feeding schedule is essential
for his general wellness. With feeding at 09:00, ensure fresh
water is always available and monitor his appetite daily.

Sources: general_pet_care.md
```

---

## 🎯 Design Decisions

**Why keyword matching instead of vector embeddings?**
The knowledge base has 4 documents and 33 chunks. Keyword overlap scoring is fast, transparent, and easy to explain — which matters for a "trustworthy AI" requirement. Vector embeddings would add complexity and cost without a meaningful accuracy improvement at this scale.

**Why OpenAI instead of Gemini?**
Gemini's free tier quota was exhausted during development across multiple projects and API keys. OpenAI's `gpt-4o-mini` worked reliably on the first call and stayed within free tier limits throughout the project.

**Why few-shot prompting?**
Without examples, the model returned unstructured paragraph responses. Adding 2 examples produced consistent Morning/Midday/Evening sections with bullet points — measurably different from the baseline, as shown in `evaluation.py`.

---

## 🧪 Testing Summary

```bash
python -m pytest tests/ -v        # 24 unit tests — all passing
python evaluation.py              # AI evaluation harness
```

**Unit tests (24):** Cover all scheduling behaviors, conflict detection, data persistence, recurring tasks, and edge cases.

**AI evaluation (4 test cases):**
- Test 1: Tobi / hip dysplasia → PASS
- Test 2: Luna / diabetes → PASS
- Test 3: Max / no conditions → PASS
- Test 4: Bella / hip dysplasia + arthritis → PASS

**Result: 4/4 passing — average confidence score: 1.00**

What worked: retrieval correctly identified relevant chunks in all cases. The few-shot prompt produced structured, consistent output.

What to improve: keyword matching sometimes retrieved chunks from unrelated documents. Semantic search would fix this.

---

## 🔁 Stretch Features Completed

- ✅ **RAG Enhancement (+2)** — sources exposed in UI and evaluation output
- ✅ **Agentic Workflow (+2)** — 3-step Analyze → Plan → Generate with observable `[AGENT]` logs
- ✅ **Fine-Tuning/Specialization (+2)** — few-shot prompting produces structured output measurably different from baseline
- ✅ **Test Harness (+2)** — `evaluation.py` runs predefined cases and prints pass/fail + confidence score

---

## 🎥 Demo Walkthrough

Loom video link: [https://www.loom.com/share/6d66c3d82924481596407cc613ed4687](https://www.loom.com/share/6d66c3d82924481596407cc613ed4687)

---

## 💡 Reflection

This project taught me that a small, well-curated knowledge base with a simple retriever and a good prompt can produce genuinely useful AI output. You don't need a complex system to build something that actually helps people.

The most important lesson: human oversight in AI-assisted development is not optional. The AI suggested the deprecated Gemini library, gave us wrong model names, and generated code that looked correct but wasn't. Every suggestion needed review. The architect is always the human.
