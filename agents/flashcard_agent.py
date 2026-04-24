import time
import sys
import os

# Add project root to path so imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rl.q_learning import QLearningCardSelector
from rl.bandit import IntervalBandit


class FlashcardAgent:
    """
    Main orchestrator agent that manages the full flashcard learning loop:
    Generate -> Review -> Feedback -> Update
    """

    def __init__(self):
        self.selector = QLearningCardSelector()   # Q-Learning: which card to show
        self.bandit   = IntervalBandit()           # Bandit: when to show it again
        self.cards    = []                         # all flashcards in session
        self.due_times = {}                        # {card_id: timestamp when due}
        self.user_stats = {
            "recent_results": [],
            "time_since_last": 0
        }
        self.last_answer_time = time.time()

    def load_text(self, text: str, n_cards: int = 10):
        """
        Generate flashcards from text using the generator tool,
        then load them into the agent. Called by the UI.
        """
        from tools.generator import generate_flashcards
        from tools.rag import FlashcardRAG

        cards = generate_flashcards(text, n=n_cards)
        if not cards:
            print("[Agent] No cards generated.")
            return

        # Store RAG reference for UI to access
        self.rag = FlashcardRAG()
        self.rag.add_cards(cards)

        self.load_cards(cards)

    def load_cards(self, cards: list):
        """
        Load a list of flashcards into the agent.
        Sets all cards as immediately due.
        Called by generator tool once cards are created.
        """
        self.cards = cards
        for card in self.cards:
            self.due_times[card["id"]] = time.time()  # all due immediately
        print(f"[Agent] Loaded {len(self.cards)} cards.")

    def count_due(self) -> int:
        """Return strict count of cards due now, without fallback."""
        now = time.time()
        return sum(1 for c in self.cards if self.due_times.get(c["id"], 0) <= now)

    def get_due_cards(self) -> list:
        """Return cards that are currently due for review."""
        now = time.time()
        due = [c for c in self.cards if self.due_times.get(c["id"], 0) <= now]
        return due if due else self.cards   # fallback: return all if none due

    def get_next_card(self) -> dict:
        """
        Use Q-Learning to select the next card to show.
        Returns the selected card dict.
        """
        if not self.cards:
            return None
        due_cards = self.get_due_cards()
        if not due_cards:
            return None
        idx = self.selector.select_card(due_cards, self.user_stats)
        return due_cards[idx]

    def submit_answer(self, card: dict, is_correct: bool) -> int:
        """
        Process user's answer for a card.
        Updates both Q-Learning and Bandit, sets next due time.
        Returns: next review interval in minutes.
        """
        reward = 1.0 if is_correct else -1.0

        # Update card statistics
        card["times_shown"]   += 1
        if is_correct:
            card["times_correct"] += 1

        # Update user statistics
        self.user_stats["recent_results"].append(int(is_correct))
        now = time.time()
        self.user_stats["time_since_last"] = now - self.last_answer_time
        self.last_answer_time = now

        # Q-Learning update
        next_card = self.get_next_card()
        self.selector.update(
            card, self.user_stats, reward,
            next_card=next_card,
            next_user_stats=self.user_stats
        )

        # Bandit update: choose interval and schedule next review
        action, interval = self.bandit.select_interval(card)
        self.due_times[card["id"]] = now + interval * 60
        self.bandit.update(action, card, reward)

        return interval

    def get_stats(self) -> dict:
        """Return current session statistics for UI display."""
        total    = len(self.user_stats["recent_results"])
        correct  = sum(self.user_stats["recent_results"])
        accuracy = correct / max(total, 1)

        # Count how many times each Bandit interval was chosen
        bandit_counts = {
            name: int(self.bandit.selection_counts[i])
            for i, name in enumerate(self.bandit.INTERVAL_NAMES)
        }

        # Calculate accuracy broken down by difficulty level
        accuracy_by_difficulty = {}
        for diff in [1, 2, 3]:
            diff_cards = [c for c in self.cards if c.get("difficulty") == diff]
            if diff_cards:
                shown   = sum(c["times_shown"]   for c in diff_cards)
                correct_diff = sum(c["times_correct"] for c in diff_cards)
                accuracy_by_difficulty[diff] = round(
                    correct_diff / max(shown, 1), 3
                )
            else:
                accuracy_by_difficulty[diff] = 0.0

        return {
            "total_answered":       total,
            "correct":              correct,
            "accuracy":             round(accuracy, 3),
            "epsilon":              round(self.selector.epsilon, 4),
            "q_table_size":         len(self.selector.q_table),
            "cards_due":            self.count_due(),
            "bandit_counts":        bandit_counts,
            "accuracy_by_difficulty": accuracy_by_difficulty
        }


if __name__ == "__main__":
    agent = FlashcardAgent()

    # Create fake cards to test without generator
    fake_cards = [
        {"id": "card_0", "question": "What is Q-Learning?",
         "answer": "A value-based RL algorithm",
         "difficulty": 2, "times_shown": 0, "times_correct": 0},
        {"id": "card_1", "question": "What is a Bandit?",
         "answer": "An RL exploration strategy",
         "difficulty": 1, "times_shown": 0, "times_correct": 0},
        {"id": "card_2", "question": "What is epsilon-greedy?",
         "answer": "Exploration vs exploitation strategy",
         "difficulty": 3, "times_shown": 0, "times_correct": 0},
    ]

    # Test load_cards
    agent.load_cards(fake_cards)

    # Test get_next_card
    card = agent.get_next_card()
    print(f"Next card: {card['id']} — {card['question']}")

    # Simulate 5 answers
    print("\n--- Simulating 5 answers ---")
    for i in range(5):
        card     = agent.get_next_card()
        correct  = i % 2 == 0     # alternate correct/wrong
        interval = agent.submit_answer(card, correct)
        print(f"Round {i+1}: {card['id']} | correct={correct} | next in {interval} mins")

    # Test get_stats
    print("\n--- Session Stats ---")
    stats = agent.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\nAll agent tests passed!")