import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UserSimulator:
    """
    Simulates a student who gradually improves over time.

    Three user types:
    - fast_learner:  improves quickly (+8% every 10 answers)
    - normal:        standard improvement (+5% every 10 answers)
    - slow_learner:  improves slowly (+2% every 10 answers)

    Base accuracy by difficulty:
    - difficulty 1: 70%
    - difficulty 2: 50%
    - difficulty 3: 30%
    """

    USER_TYPES = {
        "fast_learner": {"improvement": 0.08, "label": "Fast Learner"},
        "normal":       {"improvement": 0.05, "label": "Normal Student"},
        "slow_learner": {"improvement": 0.02, "label": "Slow Learner"},
    }

    BASE_ACCURACY = {1: 0.70, 2: 0.50, 3: 0.30}

    def __init__(self, user_type: str = "normal"):
        if user_type not in self.USER_TYPES:
            raise ValueError(f"user_type must be one of {list(self.USER_TYPES.keys())}")

        self.user_type       = user_type
        self.improvement     = self.USER_TYPES[user_type]["improvement"]
        self.label           = self.USER_TYPES[user_type]["label"]
        self.total_answered  = 0
        self.total_correct   = 0

    def answer(self, card: dict) -> bool:
        """
        Simulate answering a card.
        Probability of correct answer increases as student improves.
        Returns: True if correct, False if wrong.
        """
        difficulty  = card.get("difficulty", 2)
        base        = self.BASE_ACCURACY.get(difficulty, 0.5)

        # Improvement bonus: every 10 answers, accuracy goes up
        bonus       = (self.total_answered // 10) * self.improvement
        prob        = min(base + bonus, 0.95)   # cap at 95%

        is_correct  = random.random() < prob
        self.total_answered += 1
        if is_correct:
            self.total_correct += 1

        return is_correct

    def get_accuracy(self) -> float:
        """Return overall accuracy so far."""
        return self.total_correct / max(self.total_answered, 1)

    def reset(self):
        """Reset simulator state for a new experiment run."""
        self.total_answered = 0
        self.total_correct  = 0

    def get_stats(self) -> dict:
        return {
            "user_type":      self.user_type,
            "label":          self.label,
            "total_answered": self.total_answered,
            "total_correct":  self.total_correct,
            "accuracy":       round(self.get_accuracy(), 3)
        }


if __name__ == "__main__":
    # Test all three user types
    test_card_easy = {"id": "card_0", "difficulty": 1,
                      "times_shown": 0, "times_correct": 0}
    test_card_hard = {"id": "card_1", "difficulty": 3,
                      "times_shown": 0, "times_correct": 0}

    for user_type in ["fast_learner", "normal", "slow_learner"]:
        sim = UserSimulator(user_type=user_type)

        # Simulate 30 answers
        for i in range(30):
            card = test_card_easy if i % 2 == 0 else test_card_hard
            sim.answer(card)

        stats = sim.get_stats()
        print(f"\n[{stats['label']}]")
        print(f"  Total answered: {stats['total_answered']}")
        print(f"  Accuracy:       {stats['accuracy']}")

    # Test improvement over time
    print("\n--- Improvement over time (normal user, hard cards) ---")
    sim = UserSimulator("normal")
    for checkpoint in [10, 20, 30, 40, 50]:
        while sim.total_answered < checkpoint:
            sim.answer(test_card_hard)
        print(f"  After {checkpoint} answers: accuracy = {sim.get_accuracy():.3f}")

    print("\nAll simulator tests passed!")