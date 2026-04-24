import sys
import os
import re
import random
from html import escape as _esc

# Streamlit Cloud ships an old SQLite; swap in the newer pysqlite3-binary
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from agents.flashcard_agent import FlashcardAgent

st.set_page_config(page_title="StudyAI", layout="wide", initial_sidebar_state="expanded")

from ui.styles import load_css
st.markdown(load_css(), unsafe_allow_html=True)


def icon(name: str) -> str:
    return f'<span class="material-symbols-rounded icon">{name}</span>'


def _md_to_html(text: str) -> str:
    t = _esc(text)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(
        r'`([^`\n]+)`',
        r'<code style="background:rgba(0,0,0,.08);padding:1px 5px;border-radius:3px;font-size:.87em">\1</code>',
        t,
    )
    t = re.sub(r'(?m)^[-•*]\s+(.+)$', r'<li style="margin:.15rem 0">\1</li>', t)
    t = re.sub(r'(<li[^>]*>.*?</li>\s*)+', lambda m: f'<ul style="margin:.4rem 0;padding-left:1.3rem">{m.group(0)}</ul>', t)
    t = re.sub(r'\n{2,}', '<br><br>', t)
    t = t.replace('\n', '<br>')
    return t


_BUBBLE_BASE = (
    'border-radius:{r};padding:10px 16px;max-width:72%;'
    'font-size:.94rem;line-height:1.58;word-wrap:break-word;'
)


def _user_bubble(text: str) -> str:
    style = (
        'background:linear-gradient(135deg,#1d9097,#0f6467);color:#fff;'
        + _BUBBLE_BASE.format(r='18px 4px 18px 18px')
        + 'box-shadow:0 3px 14px rgba(14,95,100,.28);'
    )
    return (
        f'<div style="display:flex;justify-content:flex-end;margin:4px 0">'
        f'<div style="{style}">{_esc(text)}</div></div>'
    )


def _asst_bubble(text: str, streaming: bool = False) -> str:
    style = (
        'background:#ffffff;border:1px solid #c4ddd0;color:#1d2939;'
        + _BUBBLE_BASE.format(r='4px 18px 18px 18px')
        + 'box-shadow:0 2px 10px rgba(0,0,0,.07);'
    )
    cursor = '<span style="opacity:.4;margin-left:1px">▌</span>' if streaming else ''
    return (
        f'<div style="display:flex;justify-content:flex-start;margin:4px 0">'
        f'<div style="{style}">{_md_to_html(text)}{cursor}</div></div>'
    )


@st.cache_data(show_spinner=False)
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    import pymupdf
    text = ""
    with pymupdf.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()


@st.cache_data(show_spinner=False)
def extract_text_from_youtube_cached(url: str) -> str:
    from tools.input_processor import extract_text_from_youtube
    return extract_text_from_youtube(url)


@st.cache_resource
def get_groq_client():
    from groq import Groq
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def initialize_session_state() -> None:
    defaults = {
        "agent": FlashcardAgent(),
        "current_card": None,
        "show_answer": False,
        "accuracy_history": [],
        "next_interval": None,
        "all_cards_map": {},
        "extracted_text": "",
        "summary_output": None,
        "summary_style": "detailed",
        "last_feedback": None,
        "quiz_questions": [],
        "quiz_index": 0,
        "quiz_score": 0,
        "quiz_results": [],
        "quiz_count": 5,
        "related_cache_for_card": None,
        "related_cache_items": [],
        "chat_history": [],
        "pending_ai": False,
        "doc_rag": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_quiz_state() -> None:
    st.session_state.quiz_questions = []
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_results = []


def prepare_quiz_questions(cards: list, total_questions: int) -> list:
    if len(cards) < 2:
        return []

    total = min(max(total_questions, 5), 10, len(cards))
    selected_cards = random.sample(cards, total)
    questions = []

    for card in selected_cards:
        correct_answer = card["answer"]
        distractor_pool = [c["answer"] for c in cards if c["id"] != card["id"] and c["answer"] != correct_answer]
        random.shuffle(distractor_pool)
        distractors = distractor_pool[: min(3, len(distractor_pool))]
        options = [correct_answer] + distractors
        random.shuffle(options)
        questions.append({
            "card_id": card["id"],
            "question": card["question"],
            "answer": correct_answer,
            "options": options,
        })

    return questions


def render_empty_state(title: str, description: str, icon_name: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-icon">{icon(icon_name)}</div>
            <div class="empty-title">{title}</div>
            <div class="empty-copy">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


initialize_session_state()
agent = st.session_state.agent

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<div class='sidebar-brand'>{icon('school')}&nbsp;StudyAI</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>Adaptive learning powered by RL&nbsp;+&nbsp;LLM.</div>", unsafe_allow_html=True)
    st.divider()

    st.markdown(f"<div class='section-title'>{icon('ink_pen')} Study Material</div>", unsafe_allow_html=True)
    input_mode = st.radio(
        "Source",
        ["Text", "PDF", "YouTube"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if input_mode == "Text":
        with st.form("text_source_form"):
            text_input = st.text_area(
                "Paste your study material",
                value=st.session_state.extracted_text,
                height=170,
                placeholder="Paste class notes, article excerpts, or textbook sections.",
            )
            use_text = st.form_submit_button("Use Text", use_container_width=True)

        if use_text:
            if text_input.strip():
                st.session_state.extracted_text = text_input.strip()
                from tools.rag import DocumentRAG
                doc_rag = DocumentRAG()
                n_chunks = doc_rag.add_document(st.session_state.extracted_text)
                st.session_state.doc_rag = doc_rag
                st.session_state.chat_history = []
                st.success(f"Material loaded ({len(st.session_state.extracted_text):,} characters, {n_chunks} chunks indexed for Ask).")
            else:
                st.warning("Please provide text before continuing.")

    elif input_mode == "PDF":
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if st.button(
            "Extract PDF Text",
            use_container_width=True,
            disabled=uploaded_file is None,
        ):
            try:
                with st.spinner("Extracting text from PDF..."):
                    st.session_state.extracted_text = extract_text_from_pdf_bytes(uploaded_file.getvalue())
                from tools.rag import DocumentRAG
                doc_rag = DocumentRAG()
                n_chunks = doc_rag.add_document(st.session_state.extracted_text)
                st.session_state.doc_rag = doc_rag
                st.session_state.chat_history = []
                st.success(f"PDF loaded ({len(st.session_state.extracted_text):,} characters, {n_chunks} chunks indexed for Ask).")
            except Exception as e:
                st.error(f"Failed to read PDF: {e}")

    elif input_mode == "YouTube":
        with st.form("youtube_source_form"):
            yt_url = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
            load_transcript = st.form_submit_button("Load Transcript", use_container_width=True)

        if load_transcript:
            if yt_url.strip():
                try:
                    with st.spinner("Fetching transcript..."):
                        st.session_state.extracted_text = extract_text_from_youtube_cached(yt_url.strip())
                    from tools.rag import DocumentRAG
                    doc_rag = DocumentRAG()
                    n_chunks = doc_rag.add_document(st.session_state.extracted_text)
                    st.session_state.doc_rag = doc_rag
                    st.session_state.chat_history = []
                    st.success(f"Transcript loaded ({len(st.session_state.extracted_text):,} characters, {n_chunks} chunks indexed for Ask).")
                except Exception as e:
                    st.error(f"Could not load transcript: {e}")
            else:
                st.warning("Please provide a valid YouTube URL.")

    char_count = len(st.session_state.extracted_text)
    if char_count > 0:
        st.markdown(f"<div class='small-muted'>Loaded text: {char_count:,} characters</div>", unsafe_allow_html=True)
        if char_count > 8000:
            st.warning(
                f"Flashcard generation and Summary Notes use the first 8,000 of {char_count:,} characters. "
                "Ask uses the full document via semantic search."
            )

    st.divider()
    st.markdown(f"<div class='section-title'>{icon('settings')} Configurations</div>", unsafe_allow_html=True)
    n_cards = st.slider("Number of flashcards", min_value=5, max_value=20, value=10, step=1)
    st.session_state.quiz_count = st.slider(
        "Number of quizzes",
        min_value=5,
        max_value=10,
        value=min(max(st.session_state.quiz_count, 5), 10),
        step=1,
    )

    if st.button("Generate Study Set", type="primary", use_container_width=True):
        if st.session_state.extracted_text.strip():
            try:
                with st.spinner("Generating flashcards..."):
                    st.session_state.agent = FlashcardAgent()
                    agent = st.session_state.agent
                    text_to_use = st.session_state.extracted_text[:8000]
                    agent.load_text(text_to_use, n_cards)
                    st.session_state.all_cards_map = {c["id"]: c for c in agent.cards}
                    st.session_state.current_card = None
                    st.session_state.show_answer = False
                    st.session_state.accuracy_history = []
                    st.session_state.summary_output = None
                    st.session_state.last_feedback = None
                    st.session_state.related_cache_for_card = None
                    st.session_state.related_cache_items = []
                    st.session_state.chat_history = []
                    reset_quiz_state()
                if agent.cards:
                    st.success(f"Study set ready with {len(agent.cards)} flashcards.")
                else:
                    st.error("No flashcards were generated. Check your GROQ_API_KEY in the .env file.")
            except Exception as e:
                st.error(f"Generation failed: {e}")
        else:
            st.warning("Please provide study material first.")

    if st.button("Reset Session", use_container_width=True):
        st.session_state.agent = FlashcardAgent()
        st.session_state.current_card = None
        st.session_state.show_answer = False
        st.session_state.accuracy_history = []
        st.session_state.next_interval = None
        st.session_state.all_cards_map = {}
        st.session_state.extracted_text = ""
        st.session_state.summary_output = None
        st.session_state.last_feedback = None
        st.session_state.related_cache_for_card = None
        st.session_state.related_cache_items = []
        st.session_state.chat_history = []
        st.session_state.pending_ai = False
        st.session_state.doc_rag = None
        reset_quiz_state()
        agent = st.session_state.agent
        st.success("Session reset complete.")

    st.divider()
    st.markdown(f"<div class='section-title'>{icon('monitoring')} Learning Status</div>", unsafe_allow_html=True)
    stats = agent.get_stats()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats.get('epsilon', 1.0):.3f}</div>
            <div class="metric-label">Epsilon (ε)</div>
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{stats.get('q_table_size', 0)}</div>
            <div class="metric-label">Q States</div>
        </div>
        """, unsafe_allow_html=True)

    bandit_counts = stats.get("bandit_counts", {})
    if bandit_counts:
        st.markdown("<div class='small-muted'>Interval selections</div>", unsafe_allow_html=True)
        for interval, count in bandit_counts.items():
            st.markdown(f"<div class='small-muted'>{interval}: {count}</div>", unsafe_allow_html=True)


# ── Main content ──────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="app-hero">
        <div class="app-kicker">{icon('auto_awesome')} Reinforcement Learning &nbsp;·&nbsp; RAG &nbsp;·&nbsp; LLM</div>
        <h1 class="app-title">StudyAI Workspace</h1>
        <p class="app-subtitle">Generate adaptive flashcards from any source, review with spaced repetition, and test yourself — all in one place.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_dashboard, tab_flashcards, tab_quiz, tab_ask, tab_summary = st.tabs(
    ["Dashboard", "Flashcards", "Quiz", "Ask", "Summary"]
)

# ── Flashcards tab ────────────────────────────────────────────────────────────
with tab_flashcards:
    cards = agent.cards
    current_card = st.session_state.current_card

    top_metrics = st.columns(3)
    top_metrics[0].metric("Cards in Deck", len(cards))
    top_metrics[1].metric("Due Now", stats.get("cards_due", 0))
    top_metrics[2].metric("Session Accuracy", f"{stats.get('accuracy', 0.0) * 100:.0f}%")

    if st.session_state.last_feedback:
        st.success(st.session_state.last_feedback)

    col_main, col_related = st.columns([2.1, 1.1])

    with col_main:
        st.markdown(f"<div class='section-title'>{icon('style')} Smart Flashcards</div>", unsafe_allow_html=True)

        control_col1, control_col2 = st.columns([1.25, 1])
        with control_col1:
            if st.button("Get Next Card", use_container_width=True):
                next_card = agent.get_next_card()
                if next_card:
                    st.session_state.current_card = next_card
                    st.session_state.show_answer = False
                    st.session_state.next_interval = None
                else:
                    st.info("No cards are due right now. Add study material or wait for the next interval.")
        with control_col2:
            if st.button("Clear Current Card", use_container_width=True):
                st.session_state.current_card = None
                st.session_state.show_answer = False

        current_card = st.session_state.current_card
        if current_card:
            diff = current_card.get("difficulty", 1)
            diff_map = {1: ("Easy", "pill-easy"), 2: ("Medium", "pill-medium"), 3: ("Hard", "pill-hard")}
            diff_label, diff_class = diff_map.get(diff, ("Medium", "pill-medium"))

            card_position = 1
            for idx, card_obj in enumerate(cards):
                if card_obj.get("id") == current_card.get("id"):
                    card_position = idx + 1
                    break

            st.markdown(
                f"""
                <div class="flashcard-shell">
                    <div class="flashcard-meta">
                        <span class="pill {diff_class}">{diff_label}</span>
                        <span>Card {card_position} of {max(len(cards), 1)}</span>
                    </div>
                    <div class="flashcard-question">{_esc(current_card['question'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            reveal_col1, reveal_col2 = st.columns(2)
            with reveal_col1:
                if st.button("Reveal Answer", use_container_width=True):
                    st.session_state.show_answer = True
            with reveal_col2:
                if st.button("Remove Card", use_container_width=True):
                    agent.cards = [c for c in agent.cards if c["id"] != current_card["id"]]
                    if current_card["id"] in agent.due_times:
                        del agent.due_times[current_card["id"]]
                    st.session_state.all_cards_map = {c["id"]: c for c in agent.cards}
                    st.session_state.current_card = None
                    st.session_state.show_answer = False
                    st.session_state.last_feedback = "Card removed from this session."
                    st.session_state.related_cache_for_card = None
                    st.session_state.related_cache_items = []
                    reset_quiz_state()
                    st.rerun()

            if st.session_state.show_answer:
                st.markdown(
                    f"""
                    <div class="flashcard-answer">
                        <div class="answer-title">Answer</div>
                        <div>{_esc(current_card['answer'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                grade_col1, grade_col2 = st.columns(2)
                with grade_col1:
                    if st.button("I Got It", use_container_width=True):
                        interval = agent.submit_answer(current_card, True)
                        st.session_state.accuracy_history.append(1)
                        st.session_state.current_card = None
                        st.session_state.show_answer = False
                        st.session_state.last_feedback = f"Great. This card will reappear in about {interval} minute(s)."
                        st.rerun()
                with grade_col2:
                    if st.button("Needs Review", use_container_width=True):
                        interval = agent.submit_answer(current_card, False)
                        st.session_state.accuracy_history.append(0)
                        st.session_state.current_card = None
                        st.session_state.show_answer = False
                        st.session_state.last_feedback = f"No problem. We will bring this card back in about {interval} minute(s)."
                        st.rerun()
        else:
            render_empty_state(
                title="No active flashcard",
                description="Click 'Get Next Card' to begin your review session.",
                icon_name="quiz",
            )

    with col_related:
        st.markdown(f"<div class='section-title'>{icon('hub')} Related Topics</div>", unsafe_allow_html=True)
        if current_card and hasattr(agent, "rag"):
            if st.session_state.related_cache_for_card != current_card["id"]:
                st.session_state.related_cache_items = agent.rag.retrieve_similar(current_card["question"], n=4)
                st.session_state.related_cache_for_card = current_card["id"]

            similar = st.session_state.related_cache_items
            cards_map = st.session_state.all_cards_map
            shown = 0
            for item in similar:
                cid = item.get("card_id")
                related = cards_map.get(cid)
                if related and cid != current_card["id"]:
                    difficulty = related.get("difficulty", 2)
                    label = {1: "Easy", 2: "Medium", 3: "Hard"}.get(difficulty, "Medium")
                    if st.button(f"{label}: {related['question']}", key=f"related_{cid}", use_container_width=True):
                        st.session_state.current_card = related
                        st.session_state.show_answer = False
                        st.rerun()
                    shown += 1
            if shown == 0:
                st.markdown("<div class='small-muted'>No related cards found for this prompt.</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='small-muted'>Select a card to view semantically related questions.</div>", unsafe_allow_html=True)


# ── Quiz tab ──────────────────────────────────────────────────────────────────
with tab_quiz:
    st.markdown(f"<div class='section-title'>{icon('task_alt')} Quick Quiz</div>", unsafe_allow_html=True)
    st.markdown("Use a short multiple-choice quiz to validate retention before your next review cycle.")

    if len(agent.cards) < 2:
        render_empty_state(
            title="Quiz requires a study set",
            description="Generate flashcards first, then return here to launch a quiz of 5 to 10 questions.",
            icon_name="fact_check",
        )
    else:
        st.markdown(f"<div class='small-muted'>Configured from sidebar: {st.session_state.quiz_count} questions per quiz.</div>", unsafe_allow_html=True)
        if st.button("Start New Quiz", use_container_width=True):
            st.session_state.quiz_questions = prepare_quiz_questions(agent.cards, st.session_state.quiz_count)
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_results = [None] * len(st.session_state.quiz_questions)
            for i in range(len(st.session_state.quiz_questions)):
                key = f"quiz_choice_{i}"
                if key in st.session_state:
                    del st.session_state[key]

        quiz_questions = st.session_state.quiz_questions
        quiz_index = st.session_state.quiz_index

        if not quiz_questions:
            st.info("Start a quiz to begin answering multiple-choice questions.")
        elif quiz_index >= len(quiz_questions):
            total = len(quiz_questions)
            score = st.session_state.quiz_score
            percentage = (score / total) * 100 if total else 0

            st.markdown(
                f"""
                <div class="flashcard-shell">
                    <div class="flashcard-meta">
                        <span class="pill pill-medium">Quiz Complete</span>
                        <span>{score}/{total} correct</span>
                    </div>
                    <div class="flashcard-question">Your score: {percentage:.0f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if percentage >= 80:
                st.success("Excellent retention. You are ready to move forward.")
            elif percentage >= 60:
                st.info("Solid progress. A short review round should boost retention.")
            else:
                st.warning("Retention is still building. Review flashcards again and retry this quiz.")
        else:
            progress_value = (quiz_index + 1) / len(quiz_questions)
            st.progress(progress_value)

            current_q = quiz_questions[quiz_index]
            answered = st.session_state.quiz_results[quiz_index] is not None

            st.markdown(
                f"""
                <div class="flashcard-shell">
                    <div class="flashcard-meta">
                        <span class="pill pill-medium">Question {quiz_index + 1} / {len(quiz_questions)}</span>
                    </div>
                    <div class="flashcard-question">{_esc(current_q['question'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            selected_option = st.radio(
                "Choose one option",
                options=current_q["options"],
                index=None,
                key=f"quiz_choice_{quiz_index}",
            )

            if not answered:
                if st.button("Check Answer", key=f"check_{quiz_index}", use_container_width=True):
                    if selected_option is None:
                        st.warning("Please choose an option before submitting.")
                    else:
                        is_correct = selected_option == current_q["answer"]
                        st.session_state.quiz_results[quiz_index] = is_correct
                        if is_correct:
                            st.session_state.quiz_score += 1
                        st.rerun()
            else:
                if st.session_state.quiz_results[quiz_index]:
                    st.success("Correct answer.")
                else:
                    st.error(f"Incorrect. Correct answer: {current_q['answer']}")

                if st.button("Next Question", key=f"next_{quiz_index}", use_container_width=True):
                    st.session_state.quiz_index += 1
                    st.rerun()


# ── Dashboard tab ─────────────────────────────────────────────────────────────
with tab_dashboard:
    st.markdown(f"<div class='section-title'>{icon('insights')} Learning Dashboard</div>", unsafe_allow_html=True)
    st.markdown("Track your progress quality, difficulty performance, and reinforcement interval behavior.")

    dcol1, dcol2, dcol3, dcol4 = st.columns(4)
    dcol1.metric("Total Answers", stats.get("total_answered", 0))
    dcol2.metric("Correct", stats.get("correct", 0))
    dcol3.metric("Accuracy", f"{stats.get('accuracy', 0.0) * 100:.0f}%")
    dcol4.metric("Cards Due", stats.get("cards_due", 0))

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("### Accuracy Over Attempts")
        history = st.session_state.accuracy_history
        if len(history) >= 2:
            history_df = pd.DataFrame({
                "attempt": np.arange(1, len(history) + 1),
                "accuracy": history,
            })
            history_df["moving_average"] = history_df["accuracy"].rolling(
                window=min(8, len(history_df)), min_periods=1
            ).mean()

            base = alt.Chart(history_df).encode(
                x=alt.X("attempt:Q", title="Attempt", axis=alt.Axis(grid=False))
            )
            raw_line = base.mark_line(strokeWidth=2, color="#7fbdb4", opacity=0.65).encode(
                y=alt.Y("accuracy:Q", title="Accuracy", scale=alt.Scale(domain=[0, 1])),
                tooltip=["attempt:Q", alt.Tooltip("accuracy:Q", format=".2f")],
            )
            moving_line = base.mark_line(strokeWidth=3, color="#0f6467").encode(
                y=alt.Y("moving_average:Q", scale=alt.Scale(domain=[0, 1])),
                tooltip=["attempt:Q", alt.Tooltip("moving_average:Q", format=".2f")],
            )
            st.altair_chart((raw_line + moving_line).properties(height=300), use_container_width=True)
        else:
            st.markdown("<div class='small-muted'>Answer at least two cards to unlock trend analytics.</div>", unsafe_allow_html=True)

    with chart_col2:
        st.markdown("### Accuracy by Difficulty")
        by_diff = stats.get("accuracy_by_difficulty", {})
        diff_df = pd.DataFrame({
            "difficulty": ["Easy", "Medium", "Hard"],
            "accuracy": [by_diff.get(1, 0), by_diff.get(2, 0), by_diff.get(3, 0)],
            "color": ["#1f9d55", "#ce7c1f", "#c0392b"],
        })
        if any(diff_df["accuracy"].tolist()):
            diff_chart = (
                alt.Chart(diff_df)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("difficulty:N", title="Difficulty"),
                    y=alt.Y("accuracy:Q", title="Accuracy", scale=alt.Scale(domain=[0, 1])),
                    color=alt.Color("color:N", scale=None, legend=None),
                    tooltip=["difficulty:N", alt.Tooltip("accuracy:Q", format=".2f")],
                )
                .properties(height=300)
            )
            st.altair_chart(diff_chart, use_container_width=True)
        else:
            st.markdown("<div class='small-muted'>Difficulty analytics appear after your first graded answers.</div>", unsafe_allow_html=True)

    st.markdown("### Review Interval Selection")
    bandit_counts = stats.get("bandit_counts", {})
    if bandit_counts and any(bandit_counts.values()):
        interval_df = pd.DataFrame({
            "interval": list(bandit_counts.keys()),
            "count": list(bandit_counts.values()),
        })
        interval_chart = (
            alt.Chart(interval_df)
            .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6, color="#157f82")
            .encode(
                x=alt.X("interval:N", title="Interval"),
                y=alt.Y("count:Q", title="Selections"),
                tooltip=["interval:N", "count:Q"],
            )
            .properties(height=260)
        )
        st.altair_chart(interval_chart, use_container_width=True)
    else:
        st.markdown("<div class='small-muted'>Interval usage will appear after you submit a few flashcard answers.</div>", unsafe_allow_html=True)


# ── Ask tab ───────────────────────────────────────────────────────────────────
with tab_ask:
    st.markdown(f"<div class='section-title'>{icon('chat')} Ask Your Document</div>", unsafe_allow_html=True)

    if not st.session_state.extracted_text.strip():
        render_empty_state(
            title="No document loaded",
            description="Load text, a PDF, or a YouTube transcript from the sidebar first, then ask anything about it here.",
            icon_name="chat",
        )
    else:
        col_info, col_clear = st.columns([3, 1])
        with col_info:
            char_count = len(st.session_state.extracted_text)
            st.markdown(
                f"<div class='small-muted'>Chatting with your loaded document ({char_count:,} characters).</div>",
                unsafe_allow_html=True,
            )
        with col_clear:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        if not st.session_state.chat_history:
            st.markdown(
                """<div class='chat-welcome'>
                    <div class='chat-welcome-icon'>💬</div>
                    <div class='chat-welcome-title'>Ask anything about your document</div>
                    <div class='chat-welcome-sub'>Summaries, definitions, explanations, comparisons —<br>anything in the loaded material. Off-topic questions will be declined.</div>
                </div>""",
                unsafe_allow_html=True,
            )

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(_user_bubble(msg["content"]), unsafe_allow_html=True)
            else:
                st.markdown(_asst_bubble(msg["content"]), unsafe_allow_html=True)

        if st.session_state.pending_ai:
            st.session_state.pending_ai = False

            user_query = next(
                (m["content"] for m in reversed(st.session_state.chat_history) if m["role"] == "user"),
                "",
            )

            doc_rag = st.session_state.get("doc_rag")
            if doc_rag and doc_rag.chunk_count > 0:
                context = doc_rag.retrieve_context(user_query, n=5)
                context_label = "RELEVANT DOCUMENT SECTIONS (retrieved via semantic search)"
            else:
                context = st.session_state.extracted_text[:8000]
                context_label = "DOCUMENT CONTENT"

            system_prompt = f"""You are a focused study assistant. Your ONLY job is to answer questions based on the document content provided below.

RULES:
- Answer ONLY questions that are directly relevant to the content in this document.
- If a question is clearly unrelated or not covered by the document, respond with: "That topic isn't covered in your loaded document. Try asking something specific to what you've loaded."
- Never use outside knowledge — base every answer solely on the document content.
- Keep answers clear, accurate, and concise.

{context_label}:
{context}"""

            messages = [{"role": "system", "content": system_prompt}]
            for past_msg in st.session_state.chat_history[-10:]:
                messages.append({"role": past_msg["role"], "content": past_msg["content"]})

            groq_client = get_groq_client()
            stream = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1024,
                stream=True,
            )

            resp_slot = st.empty()
            full_response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    resp_slot.markdown(_asst_bubble(full_response, streaming=True), unsafe_allow_html=True)
            resp_slot.markdown(_asst_bubble(full_response), unsafe_allow_html=True)
            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

        if prompt := st.chat_input("Ask something about your document..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.pending_ai = True
            st.rerun()


# ── Summary tab ───────────────────────────────────────────────────────────────
with tab_summary:
    st.markdown(f"<div class='section-title'>{icon('description')} Summary Notes</div>", unsafe_allow_html=True)
    st.markdown("Generate structured notes from your source material in your preferred learning style.")

    if not st.session_state.extracted_text.strip():
        render_empty_state(
            title="No source material loaded",
            description="Use the sidebar to load text, a PDF, or a YouTube transcript before generating notes.",
            icon_name="article",
        )
    else:
        style_labels = {
            "detailed": "Detailed prose",
            "bullets": "Bullet points",
            "eli5": "Explain simply",
        }

        st.session_state.summary_style = st.radio(
            "Summary style",
            options=["detailed", "bullets", "eli5"],
            format_func=lambda s: style_labels[s],
            horizontal=True,
            key="summary_style_radio",
        )

        if st.button("Generate Notes", use_container_width=True, type="primary"):
            with st.spinner("Generating notes..."):
                style_prompts = {
                    "detailed": (
                        "Generate structured study notes in detailed prose format using markdown headings and markdown bullet points where useful. "
                        "Organize into clear sections with short headings. "
                        "End with a section titled 'Key Takeaways' containing 3-5 points."
                    ),
                    "bullets": (
                        "Generate structured study notes in bullet point format as valid markdown. "
                        "Organize into clear sections with concise bullets. "
                        "End with a section titled 'Key Takeaways'."
                    ),
                    "eli5": (
                        "Generate study notes in simple, beginner-friendly language using valid markdown formatting. "
                        "Use easy analogies and avoid jargon. "
                        "End with a section titled 'Main Ideas'."
                    ),
                }

                summary_prompt = f"""{style_prompts[st.session_state.summary_style]}

Text to summarize:
{st.session_state.extracted_text[:8000]}

Generate the notes now."""

                try:
                    groq_client = get_groq_client()
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": summary_prompt}],
                        max_tokens=2000,
                    )
                    st.session_state.summary_output = response.choices[0].message.content
                except Exception as e:
                    st.error(f"Error generating summary notes: {e}")

        if st.session_state.summary_output:
            st.markdown(
                f'<div class="summary-chip">{style_labels.get(st.session_state.summary_style, "Detailed prose")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(st.session_state.summary_output)

            st.download_button(
                label="Download Notes",
                data=st.session_state.summary_output,
                file_name="study_notes.txt",
                mime="text/plain",
                use_container_width=True,
            )
