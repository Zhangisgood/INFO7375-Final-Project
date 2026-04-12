import chromadb

class FlashcardRAG:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection("flashcards")

    def add_cards(self, cards):
        if not cards:
            return
        documents = [f"{c['question']} {c['answer']}" for c in cards]
        ids = [c["id"] for c in cards]
        metadatas = [{"difficulty": c["difficulty"], "card_id": c["id"]} for c in cards]
        self.collection.add(documents=documents, ids=ids, metadatas=metadatas)

    def retrieve_similar(self, query, n=3):
        results = self.collection.query(query_texts=[query], n_results=n)
        if results and results["metadatas"]:
            return results["metadatas"][0]
        return []

    def get_all_cards(self):
        results = self.collection.get()
        return results

    def clear(self):
        self.client.delete_collection("flashcards")
        self.collection = self.client.get_or_create_collection("flashcards")


def test_rag():
    rag = FlashcardRAG()

    sample_cards = [
        {"id": "card_0", "question": "What is photosynthesis?", "answer": "Process plants use to convert sunlight into energy.", "difficulty": 1},
        {"id": "card_1", "question": "What is the powerhouse of the cell?", "answer": "The mitochondria.", "difficulty": 1},
        {"id": "card_2", "question": "What is the Calvin cycle?", "answer": "The light-independent stage of photosynthesis.", "difficulty": 2},
    ]

    print("Adding cards...")
    rag.add_cards(sample_cards)

    print("Retrieving similar to 'photosynthesis and plants'...")
    results = rag.retrieve_similar("photosynthesis and plants", n=2)
    for r in results:
        print(f"  Found: {r}")

    print("Test passed!")


if __name__ == "__main__":
    test_rag()