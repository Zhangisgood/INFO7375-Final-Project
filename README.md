# StudyAI — Smart Flashcard Generator with RL-Optimized Review Scheduling

Final project for **INFO 7375 — Prompt Engineering for Generative AI**  
Northeastern University · April 2026  
**Team:** Mridula Mahendran · Junyi Zhang

---

## What It Does

Given any study material — a pasted text, uploaded PDF, or YouTube video URL — StudyAI:

1. Extracts and preprocesses the raw text
2. Generates structured flashcards with difficulty ratings via a prompted LLM (Groq / LLaMA 3.3-70b)
3. Indexes cards and source document chunks into a vector database (ChromaDB)
4. Presents cards adaptively using Q-Learning to select which card to show next
5. Schedules the next review of each card using a LinUCB Contextual Bandit
6. Provides a document-scoped Q&A chat backed by semantic retrieval (RAG)
7. Offers summary note generation and a multiple-choice quiz for retention testing

The system improves with use — as you answer more cards, the RL agents accumulate a better policy for your individual learning profile.

---

## Reinforcement Learning Components

### Algorithm 1: Q-Learning (Card Selection)

Decides **which card to show next** based on the user's current state.

| Parameter | Value |
|-----------|-------|
| Learning rate (α) | 0.1 |
| Discount factor (γ) | 0.9 |
| Initial epsilon (ε) | 0.4 |
| Epsilon decay | 0.99 per update |
| Epsilon floor | 0.05 |

**State space** (3 dimensions → 27 possible states):

| Dimension | Values | Derivation |
|-----------|--------|------------|
| card_difficulty | 1, 2, 3 | Card metadata field |
| user_accuracy_level | 0 (<40%), 1 (40–70%), 2 (>70%) | Rolling last-10 answers |
| time_gap_level | 0 (<1 min), 1 (1 min–1 hr), 2 (>1 hr) | Seconds since last answer |

**Reward:** +1.0 for correct answer, −1.0 for wrong answer

### Algorithm 2: LinUCB Contextual Bandit (Review Interval)

Decides **when to show a card again** after it has been answered.

**Context vector (3-dimensional):**

| Feature | Formula |
|---------|---------|
| accuracy_rate | times_correct / max(times_shown, 1) |
| norm_difficulty | difficulty / 3.0 |
| norm_times_shown | min(times_shown / 20.0, 1.0) |

**Action space:** 1 min · 10 min · 1 hour · 1 day · 3 days  
**Exploration coefficient (α):** 1.0

---

## System Architecture

```
Streamlit Web Interface (ui/app.py)
Dashboard | Flashcards | Quiz | Ask | Summary

Study material (Text / PDF / YouTube)
        ↓
  Input Processor
  PyMuPDF · youtube-transcript-api
        ↓
LLM Flashcard Generator (tools/generator.py)
  Groq API · LLaMA 3.3-70b
        ↓
FlashcardAgent Orchestrator (agents/flashcard_agent.py)
    ↙                    ↘
Q-Learning             LinUCB Bandit
Card Selector          Interval Scheduler
        ↓
Vector Store (tools/rag.py)
  FlashcardRAG (related topics)
  DocumentRAG  (Ask tab Q&A retrieval)
        ↓
  User Feedback Loop
  'I Got It' → +1.0   'Needs Review' → −1.0
```

---

## RAG Implementation

**FlashcardRAG** — each card's `question + answer` text is embedded in ChromaDB. When a card is shown, the top-4 nearest neighbours are retrieved to power the Related Topics panel.

**DocumentRAG** — the full source document is chunked into 500-character windows with 100-character overlap and indexed. At query time, the 5 most semantically relevant chunks are retrieved and injected into the Ask tab's system prompt, enabling accurate Q&A over documents of any length.

---

## Experiment Results

Three synthetic user profiles were simulated for 100 rounds each, comparing the RL system (Q-Learning card selection + LinUCB interval scheduling) against a random baseline (random card order + fixed intervals).

| User Type | RL Final Accuracy | Baseline Final Accuracy | Delta |
|-----------|:-----------------:|:-----------------------:|:-----:|
| Fast Learner | 100% | 90% | +10% |
| Normal Student | 85% | 85% | Matched |
| Slow Learner | 60% | 60% | Matched |

**Key findings:**
- Fast Learner reaches 100% ~15 rounds earlier than baseline due to smarter card ordering
- Normal Student shows lower variance — Q-Learning stops over-presenting already-mastered cards
- Slow Learner plateaus at 60% regardless of scheduling — the bottleneck is comprehension, not scheduling

By round 60, ε < 0.1, meaning the agent exploits its learned policy more than 90% of the time.

---

## Project Structure

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

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | LLaMA 3.3-70b via Groq API |
| Vector DB | ChromaDB |
| Embeddings | all-MiniLM-L6-v2 (via ChromaDB default) |
| Web UI | Streamlit |
| RL algorithms | NumPy — custom Q-Learning and LinUCB |
| PDF extraction | PyMuPDF |
| Transcript | youtube-transcript-api |
| Visualization | Altair + Matplotlib |

---

## Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/Zhangisgood/INFO7375-Final-Project.git
cd INFO7375-Final-Project
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate    # macOS / Linux
venv\Scripts\activate       # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free Groq API key at [console.groq.com](https://console.groq.com).

### 5. Launch the app
```bash
streamlit run ui/app.py
```

### 6. Run experiments (optional)
```bash
python simulation/experiment.py   # generates experiment_results.json
python evaluation/visualizer.py   # renders charts into results/
```

---

## Deployment

The app can be deployed for free on [Streamlit Community Cloud](https://share.streamlit.io):

1. Push the repo to GitHub
2. Go to share.streamlit.io → New app → select repo → set main file to `ui/app.py`
3. Under Advanced settings → Secrets, add:
   ```toml
   GROQ_API_KEY = "your_key_here"
   ```
4. Click Deploy

---

## Team

| Member | Responsibilities |
|--------|-----------------|
| Mridula Mahendran | Tools (generator, RAG, input processor), Streamlit UI, CSS theme, README |
| Junyi Zhang | RL core (Q-Learning, LinUCB), FlashcardAgent orchestrator, simulation, experiments, visualizer |
