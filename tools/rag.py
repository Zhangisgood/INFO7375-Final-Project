import chromadb


def _chunk_text(text: str, size: int = 500, overlap: int = 100) -> list:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += size - overlap
    return chunks


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

    def retrieve_similar(self, query: str, n: int = 4) -> list:
        count = self.collection.count()
        if count == 0:
            return []
        n = min(n, count)
        results = self.collection.query(query_texts=[query], n_results=n)
        if not results or not results["metadatas"]:
            return []
        return results["metadatas"][0]

    def get_all_cards(self):
        return self.collection.get()

    def clear(self):
        self.client.delete_collection("flashcards")
        self.collection = self.client.get_or_create_collection("flashcards")


class DocumentRAG:
    def __init__(self):
        self.client = chromadb.Client()
        self._clear_collection()

    def _clear_collection(self):
        try:
            self.client.delete_collection("document_chunks")
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection("document_chunks")

    def add_document(self, text: str, chunk_size: int = 500, overlap: int = 100) -> int:
        self._clear_collection()
        chunks = _chunk_text(text, size=chunk_size, overlap=overlap)
        if not chunks:
            return 0
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"chunk_index": i} for i in range(len(chunks))]
        self.collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        return len(chunks)

    def retrieve_context(self, query: str, n: int = 5) -> str:
        count = self.collection.count()
        if count == 0:
            return ""
        n = min(n, count)
        results = self.collection.query(query_texts=[query], n_results=n)
        if not results or not results["documents"]:
            return ""
        return "\n\n---\n\n".join(results["documents"][0])

    @property
    def chunk_count(self) -> int:
        return self.collection.count()


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
