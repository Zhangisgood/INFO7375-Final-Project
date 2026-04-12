import numpy as np
import json
import random


class QLearningCardSelector:
    """
    Q-Learning algorithm for selecting which flashcard to show next.
    State: (card_difficulty, user_accuracy_level, time_since_last_review_level)
    Action: select a card (by card_id)
    Reward: +1 for correct answer, -1 for wrong answer
    """

    def __init__(self, lr=0.1, gamma=0.9, epsilon=0.4, epsilon_decay=0.99, epsilon_min=0.05):
        self.lr = lr                        # learning rate
        self.gamma = gamma                  # discount factor
        self.epsilon = epsilon              # exploration rate
        self.epsilon_decay = epsilon_decay  # how fast epsilon decreases
        self.epsilon_min = epsilon_min      # lowest epsilon can go
        self.q_table = {}                   # {state: {card_id: q_value}}

    def get_state(self, card: dict, user_stats: dict) -> tuple:
        """
        Convert card info + user history into a state tuple (used as Q-table key).
        Returns: (difficulty_level, accuracy_level, time_level)
        """
        # Dimension 1: card difficulty (1, 2, or 3)
        difficulty = card.get("difficulty", 2)

        # Dimension 2: user's recent accuracy level (0=low, 1=medium, 2=high)
        recent = user_stats.get("recent_results", [])
        if len(recent) == 0:
            acc_level = 1  # default medium if no history
        else:
            acc = sum(recent[-10:]) / len(recent[-10:])
            acc_level = 0 if acc < 0.4 else (1 if acc < 0.7 else 2)

        # Dimension 3: time since last review in seconds (0=short, 1=medium, 2=long)
        gap = user_stats.get("time_since_last", 0)
        gap_level = 0 if gap < 60 else (1 if gap < 3600 else 2)

        return (difficulty, acc_level, gap_level)
    
    def get_q_values(self, state: tuple) -> dict:
        """Get Q-values for a state. Initialize to 0 if state not seen before."""
        if state not in self.q_table:
            self.q_table[state] = {}
        return self.q_table[state]

    def select_card(self, cards: list, user_stats: dict) -> int:
        """
        Select which card to show next using epsilon-greedy policy.
        Returns: index of selected card in the cards list
        """
        if not cards:
            return 0

        # Exploration: pick a random card
        if random.random() < self.epsilon:
            return random.randint(0, len(cards) - 1)

        # Exploitation: pick the card with highest Q-value
        best_idx = 0
        best_q = float("-inf")

        for i, card in enumerate(cards):
            state = self.get_state(card, user_stats)
            q_vals = self.get_q_values(state)
            q = q_vals.get(card["id"], 0.0)
            if q > best_q:
                best_q = q
                best_idx = i

        return best_idx

    def update(self, card: dict, user_stats: dict, reward: float,
               next_card: dict = None, next_user_stats: dict = None):
        """
        Update Q-table using Q-Learning formula:
        Q(s,a) <- Q(s,a) + lr * [reward + gamma * max_Q(s') - Q(s,a)]
        """
        state = self.get_state(card, user_stats)
        q_vals = self.get_q_values(state)
        current_q = q_vals.get(card["id"], 0.0)

        # Calculate next state's max Q-value
        next_max_q = 0.0
        if next_card and next_user_stats:
            next_state = self.get_state(next_card, next_user_stats)
            next_q_vals = self.get_q_values(next_state)
            if next_q_vals:
                next_max_q = max(next_q_vals.values())

        # Q-Learning update formula
        new_q = current_q + self.lr * (reward + self.gamma * next_max_q - current_q)
        self.q_table[state][card["id"]] = new_q

        # Decay epsilon after each update
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        return abs(new_q - current_q)  # return TD error for monitoring
    
    def save(self, path: str = "data/q_table.json"):
        """Save Q-table to a JSON file for persistence."""
        serializable = {}
        for state, actions in self.q_table.items():
            key = str(state)  # convert tuple to string for JSON
            serializable[key] = actions

        with open(path, "w") as f:
            json.dump({
                "q_table": serializable,
                "epsilon": self.epsilon
            }, f, indent=2)

        print(f"[Q-Learning] Q-table saved to {path}")

    def load(self, path: str = "data/q_table.json"):
        """Load Q-table from a JSON file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)

            self.q_table = {}
            for key, actions in data["q_table"].items():
                state = eval(key)  # convert string back to tuple
                self.q_table[state] = actions

            self.epsilon = data.get("epsilon", self.epsilon_min)
            print(f"[Q-Learning] Q-table loaded from {path}")

        except FileNotFoundError:
            print(f"[Q-Learning] No saved Q-table found at {path}, starting fresh.")

if __name__ == "__main__":
    # Quick test to verify everything works
    selector = QLearningCardSelector()

    # Create two fake cards for testing
    test_cards = [
        {"id": "card_0", "question": "What is ML?", "answer": "Machine Learning",
         "difficulty": 1, "times_shown": 0, "times_correct": 0},
        {"id": "card_1", "question": "What is RL?", "answer": "Reinforcement Learning",
         "difficulty": 3, "times_shown": 2, "times_correct": 1},
    ]

    test_stats = {"recent_results": [1, 0, 1, 1, 0], "time_since_last": 120}

    # Test get_state
    state = selector.get_state(test_cards[0], test_stats)
    print(f"State for card_0: {state}")

    # Test select_card
    idx = selector.select_card(test_cards, test_stats)
    print(f"Selected card index: {idx} -> {test_cards[idx]['id']}")

    # Test update
    td_error = selector.update(test_cards[0], test_stats, reward=1.0,
                                next_card=test_cards[1], next_user_stats=test_stats)
    print(f"TD Error after update: {td_error:.4f}")
    print(f"Epsilon after update: {selector.epsilon:.4f}")
    print(f"Q-table size: {len(selector.q_table)} states")

    # Test save
    selector.save()
    print("All tests passed!")