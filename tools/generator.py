from dotenv import load_dotenv
import os
load_dotenv()
import anthropic
import json

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_flashcards(text, n):
    prompt = f"""You are a flashcard generator. Given the following text, generate exactly {n} flashcards.

Return ONLY a JSON array. No explanation, no markdown, no code blocks. Just the raw JSON array.

Each flashcard must have exactly these fields:
- "question": a clear question string
- "answer": a concise answer string
- "difficulty": an integer 1, 2, or 3 (1=easy, 2=medium, 3=hard)

Text:
{text}

Return only the JSON array, nothing else."""

    try:
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        cards = json.loads(raw)
    except json.JSONDecodeError:
        # Retry once
        try:
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text.strip()
            cards = json.loads(raw)
        except Exception as e:
            print(f"Error on retry: {e}")
            return []
    except Exception as e:
        print(f"API error: {e}")
        return []

    # Add required fields
    for i, card in enumerate(cards):
        card["id"] = f"card_{i}"
        card["times_shown"] = 0
        card["times_correct"] = 0

    return cards


def test_generator():
    sample_text = """
    Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide 
    to produce oxygen and energy in the form of glucose. It occurs in the chloroplasts, 
    specifically using the green pigment chlorophyll. The process has two stages: 
    the light-dependent reactions and the Calvin cycle.
    """
    print("Testing generator...")
    cards = generate_flashcards(sample_text, 3)
    if cards:
        print(f"Generated {len(cards)} cards:")
        for card in cards:
            print(f"\n  ID: {card['id']}")
            print(f"  Q: {card['question']}")
            print(f"  A: {card['answer']}")
            print(f"  Difficulty: {card['difficulty']}")
    else:
        print("No cards generated — check your API key.")


if __name__ == "__main__":
    test_generator()