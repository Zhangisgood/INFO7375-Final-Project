import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ReviewAgent:
    """
    Supporting agent for review scheduling.
    Manages due cards, priority queue, and session summaries.
    """

    def __init__(self):
        self.session_start = time.time()

    def get_due_cards(self, all_cards: list, due_times: dict) -> list:
        """
        Return cards that are currently due for review.
        A card is due if its scheduled time <= now.
        """
        now = time.time()
        due = [c for c in all_cards if due_times.get(c["id"], 0) <= now]
        return due

    def get_priority_score(self, card: dict) -> float:
        """
        Calculate priority score for a card.
        Higher score = should be reviewed sooner.

        Formula:
        - Higher difficulty = higher priority
        - Lower accuracy    = higher priority
        - More times shown  = slight boost (needs reinforcement)
        """
        difficulty    = card.get("difficulty", 2)
        times_shown   = card.get("times_shown", 0)
        times_correct = card.get("times_correct", 0)

        accuracy = times_correct / max(times_shown, 1)

        # Weighted priority formula
        priority = (difficulty * 2.0) + ((1.0 - accuracy) * 3.0) + (times_shown * 0.1)
        return round(priority, 4)

    def sort_by_priority(self, due_cards: list) -> list:
        """
        Sort due cards by priority score (highest first).
        Helps Q-Learning make better selections.
        """
        return sorted(
            due_cards,
            key=lambda c: self.get_priority_score(c),
            reverse=True
        )

    def get_session_summary(self, cards: list) -> dict:
        """
        Return a summary of the current review session.
        """
        if not cards:
            return {"message": "No cards reviewed yet."}

        total         = sum(c["times_shown"]   for c in cards)
        correct       = sum(c["times_correct"] for c in cards)
        accuracy      = correct / max(total, 1)

        # Find hardest card (lowest accuracy, minimum 1 attempt)
        attempted = [c for c in cards if c["times_shown"] > 0]
        if attempted:
            hardest = min(
                attempted,
                key=lambda c: c["times_correct"] / c["times_shown"]
            )
        else:
            hardest = None

        # Find most reviewed card
        most_reviewed = max(cards, key=lambda c: c["times_shown"])

        session_duration = round(time.time() - self.session_start, 1)

        return {
            "total_attempts":    total,
            "total_correct":     correct,
            "overall_accuracy":  round(accuracy, 3),
            "hardest_card":      hardest["question"] if hardest else "N/A",
            "most_reviewed":     most_reviewed["question"],
            "session_duration":  f"{session_duration}s",
            "cards_in_session":  len(cards)
        }


if __name__ == "__main__":
    import time

    agent = ReviewAgent()

    # Fake cards for testing
    fake_cards = [
        {"id": "card_0", "question": "What is Q-Learning?",
         "answer": "Value-based RL", "difficulty": 2,
         "times_shown": 5, "times_correct": 4},
        {"id": "card_1", "question": "What is a Bandit?",
         "answer": "RL exploration", "difficulty": 1,
         "times_shown": 3, "times_correct": 3},
        {"id": "card_2", "question": "What is epsilon-greedy?",
         "answer": "Exploration strategy", "difficulty": 3,
         "times_shown": 6, "times_correct": 2},
    ]

    # Fake due times: card_0 overdue, card_1 due now, card_2 not due yet
    now = time.time()
    fake_due_times = {
        "card_0": now - 100,   # overdue
        "card_1": now - 1,     # just due
        "card_2": now + 9999,  # not due yet
    }

    # Test get_due_cards
    due = agent.get_due_cards(fake_cards, fake_due_times)
    print(f"Due cards: {[c['id'] for c in due]}")

    # Test get_priority_score
    for card in fake_cards:
        score = agent.get_priority_score(card)
        print(f"Priority of {card['id']}: {score}")

    # Test sort_by_priority
    sorted_cards = agent.sort_by_priority(due)
    print(f"\nSorted by priority: {[c['id'] for c in sorted_cards]}")

    # Test get_session_summary
    print("\n--- Session Summary ---")
    summary = agent.get_session_summary(fake_cards)
    for k, v in summary.items():
        print(f"  {k}: {v}")

    print("\nAll review agent tests passed!")