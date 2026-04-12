import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.flashcard_agent import FlashcardAgent
from simulation.user_simulator import UserSimulator


# Sample text used as knowledge base for all experiments
SAMPLE_TEXT_CARDS = [
    {"id": "card_0", "question": "What is reinforcement learning?",
     "answer": "A learning paradigm where agents learn through rewards and penalties.",
     "difficulty": 2, "times_shown": 0, "times_correct": 0},
    {"id": "card_1", "question": "What is Q-Learning?",
     "answer": "A value-based RL algorithm that learns action values.",
     "difficulty": 2, "times_shown": 0, "times_correct": 0},
    {"id": "card_2", "question": "What is epsilon-greedy?",
     "answer": "A strategy balancing exploration and exploitation.",
     "difficulty": 2, "times_shown": 0, "times_correct": 0},
    {"id": "card_3", "question": "What is a contextual bandit?",
     "answer": "An RL approach that selects actions based on context.",
     "difficulty": 3, "times_shown": 0, "times_correct": 0},
    {"id": "card_4", "question": "What is RAG?",
     "answer": "Retrieval-Augmented Generation combining retrieval with generation.",
     "difficulty": 3, "times_shown": 0, "times_correct": 0},
    {"id": "card_5", "question": "What is a reward function?",
     "answer": "A function that defines the goal of an RL agent.",
     "difficulty": 1, "times_shown": 0, "times_correct": 0},
    {"id": "card_6", "question": "What is the Bellman equation?",
     "answer": "A recursive formula for computing optimal value functions.",
     "difficulty": 3, "times_shown": 0, "times_correct": 0},
    {"id": "card_7", "question": "What is a policy in RL?",
     "answer": "A mapping from states to actions that guides agent behavior.",
     "difficulty": 2, "times_shown": 0, "times_correct": 0},
]


def reset_cards() -> list:
    """Return a fresh copy of cards with zeroed statistics."""
    return [dict(card) for card in SAMPLE_TEXT_CARDS]


def run_experiment(n_rounds: int = 100, user_type: str = "normal") -> dict:
    """
    Run a full RL learning experiment.
    Every round: select card -> simulate answer -> update RL -> record metrics.
    Records accuracy and epsilon every 10 rounds.
    """
    agent     = FlashcardAgent()
    simulator = UserSimulator(user_type=user_type)
    agent.load_cards(reset_cards())

    accuracy_history = []
    epsilon_history  = []
    reward_history   = []

    for round_num in range(n_rounds):
        card       = agent.get_next_card()
        is_correct = simulator.answer(card)
        interval   = agent.submit_answer(card, is_correct)

        reward_history.append(1.0 if is_correct else -1.0)

        # Record metrics every 10 rounds
        if (round_num + 1) % 10 == 0:
            recent   = agent.user_stats["recent_results"][-20:]
            acc      = sum(recent) / max(len(recent), 1)
            eps      = agent.selector.epsilon

            accuracy_history.append(round(acc, 4))
            epsilon_history.append(round(eps, 4))

            print(f"  [{user_type}] Round {round_num+1:3d}: "
                  f"accuracy={acc:.3f}  epsilon={eps:.4f}")

    return {
        "user_type":        user_type,
        "n_rounds":         n_rounds,
        "accuracy_history": accuracy_history,
        "epsilon_history":  epsilon_history,
        "final_accuracy":   accuracy_history[-1] if accuracy_history else 0,
        "final_epsilon":    epsilon_history[-1]  if epsilon_history  else 0,
    }


def run_baseline_experiment(n_rounds: int = 100, user_type: str = "normal") -> dict:
    """
    Baseline: random card selection (no Q-Learning).
    Used for comparison against our RL system.
    """
    import random

    simulator        = UserSimulator(user_type=user_type)
    cards            = reset_cards()
    recent_results   = []
    accuracy_history = []

    for round_num in range(n_rounds):
        # Random card selection (no RL)
        card       = random.choice(cards)
        is_correct = simulator.answer(card)
        recent_results.append(int(is_correct))

        if (round_num + 1) % 10 == 0:
            recent = recent_results[-20:]
            acc    = sum(recent) / max(len(recent), 1)
            accuracy_history.append(round(acc, 4))

    return {
        "user_type":        f"{user_type}_baseline",
        "n_rounds":         n_rounds,
        "accuracy_history": accuracy_history,
        "final_accuracy":   accuracy_history[-1] if accuracy_history else 0,
    }


def run_all_experiments(n_rounds: int = 100) -> dict:
    """
    Run all experiments: 3 user types x (RL + baseline).
    Saves results to data/experiment_results.json.
    """
    print("=" * 50)
    print("Running all experiments...")
    print("=" * 50)

    results = {}

    for user_type in ["fast_learner", "normal", "slow_learner"]:
        print(f"\n--- RL System: {user_type} ---")
        results[user_type] = run_experiment(n_rounds, user_type)

        print(f"\n--- Baseline: {user_type} ---")
        results[f"{user_type}_baseline"] = run_baseline_experiment(n_rounds, user_type)

    # Save results to file
    os.makedirs("data", exist_ok=True)
    with open("data/experiment_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n[Saved] data/experiment_results.json")

    # Print final summary
    print("\n" + "=" * 50)
    print("FINAL ACCURACY SUMMARY")
    print("=" * 50)
    for key, result in results.items():
        print(f"  {key:30s}: {result['final_accuracy']:.3f}")

    return results


if __name__ == "__main__":
    results = run_all_experiments(n_rounds=100)
    print("\nAll experiments completed!")