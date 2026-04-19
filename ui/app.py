import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from agents.flashcard_agent import FlashcardAgent

st.set_page_config(page_title="Smart Flashcard RL", layout="wide")
st.title("🧠 Smart Flashcard Generator with RL-Optimized Review")

# Init session state
if "agent" not in st.session_state:
    st.session_state.agent = FlashcardAgent()
if "current_card" not in st.session_state:
    st.session_state.current_card = None
if "show_answer" not in st.session_state:
    st.session_state.show_answer = False
if "accuracy_history" not in st.session_state:
    st.session_state.accuracy_history = []
if "next_interval" not in st.session_state:
    st.session_state.next_interval = None
if "all_cards_map" not in st.session_state:
    st.session_state.all_cards_map = {}

agent = st.session_state.agent

with st.sidebar:
    st.header("📥 Generate Flashcards")

    input_mode = st.radio("Input type", ["📝 Text", "📄 PDF", "🎥 YouTube"])

    text_input = ""

    if input_mode == "📝 Text":
        text_input = st.text_area("Paste your text here", height=200,
                                   placeholder="Paste any article, notes, or textbook paragraph...")

    elif input_mode == "📄 PDF":
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        if uploaded_file:
            try:
                from tools.input_processor import extract_text_from_pdf
                text_input = extract_text_from_pdf(uploaded_file)
                st.success(f"PDF loaded: {len(text_input)} characters extracted.")
            except Exception as e:
                st.error(f"Failed to read PDF: {e}")

    elif input_mode == "🎥 YouTube":
        yt_url = st.text_input("YouTube URL",
                                placeholder="https://www.youtube.com/watch?v=...")
        if yt_url:
            try:
                from tools.input_processor import extract_text_from_youtube
                text_input = extract_text_from_youtube(yt_url)
                st.success(f"Transcript loaded: {len(text_input)} characters extracted.")
            except Exception as e:
                st.error(f"Failed to load transcript: {e}")

    n_cards = st.slider("Number of cards", min_value=5, max_value=20, value=10)

    if st.button("Generate Flashcards", type="primary"):
        if text_input.strip():
            with st.spinner("Generating flashcards..."):
                agent.load_text(text_input, n_cards)
                st.session_state.all_cards_map = {c["id"]: c for c in agent.cards}
                st.session_state.agent = agent
                st.session_state.current_card = None
                st.session_state.show_answer = False
            st.success(f"Generated {n_cards} flashcards!")
        else:
            st.warning("Please paste some text first.")

    st.divider()
    st.header("📊 RL Status")
    stats = agent.get_stats()
    st.metric("Current ε (exploration)", f"{stats.get('epsilon', 1.0):.3f}")
    st.metric("Q-table states learned", stats.get("q_table_size", 0))

    bandit_counts = stats.get("bandit_counts", {})
    if bandit_counts:
        st.write("**Bandit interval selections:**")
        for interval, count in bandit_counts.items():
            st.write(f"  {interval} min: {count}x")

# ── Main Area ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📚 Review Cards")

    if st.button("Get Next Card"):
        card = agent.get_next_card()
        if card:
            st.session_state.current_card = card
            st.session_state.show_answer = False
            st.session_state.next_interval = None
        else:
            st.info("No cards due right now. Generate some cards first!")

    card = st.session_state.current_card
    if card:
        st.subheader("Question")
        difficulty_label = {1: "🟢 Easy", 2: "🟡 Medium", 3: "🔴 Hard"}
        st.caption(difficulty_label.get(card.get("difficulty", 1), ""))
        st.write(card["question"])

        if st.button("Show Answer"):
            st.session_state.show_answer = True

        if st.session_state.show_answer:
            st.subheader("Answer")
            st.success(card["answer"])

            col_correct, col_wrong = st.columns(2)
            with col_correct:
                if st.button("✅ Correct"):
                    interval = agent.submit_answer(card, True)
                    st.session_state.next_interval = interval
                    st.session_state.accuracy_history.append(1)
                    st.session_state.current_card = None
                    st.session_state.show_answer = False
                    st.rerun()
            with col_wrong:
                if st.button("❌ Wrong"):
                    interval = agent.submit_answer(card, False)
                    st.session_state.next_interval = interval
                    st.session_state.accuracy_history.append(0)
                    st.session_state.current_card = None
                    st.session_state.show_answer = False
                    st.rerun()

        if st.session_state.next_interval is not None:
            st.info(f"⏱ Next review in: **{st.session_state.next_interval} minutes**")
    else:
        st.info("Click 'Get Next Card' to start reviewing.")

with col2:
    st.header("📈 Related Cards")
    if card:
        similar = agent.rag.retrieve_similar(card["question"], n=3)
        difficulty_label = {1: "🟢 Easy", 2: "🟡 Medium", 3: "🔴 Hard"}
        cards_map = st.session_state.all_cards_map
        for s in similar:
            cid = s["card_id"]
            related = cards_map.get(cid)
            if related and cid != card["id"]:
                label = f"{difficulty_label.get(s['difficulty'], '')} {related['question']}"
                if st.button(label, key=f"related_{cid}"):
                    st.session_state.current_card = related
                    st.session_state.show_answer = False
                    st.session_state.next_interval = None
                    st.rerun()
    else:
        st.write("Select a card to see related topics.")

# ── RL Dashboard ──────────────────────────────────────────────────────────────
st.divider()
st.header("📉 RL Dashboard")

dash_col1, dash_col2 = st.columns(2)

with dash_col1:
    st.subheader("Accuracy Over Time")
    history = st.session_state.accuracy_history
    if len(history) >= 2:
        fig, ax = plt.subplots()
        window = min(10, len(history))
        moving_avg = np.convolve(history, np.ones(window)/window, mode='valid')
        ax.plot(range(len(history)), history, alpha=0.3, label="Raw")
        ax.plot(range(len(moving_avg)), moving_avg, label="Moving Avg", linewidth=2)
        ax.set_ylim(0, 1.1)
        ax.set_xlabel("Answers")
        ax.set_ylabel("Accuracy")
        ax.legend()
        st.pyplot(fig)
        plt.close()
    else:
        st.write("Answer some cards to see your accuracy trend.")

with dash_col2:
    st.subheader("Accuracy by Difficulty")
    stats = agent.get_stats()
    by_diff = stats.get("accuracy_by_difficulty", {})
    if by_diff:
        fig, ax = plt.subplots()
        labels = ["Easy", "Medium", "Hard"]
        values = [by_diff.get(1, 0), by_diff.get(2, 0), by_diff.get(3, 0)]
        ax.bar(labels, values, color=["green", "orange", "red"])
        ax.set_ylim(0, 1.1)
        ax.set_ylabel("Accuracy")
        st.pyplot(fig)
        plt.close()
    else:
        st.write("Answer some cards to see accuracy by difficulty.")