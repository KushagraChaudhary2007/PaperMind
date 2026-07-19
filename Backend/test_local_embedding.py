import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()


MODEL_NAME = os.getenv(
    "LOCAL_EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


def main() -> None:
    print("Loading local embedding model...")
    print("Model:", MODEL_NAME)

    model = SentenceTransformer(
        MODEL_NAME,
        device="cpu",
    )

    sentences = [
        "This paper studies machine-learning models.",
        "What machine-learning method does the paper use?",
    ]

    embeddings = model.encode(
        sentences,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    print("Local embedding test successful!")
    print("Number of vectors:", len(embeddings))
    print("Vector dimensions:", len(embeddings[0]))


if __name__ == "__main__":
    main()