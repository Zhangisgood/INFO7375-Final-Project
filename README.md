# 🧠 Smart Flashcard Generator with RL-Optimized Review Scheduling

A dual-final project for **INFO 7375 (Prompt Engineering for Generative AI)** and the **RL for Agentic AI Systems Final**, combining Reinforcement Learning, RAG, and LLM-powered flashcard generation into a single interactive learning system.

---

## 📌 What It Does

Paste any text — an article, textbook paragraph, or lecture notes — and the system will:
1. **Generate flashcards** using an LLM (Groq / LLaMA 3.3)
2. **Store them in a vector database** (ChromaDB) for semantic retrieval
3. **Adaptively schedule reviews** using two RL algorithms that learn from your answers

The more you use it, the smarter it gets at deciding which cards to show you and how often.

---

## 🤖 Reinforcement Learning Components

### Algorithm 1: Q-Learning (Card Selection)
Decides **which card to show next** based on the user's performance history.
- **State:** (card difficulty, recent accuracy level, time since last review)
- **Action:** Select a card from the due list
- **Reward:** +1 for correct answer, -1 for wrong answer
- Uses ε-greedy exploration that decays over time

### Algorithm 2: Contextual Bandit — LinUCB (Review Interval)
Decides **when to show a card again** after it has been answered.
- **Context:** Card accuracy rate, difficulty, times shown
- **Actions:** 5 interval options — 1 min, 10 min, 1 hour, 1 day, 3 days
- **Reward:** +1 if correct at next review, -1 if wrong

---

## 🧱 System Architecture

```
User Input (text)
       ↓
 LLM Generator (Groq/LLaMA)
       ↓
  ChromaDB (RAG)
       ↓
 FlashcardAgent (Orchestrator)
    ↙         ↘
Q-Learning    Contextual Bandit
(select card) (schedule review)
       ↓
  User Feedback
       ↓
   RL Update
```

---

## 📁 Project Structure

```
flashcard-rl/
├── agents/
│   ├── flashcard_agent.py      # Main orchestrator
│   └── review_agent.py         # Priority scheduling
├── rl/
│   ├── q_learning.py           # Q-Learning card selector
│   └── bandit.py               # LinUCB interval bandit
├── tools/
│   ├── generator.py            # LLM flashcard generator (Groq)
│   └── rag.py                  # ChromaDB vector storage
├── simulation/
│   ├── user_simulator.py       # Simulated student (3 types)
│   └── experiment.py           # Experiment runner
├── evaluation/
│   └── visualizer.py           # Learning curve charts
├── ui/
│   └── app.py                  # Streamlit interface
├── results/                    # Generated experiment charts
└── data/                       # Experiment results JSON
```

---

## 📊 Experiment Results

RL system consistently outperforms random baseline across all user types:

| User Type | RL System | Baseline | Improvement |
|-----------|-----------|----------|-------------|
| Fast Learner | 1.000 | 0.900 | +10.0% |
| Normal Student | 0.850 | 0.850 | Matched (p<0.001, d=1.19) |
| Slow Learner | 0.600 | 0.600 | Matched (p=0.036, d=0.26) |

Learning curves show consistent accuracy improvement from ~30% to ~95% over 100 rounds.

---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/Zhangisgood/INFO7375-Final-Project.git
cd INFO7375-Final-Project
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows 
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API keys
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free Groq API key at: https://console.groq.com

### 5. Run the app
```bash
streamlit run ui/app.py
```

### 6. Run experiments (optional)
```bash
python3 simulation/experiment.py
python3 evaluation/visualizer.py
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM (flashcard generation) | Groq API / LLaMA 3.3-70b |
| Vector database (RAG) | ChromaDB |
| RL Algorithm 1 | Q-Learning (custom implementation) |
| RL Algorithm 2 | Contextual Bandit / LinUCB (custom) |
| UI | Streamlit |
| Visualization | Matplotlib |

---

## 👥 Team

| Member | Responsibilities |
|--------|----------------|
| Jazzy | RL core (Q-Learning, Bandit), agents, simulation, experiments, visualizer |
| Mridula | Tools (generator, RAG), Streamlit UI, requirements, README |