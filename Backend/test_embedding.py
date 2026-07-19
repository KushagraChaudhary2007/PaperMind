import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

model_name = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001",
)


def main():
    if not api_key:
        print("ERROR: GEMINI_API_KEY is missing.")
        return

    client = genai.Client(
        api_key=api_key
    )

    try:
        response = client.models.embed_content(
            model=model_name,
            contents=(
                "This research paper studies "
                "machine-learning methods."
            ),
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=768,
            ),
        )

        if not response.embeddings:
            print("ERROR: No embedding was returned.")
            return

        values = response.embeddings[0].values

        print("Embedding test successful!")
        print("Model:", model_name)
        print("Vector dimensions:", len(values))

    except errors.APIError as error:
        print("Gemini API error")
        print("Status code:", error.code)
        print("Message:", error.message)

    except Exception as error:
        print("Unexpected error")
        print("Type:", type(error).__name__)
        print("Message:", str(error))

    finally:
        client.close()


if __name__ == "__main__":
    main()