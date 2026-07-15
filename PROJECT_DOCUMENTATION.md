# StudyAI — Technical Documentation

**Course:** INFO 7375 — Prompt Engineering for Generative AI  
**Institution:** Northeastern University  
**Team:** Mridula Mahendran · Junyi Zhang  
**Date:** April 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Core Components](#3-core-components)
4. [Implementation Details](#4-implementation-details)
5. [Performance Metrics and Experimental Results](#5-performance-metrics-and-experimental-results)
6. [Challenges and Solutions](#6-challenges-and-solutions)
7. [Future Improvements](#7-future-improvements)
8. [Ethical Considerations](#8-ethical-considerations)
9. [Appendix A — Repository Structure](#appendix-a--repository-structure)
10. [Appendix B — Setup Instructions](#appendix-b--setup-instructions)

---

## 1 Project Overview

### 1.1 Motivation

Spaced repetition is one of the most empirically validated techniques in cognitive science for long-term memory retention. Tools like Anki have demonstrated its effectiveness, but they rely entirely on manually created cards and fixed scheduling algorithms (typically a variant of SM-2). Two problems remain unsolved by existing tools:

- **Card creation is a bottleneck.** Writing good flashcards from study material takes nearly as long as studying the material itself.
- **Scheduling is not personalized.** Fixed algorithms apply the same interval multipliers to every user and every card regardless of individual learning patterns.

StudyAI addresses both problems by combining Large Language Model (LLM)-powered card generation with two custom Reinforcement Learning algorithms that learn individual review schedules from real-time feedback.

### 1.2 What the System Does

Given any study material — a pasted article, uploaded PDF, or YouTube video URL — the system:

- Extracts and preprocesses the raw text
- Generates structured flashcards with difficulty ratings via a prompted LLM (Groq / LLaMA 3.3-70b)
- Indexes cards and source document chunks into a vector database (ChromaDB)
- Presents cards adaptively, using Q-Learning to select which card to show
- Schedules the next review of each card using a Contextual Bandit (LinUCB) that learns the optimal interval
- Provides a document-scoped Q&A chat backed by semantic retrieval
- Offers summary note generation and a multiple-choice quiz for retention testing

The system improves with use: as the user answers more cards, the RL agents accumulate better policies for that specific user's learning profile.

---

## 2 System Architecture

### 2.1 High-Level Diagram

```
Streamlit Web Interface (ui/app.py)
Dashboard | Flashcards | Quiz | Ask | Summary

Study material (Text / PDF / YouTube)
        ↓
  Input Processor
  PyMuPDF · youtube-transcript-api
        ↓ Cleaned text
LLM Flashcard Generator (tools/generator.py)
  Groq API · LLaMA 3.3-70b · structured prompt
        ↓
FlashcardAgent Orchestrator (agents/flashcard_agent.py)
    ↙                    ↘
Q-Learning             LinUCB Bandit
Card Selector          Interval Scheduler
        ↓
Vector Store (tools/rag.py)
  FlashcardRAG (related topics)   DocumentRAG (Q&A retrieval)
        ↓
  User Feedback Loop
  'I Got It' → reward +1.0   'Needs Review' → reward −1.0
```

### 2.2 Data Flow Summary

| Stage | Input | Output | Technology |
|-------|-------|--------|------------|
| Text extraction | PDF / YouTube URL / paste | Plain text | PyMuPDF, youtube-transcript-api |
| Card generation | Text (≤8,000 chars) | JSON flashcard array | Groq API / LLaMA 3.3-70b |
| Card indexing | Flashcard list | Embeddings in ChromaDB | ChromaDB (all-MiniLM-L6-v2) |
| Document indexing | Full source text | 500-char chunks in ChromaDB | ChromaDB |
| Card selection | Due cards + user stats | Next card to show | Q-Learning |
| Interval scheduling | Card context vector | Review interval | LinUCB Bandit |
| Document Q&A | User query + retrieved chunks | Streamed answer | Groq API (streaming) |

---

## 3 Core Components

### 3.1 Prompt Engineering

The system implements structured prompt engineering in three distinct contexts:

#### Flashcard Generation Prompt

The generator prompt enforces strict JSON output with a defined schema. LLM outputs are non-deterministic, so the prompt includes an explicit output contract, a required schema with typed fields (`question`, `answer`, `difficulty`), a prohibition on markdown or code fences, and a retry layer with a stronger constraint if the first attempt produces malformed JSON.

```
You are a flashcard generator. Given the following text,
generate exactly N flashcards.
Return ONLY a JSON array. No explanation, no markdown, no code blocks. Just the raw JSON array.
Each flashcard must have exactly these fields:
- "question": a clear question string
- "answer": a concise answer string
- "difficulty": an integer 1, 2, or 3 (1=easy, 2=medium, 3=hard)
```

#### Document-Scoped Chat Prompt

The Ask tab uses a system prompt that constrains the model to the loaded document, preventing hallucination of information not present in the source material — important for accurate studying.

```
You are a focused study assistant. Your ONLY job is to
answer questions based on the document content provided below.
Answer ONLY questions directly relevant to this document.
Never use outside knowledge.
```

#### Summary Generation Prompts

Three style-specific prompts are used:
- **Detailed prose** — Markdown headings and bullets, 'End with Key Takeaways'
- **Bullet points** — valid markdown lists, organized into concise sections
- **ELI5** — Simple, beginner-friendly language, easy analogies, no jargon, ends with 'Main Ideas'

---

### 3.2 Retrieval-Augmented Generation (RAG)

#### FlashcardRAG — Semantic Card Similarity

Each flashcard's combined `question + answer` text is embedded and stored in ChromaDB. When a card is displayed, ChromaDB is queried for the top-n nearest neighbours using the default L2 distance metric. Results are returned directly with no distance threshold filtering — all top-n results are displayed. This powers the **Related Topics** panel.

```python
def retrieve_similar(self, query: str, n: int = 4) -> list:
    count = self.collection.count()
    if count == 0:
        return []
    n = min(n, count)
    results = self.collection.query(query_texts=[query], n_results=n)
    if not results or not results["metadatas"]:
        return []
    return results["metadatas"][0]
```

#### DocumentRAG — Full-Document Q&A Retrieval

The source document is chunked into 500-character windows with 100-character overlap to preserve context across chunk boundaries. All chunks are indexed. At query time, the 5 most relevant chunks are retrieved and injected into the Ask tab's system prompt.

This is a significant improvement over naive text truncation: a 50,000-character document that would otherwise be 80% invisible is now fully searchable. The model sees only the fragments relevant to the specific question asked.

#### Chunking Strategy

```
Chunk 1: chars    0–500
Chunk 2: chars  400–900   (100-char overlap with Chunk 1)
Chunk 3: chars  800–1300
...
```

**Note:** Chunking is purely character-based (`text[start:end]`). There is no whitespace boundary detection; chunks may split mid-word in edge cases.

---

### 3.3 Reinforcement Learning — Q-Learning (Card Selection)

**Algorithm:** Tabular Q-Learning with ε-greedy exploration.  
**Purpose:** Decide *which* card to show next.

#### State Space (3-dimensional tuple)

| Dimension | Values | Derivation |
|-----------|--------|------------|
| card_difficulty | 1, 2, 3 | Card metadata field |
| user_accuracy_level | 0 (<40%), 1 (40–70%), 2 (>70%) | Rolling last-10 answers |
| time_gap_level | 0 (<1 min), 1 (1 min–1 hr), 2 (>1 hr) | Seconds since last answer |

The 3×3×3 = 27 possible states are discovered lazily; the Q-table is a dictionary of `{state: {card_id: q_value}}`.

#### Update Rule

```
Q(s, a) ← Q(s, a) + α × [r + γ × max_a' Q(s', a') − Q(s, a)]
```

**Parameters:** α = 0.1 (learning rate), γ = 0.9 (discount factor).  
**Exploration:** ε starts at 0.4, decays by factor 0.99 per update, floored at 0.05.

---

### 3.4 Reinforcement Learning — LinUCB (Interval Scheduling)

**Algorithm:** Linear Upper Confidence Bound (LinUCB).  
**Purpose:** Decide *when* to show a card again.

#### Context Vector (3-dimensional)

| Feature | Formula |
|---------|---------|
| accuracy_rate | `times_correct / max(times_shown, 1)` |
| norm_difficulty | `difficulty / 3.0` |
| norm_times_shown | `min(times_shown / 20.0, 1.0)` |

**Action Space:** Five review intervals — 1 min, 10 min, 1 hour, 1 day, 3 days.

#### UCB Selection Formula

```
UCB(i) = θᵢᵀ · x + α · √(xᵀ · Aᵢ⁻¹ · x)
```

Where θᵢ = Aᵢ⁻¹ · bᵢ is the estimated reward coefficient vector for action i, and the second term is an exploration bonus scaled by α = 1.0.

---

## 4 Implementation Details

### 4.1 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| LLM | LLaMA 3.3-70b via Groq API | Card generation, Q&A, summaries |
| Vector DB | ChromaDB | Flashcard and document embeddings |
| Embeddings | all-MiniLM-L6-v2 | Sentence-level semantic vectors |
| Web UI | Streamlit | Interactive application interface |
| RL algorithms | NumPy — custom Q-Learning and LinUCB | Adaptive card selection and scheduling |
| PDF extraction | PyMuPDF | Page-by-page text extraction |
| Transcript | youtube-transcript-api | YouTube closed-caption fetch |
| Visualization | Altair + Matplotlib | Analytics charts |

### 4.2 Agent Architecture

`FlashcardAgent` is the central orchestrator. It owns: the card list and per-card due times, a `QLearningCardSelector` instance, an `IntervalBandit` instance, and a `FlashcardRAG` instance.

The three-step loop on every user answer:

```python
# 1. Update card statistics
card["times_shown"] += 1
if is_correct:
    card["times_correct"] += 1

# 2. Q-Learning update (which card was good to show)
self.selector.update(card, user_stats, reward, next_card, next_user_stats)

# 3. Bandit update (was this interval appropriate)
action, interval = self.bandit.select_interval(card)
self.due_times[card['id']] = now + interval * 60
self.bandit.update(action, card, reward)
```

### 4.3 Session State Management

Streamlit's session state is used as the single source of truth for all runtime data.

| Key | Type | Purpose |
|-----|------|---------|
| agent | FlashcardAgent | All RL state, cards, due times |
| doc_rag | DocumentRAG | Source document index |
| extracted_text | str | Current source material |
| accuracy_history | List[int] | Per-answer 0/1 history for charts |
| chat_history | List[dict] | Conversation turns for Ask tab |
| quiz_questions | List[dict] | Generated MCQ questions |

### 4.4 Streamlit Application Structure

| Tab | Core Feature | Key Interaction |
|-----|-------------|----------------|
| Dashboard | Session analytics | Accuracy trend, difficulty breakdown, interval histogram |
| Flashcards | Adaptive review | Get Next Card → Reveal → Grade |
| Quiz | MCQ retention test | 5–10 auto-generated multiple-choice questions |
| Ask | Document Q&A | Streaming chat backed by DocumentRAG retrieval |
| Summary | LLM note generation | Three styles: prose, bullets, ELI5 |

---

## 5 Performance Metrics and Experimental Results

### 5.1 Experiment Setup

To evaluate the RL system's effectiveness, a simulation framework was built with three synthetic user profiles. Each user type is modelled as a **linear stepwise improvement** over time: the probability of answering a card correctly increases by a fixed percentage every 10 answers, starting from a difficulty-based baseline, capped at 95%.

| User Type | Improvement Rate | Base Accuracy (by difficulty) |
|-----------|:-----------------:|-------------------------------|
| Fast Learner | +8% per 10 answers | Easy 70%, Medium 50%, Hard 30% |
| Normal Student | +5% per 10 answers | Easy 70%, Medium 50%, Hard 30% |
| Slow Learner | +2% per 10 answers | Easy 70%, Medium 50%, Hard 30% |

Answer probability formula:

```
prob = min(base_accuracy[difficulty] + (total_answered // 10) × improvement_rate, 0.95)
```

Each user type was tested for 100 rounds against the RL system (Q-Learning card selection + LinUCB interval scheduling) and a **baseline** (random card selection with no RL, no adaptive scheduling).

### 5.2 Accuracy Results

| User Type | RL Final Accuracy | Baseline Final Accuracy | Delta |
|-----------|:-----------------:|:-----------------------:|:-----:|
| Fast Learner | 100% | 90% | +10% |
| Normal Student | 85% | 85% | Matched |
| Slow Learner | 60% | 60% | Matched |

*Accuracy is measured as the moving average over the last 20 answers.*

### 5.3 Learning Curve Characteristics

**Fast Learner**  
Accuracy rises steadily and reaches 100% by approximately round 85. The RL system reaches ceiling performance approximately 15 rounds earlier than the baseline due to smarter card ordering — the Q-Learning agent prioritises harder, undermastered cards.

**Normal Student**  
Both systems converge to ~85% accuracy, but the RL system shows lower variance — the moving average is smoother because the Q-Learning agent stops over-presenting already-mastered cards.

**Slow Learner**  
Both systems plateau at ~60%. This represents the limit of what scheduling optimization can achieve when underlying comprehension is the bottleneck — the right intervention here is content simplification, not better scheduling.

### 5.4 Epsilon Decay

```
εₙ = max(0.05, 0.4 × 0.99ⁿ)
```

By round 60, ε < 0.1, meaning the agent is exploiting its learned policy more than 90% of the time.

### 5.5 Bandit Interval Distribution

In a typical user session, the LinUCB bandit converges toward longer intervals for well-mastered easy cards and shorter intervals for hard or frequently-missed cards, consistent with the theoretical behaviour of the spaced repetition curve.

### 5.6 RAG Quality

The DocumentRAG chunking strategy produces approximately 1 chunk per 400 characters of net text (due to 100-char overlap). For a typical 2,000-word article (~12,000 characters), this yields approximately 30 chunks, of which 5 are retrieved per query — covering roughly the most semantically relevant 17% of the document for the specific question asked.

---

## 6 Challenges and Solutions

### 6.1 Structured LLM Output Reliability

**Challenge**  
LLMs frequently wrap JSON in markdown code fences, add explanatory prose before the array, or return incomplete arrays. In early testing, approximately 15% of generation attempts produced JSON parse errors.

**Solution**  
A two-stage generation pipeline was implemented. The first attempt uses a standard structured prompt. If `json.loads()` raises an exception, a retry is issued with a stronger constraint prompt. A code-fence stripping step handles the remaining edge case:

```python
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
```

### 6.2 Q-Table State Space Design

**Challenge**  
Designing a state space compact enough to be learnable within a typical session (10–50 card answers) but expressive enough to capture meaningful differences between learning situations.

**Solution**  
All state dimensions were discretized into 3 bins each, producing a 27-state space. This ensures multiple visits to each state within a session. The time dimension uses human-meaningful boundaries (1 minute, 1 hour) that reflect genuine changes in memory consolidation windows.

### 6.3 ChromaDB Collection Lifecycle

**Challenge**  
ChromaDB's in-memory client raises `InvalidArgumentError` when `n_results` exceeds the number of indexed documents. This caused crashes with small study sets (< 4 cards).

**Solution**  
All `retrieve_similar()` calls now clamp `n` to `min(n, collection.count())` before querying. The `DocumentRAG.add_document()` method explicitly deletes and recreates the collection before indexing to prevent stale data:

```python
def add_document(self, text: str, chunk_size: int = 500, overlap: int = 100) -> int:
    self._clear_collection()
    ...
```

### 6.4 Bandit Counts Metric

**Challenge**  
The initial implementation tracked interval usage by summing `b[i]` vectors (LinUCB reward-weighted feature vectors), producing nonsensical floating-point values that could be negative.

**Solution**  
A dedicated `selection_counts` integer array was added to `IntervalBandit`, incremented once per `select_interval()` call, providing an exact non-negative count:

```python
self.selection_counts = np.zeros(self.n_actions, dtype=int)
...
self.selection_counts[action] += 1
```

### 6.5 Session State Consistency

**Challenge**  
Streamlit's execution model re-runs the entire script on every user interaction. Stale references led to the Ask tab showing conversations from a previous document, and quiz state persisting across new study sets.

**Solution**  
"Generate Study Set" now explicitly resets `chat_history`, `related_cache_for_card`, `related_cache_items`, and `quiz_state`. Text-loading handlers (Text / PDF / YouTube) also clear `chat_history` whenever new source material is committed.

---

## 7 Future Improvements

### 7.1 Persistent Cross-Session Learning

Currently, the `QLearningCardSelector` has `save()` and `load()` methods to persist the Q-table to `data/q_table.json`, but this feature is not wired into the Streamlit UI. A "Save Progress" button and per-user Q-table storage would allow the RL agent to accumulate knowledge across multiple study sessions.

### 7.2 Fine-Tuning the Flashcard Generator

The current system relies on zero-shot prompting. A fine-tuned model on a corpus of high-quality human-written flashcards (e.g., Anki community decks) would produce more concise, pedagogically appropriate questions.

### 7.3 Richer State Representation

The Q-Learning state currently captures three discrete dimensions. A more expressive state could include forgetting curve estimates, consecutive correct answer counts, and card similarity features. A Deep Q-Network (DQN) would enable this without sparsity problems.

### 7.4 Multi-User Support

The current architecture stores all state in Streamlit session state. A proper multi-user system would require a backend database, user authentication, and per-user model checkpoints.

### 7.5 Active Learning for Card Generation

An active learning approach could identify which concepts the user is struggling with and generate additional cards specifically targeting those gaps, rather than uniformly sampling from the source.

### 7.6 Multimodal Input

Extending the input processor to handle image-based PDFs (via OCR), audio lectures (via ASR), or handwritten notes would make the system practical for a wider range of study scenarios.

---

## 8 Ethical Considerations

### 8.1 Academic Integrity

An AI flashcard generator could be misused as a shortcut that replaces engagement with course material rather than augmenting it. The system is designed as a study aid — it generates cards from material the user provides, so the user must still read and understand the source text. The Ask tab is constrained to answer only questions about the loaded document. However, there is no technical enforcement preventing a student from loading another student's notes or using AI-generated summaries without engaging with the primary source.

### 8.2 LLM Hallucination and Factual Accuracy

LLMs occasionally generate plausible-sounding but incorrect information. Flashcards generated from a source text are generally grounded, but edge cases exist. Mitigation measures include grounding prompts, the Ask tab's system prompt forbidding outside knowledge, and encouraging users to review generated cards before trusting them.

### 8.3 Bias in Generated Content

The underlying LLaMA 3.3 model carries the biases of its training corpus. Flashcards generated from social-science or humanities content may reflect cultural, political, or linguistic biases. The difficulty classifier may also be calibrated differently for specialized domains. Users should critically review generated content.

### 8.4 Privacy

The system sends user-provided text to the Groq API for processing. Users should be aware that text content is transmitted to Groq's servers, subject to Groq's privacy and data retention policies. Sensitive or confidential documents should not be loaded into the system. The system does not itself log or transmit user data beyond the current session.

### 8.5 Accessibility

The current UI is text-only and requires manual interaction. Users with visual impairments, motor disabilities, or dyslexia are not well-served. Future work should consider screen-reader compatibility, keyboard-only navigation, and adjustable font sizes.

### 8.6 Over-Reliance on AI-Generated Feedback

The RL reward signal is based entirely on self-reported user answers. A user could mark all answers as correct regardless of actual recall, undermining the adaptive scheduling. More robust assessment — such as typing an answer before revealing it, or timed evaluation — would produce a more honest signal.

---

## Appendix A — Repository Structure

```
INFO7375-Final-Project/
├── agents/
│   ├── flashcard_agent.py      # Central orchestrator (RL loop, due times, stats)
│   └── review_agent.py         # Priority scoring utilities
├── rl/
│   ├── q_learning.py           # Tabular Q-Learning card selector
│   └── bandit.py               # LinUCB contextual bandit interval scheduler
├── tools/
│   ├── generator.py            # LLM flashcard generation via Groq
│   ├── rag.py                  # FlashcardRAG + DocumentRAG (ChromaDB)
│   └── input_processor.py      # PDF and YouTube text extraction
├── simulation/
│   ├── user_simulator.py       # Parametric synthetic user models
│   └── experiment.py           # RL vs baseline experiment runner
├── evaluation/
│   └── visualizer.py           # Matplotlib learning curve charts
├── ui/
│   ├── app.py                  # Streamlit application
│   └── styles.py               # Custom CSS theme
├── data/
│   ├── experiment_results.json
│   ├── cards.json
│   └── q_table.json
├── results/
│   ├── learning_curves.png
│   ├── epsilon_decay.png
│   └── final_comparison.png
├── requirements.txt
└── .env                        # Not committed — add your GROQ_API_KEY here
```

---

## Appendix B — Setup Instructions

### Prerequisites

- Python 3.10 or later (tested on Python 3.13.3)
- A free Groq API key from [console.groq.com](https://console.groq.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Zhangisgood/INFO7375-Final-Project.git
cd INFO7375-Final-Project

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate    # macOS / Linux
venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Create a .env file in the project root:
# GROQ_API_KEY=your_key_here

# 5. Launch the application
streamlit run ui/app.py
```

### Running Experiments

```bash
# Generate 100-round RL vs baseline results
python simulation/experiment.py

# Render learning curve charts into results/
python evaluation/visualizer.py
```

### Deployment on Streamlit Community Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select repo → set main file to `ui/app.py`
3. Under **Advanced settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
4. Click **Deploy** — dependencies install automatically from `requirements.txt`
