import numpy as np


class IntervalBandit:
    """
    Contextual Bandit (LinUCB) for optimizing flashcard review intervals.
    Context: card's current state (accuracy, difficulty, times shown)
    Action: choose a review interval (1 min, 10 min, 1 hour, 1 day, 3 days)
    Reward: +1 if user answers correctly next time, -1 if wrong
    """

    INTERVALS = [1, 10, 60, 1440, 4320]        # in minutes
    INTERVAL_NAMES = ["1 min", "10 min", "1 hour", "1 day", "3 days"]

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha                      # exploration coefficient
        self.n_actions = len(self.INTERVALS)
        self.n_features = 3                     # context vector size

        # Each action has its own A matrix and b vector (LinUCB)
        self.A = [np.identity(self.n_features) for _ in range(self.n_actions)]
        self.b = [np.zeros(self.n_features)    for _ in range(self.n_actions)]

    def get_context(self, card: dict) -> np.ndarray:
        """
        Convert card state into a 3-dimensional context vector.
        [accuracy_rate, normalized_difficulty, normalized_times_shown]
        """
        times_shown   = card.get("times_shown", 0)
        times_correct = card.get("times_correct", 0)

        accuracy      = times_correct / max(times_shown, 1)
        difficulty    = card.get("difficulty", 2) / 3.0
        shown_norm    = min(times_shown / 20.0, 1.0)

        return np.array([accuracy, difficulty, shown_norm])

    def select_interval(self, card: dict) -> tuple:
        """
        Use LinUCB to select the best review interval.
        Returns: (action_index, interval_minutes)
        UCB formula: theta^T * x + alpha * sqrt(x^T * A_inv * x)
        """
        context   = self.get_context(card)
        ucb_vals  = []

        for i in range(self.n_actions):
            A_inv   = np.linalg.inv(self.A[i])
            theta   = A_inv @ self.b[i]
            exploit = theta @ context
            explore = self.alpha * np.sqrt(context @ A_inv @ context)
            ucb_vals.append(exploit + explore)

        action = int(np.argmax(ucb_vals))
        return action, self.INTERVALS[action]

    def update(self, action: int, card: dict, reward: float):
        """
        Update A matrix and b vector for the chosen action.
        Called after user answers the card at next review.
        """
        context       = self.get_context(card)
        self.A[action] += np.outer(context, context)
        self.b[action] += reward * context

    def get_interval_name(self, action: int) -> str:
        return self.INTERVAL_NAMES[action]


if __name__ == "__main__":
    bandit = IntervalBandit(alpha=1.0)

    # Fake card: shown 4 times, correct 3 times, difficulty 2
    test_card = {
        "id": "card_0",
        "difficulty": 2,
        "times_shown": 4,
        "times_correct": 3
    }

    # Test get_context
    ctx = bandit.get_context(test_card)
    print(f"Context vector: {ctx}")

    # Test select_interval
    action, interval = bandit.select_interval(test_card)
    print(f"Selected action: {action} -> {bandit.get_interval_name(action)} ({interval} mins)")

    # Test update with positive reward (answered correctly)
    bandit.update(action, test_card, reward=1.0)
    print(f"Updated A[{action}] and b[{action}] successfully")

    # Test again after update — should potentially pick different interval
    action2, interval2 = bandit.select_interval(test_card)
    print(f"After update — selected: {bandit.get_interval_name(action2)} ({interval2} mins)")

    print("All bandit tests passed!")