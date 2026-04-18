import json
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def moving_average(data: list, window: int = 10) -> list:
    """Smooth a data series using a moving average."""
    result = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        result.append(round(sum(data[start:i+1]) / (i - start + 1), 4))
    return result


def plot_learning_curves(results: dict, save_path: str = "results/learning_curves.png"):
    os.makedirs("results", exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Learning Curves: RL System vs Baseline", fontsize=14, fontweight="bold")

    user_types = ["fast_learner", "normal", "slow_learner"]
    titles     = ["Fast Learner", "Normal Student", "Slow Learner"]
    colors_rl  = ["#2196F3", "#4CAF50", "#FF9800"]
    colors_bl  = ["#90CAF9", "#A5D6A7", "#FFCC80"]

    for i, (user_type, title) in enumerate(zip(user_types, titles)):
        ax = axes[i]

        rl_acc = results[user_type]["accuracy_history"]
        bl_acc = results[f"{user_type}_baseline"]["accuracy_history"]
        x      = list(range(1, len(rl_acc) + 1))

        ax.plot(x, rl_acc,
                color=colors_rl[i], linewidth=1.5,
                alpha=0.5, label="RL System")
        ax.plot(x, moving_average(rl_acc),
                color=colors_rl[i], linewidth=2,
                linestyle="--", label="RL (smoothed)")
        ax.plot(x, bl_acc,
                color=colors_bl[i], linewidth=1.5,
                alpha=0.5, label="Baseline (random)")

        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Round")
        ax.set_ylabel("Accuracy")
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"[Saved] {save_path}")
    plt.close()


def plot_epsilon_decay(results: dict, save_path: str = "results/epsilon_decay.png"):
    os.makedirs("results", exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_title("Exploration Rate (ε) Decay Over Time", fontsize=13, fontweight="bold")

    colors     = ["#2196F3", "#4CAF50", "#FF9800"]
    user_types = ["fast_learner", "normal", "slow_learner"]
    labels     = ["Fast Learner", "Normal Student", "Slow Learner"]

    for user_type, label, color in zip(user_types, labels, colors):
        eps = results[user_type]["epsilon_history"]
        x   = list(range(1, len(eps) + 1))
        ax.plot(x, eps, color=color, linewidth=2, marker="o", markersize=5,
                markevery=10, label=label)

    ax.axhline(y=0.05, color="red", linestyle="--",
               linewidth=1, alpha=0.7, label="Min ε (0.05)")
    ax.set_xlabel("Round")
    ax.set_ylabel("Epsilon (ε)")
    ax.set_ylim(0, 0.5)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"[Saved] {save_path}")
    plt.close()


def plot_final_comparison(results: dict, save_path: str = "results/final_comparison.png"):
    os.makedirs("results", exist_ok=True)

    user_types  = ["fast_learner", "normal", "slow_learner"]
    labels      = ["Fast Learner", "Normal Student", "Slow Learner"]
    rl_scores   = [results[u]["final_accuracy"] for u in user_types]
    bl_scores   = [results[f"{u}_baseline"]["final_accuracy"] for u in user_types]

    x     = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 6))
    bars1 = ax.bar(x - width/2, rl_scores, width,
                   label="RL System", color="#2196F3", alpha=0.85)
    bars2 = ax.bar(x + width/2, bl_scores, width,
                   label="Baseline (random)", color="#90CAF9", alpha=0.85)

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{bar.get_height():.3f}", ha="center", fontsize=10, fontweight="bold")
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{bar.get_height():.3f}", ha="center", fontsize=10)

    ax.set_title("Final Accuracy: RL System vs Baseline", fontsize=13, fontweight="bold")
    ax.set_ylabel("Final Accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.15)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"[Saved] {save_path}")
    plt.close()


def plot_all(results_path: str = "data/experiment_results.json"):
    with open(results_path, "r") as f:
        results = json.load(f)

    print("Generating all charts...")
    plot_learning_curves(results)
    plot_epsilon_decay(results)
    plot_final_comparison(results)
    print("\nAll charts saved to results/ folder!")


if __name__ == "__main__":
    plot_all()