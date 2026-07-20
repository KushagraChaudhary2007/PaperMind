import math
import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


load_dotenv()


GENERATION_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash",
)

EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-001",
)

EMBEDDING_DIMENSIONS = 768

MAX_CHUNK_CHARACTERS = 4500
CHUNK_OVERLAP_CHARACTERS = 500
EMBEDDING_BATCH_SIZE = 20
MAX_RETRIEVED_CHUNKS = 5


class RAGServiceError(Exception):
    """
    Raised when PaperMind cannot index a paper,
    retrieve context, or generate an answer.
    """


@dataclass(slots=True)
class IndexedChunk:
    chunk_index: int
    text: str
    embedding: list[float]


@dataclass(slots=True)
class RetrievedChunk:
    chunk_index: int
    text: str
    similarity: float


class GeneratedRAGAnswer(BaseModel):
    answer: str = Field(
        description=(
            "A direct and accurate answer based only "
            "on the supplied research-paper context."
        )
    )

    insufficient_context: bool = Field(
        description=(
            "True when the supplied context does not "
            "contain enough information to answer."
        )
    )


def normalize_vector(
    values: list[float],
) -> list[float]:
    """
    Converts an embedding into a unit-length vector.
    """

    magnitude = math.sqrt(
        sum(
            float(value) * float(value)
            for value in values
        )
    )

    if magnitude == 0:
        raise RAGServiceError(
            "Gemini returned an invalid embedding."
        )

    return [
        float(value) / magnitude
        for value in values
    ]


def cosine_similarity(
    first: list[float],
    second: list[float],
) -> float:
    """
    Calculates similarity between two normalized
    embedding vectors.
    """

    if len(first) != len(second):
        raise RAGServiceError(
            "Embedding dimensions do not match."
        )

    return sum(
        first_value * second_value
        for first_value, second_value
        in zip(first, second)
    )


def chunk_paper_text(
    extracted_text: str,
) -> list[str]:
    """
    Divides extracted paper text into overlapping
    chunks suitable for semantic retrieval.
    """

    cleaned_text = re.sub(
        r"\n{3,}",
        "\n\n",
        extracted_text.strip(),
    )

    if not cleaned_text:
        raise RAGServiceError(
            "The research paper has no extracted text."
        )

    chunks: list[str] = []
    start = 0
    text_length = len(cleaned_text)

    while start < text_length:
        proposed_end = min(
            start + MAX_CHUNK_CHARACTERS,
            text_length,
        )

        end = proposed_end

        if proposed_end < text_length:
            minimum_break_position = (
                start
                + MAX_CHUNK_CHARACTERS // 2
            )

            paragraph_break = cleaned_text.rfind(
                "\n\n",
                minimum_break_position,
                proposed_end,
            )

            sentence_break = cleaned_text.rfind(
                ". ",
                minimum_break_position,
                proposed_end,
            )

            best_break = max(
                paragraph_break,
                sentence_break,
            )

            if best_break > start:
                end = best_break + 1

        chunk = cleaned_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = end - CHUNK_OVERLAP_CHARACTERS

        start = max(
            next_start,
            start + 1,
        )

    if not chunks:
        raise RAGServiceError(
            "PaperMind could not create paper chunks."
        )

    return chunks


def create_document_embeddings(
    chunks: list[str],
) -> tuple[list[list[float]], str]:
    """
    Creates normalized document embeddings with the
    Gemini Embedding API.

    This avoids loading SentenceTransformer/PyTorch
    inside the Railway backend.
    """

    if not chunks:
        raise RAGServiceError(
            "No paper chunks were provided."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RAGServiceError(
            "GEMINI_API_KEY was not found."
        )

    client = genai.Client(
        api_key=api_key,
    )

    embeddings: list[list[float]] = []

    try:
        for start in range(
            0,
            len(chunks),
            EMBEDDING_BATCH_SIZE,
        ):
            batch = chunks[
                start:
                start + EMBEDDING_BATCH_SIZE
            ]

            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=(
                        EMBEDDING_DIMENSIONS
                    ),
                ),
            )

            if not result.embeddings:
                raise RAGServiceError(
                    (
                        "Gemini returned no document "
                        "embeddings."
                    )
                )

            for embedding in result.embeddings:
                if not embedding.values:
                    raise RAGServiceError(
                        (
                            "Gemini returned an empty "
                            "document embedding."
                        )
                    )

                embeddings.append(
                    normalize_vector(
                        [
                            float(value)
                            for value
                            in embedding.values
                        ]
                    )
                )

        if len(embeddings) != len(chunks):
            raise RAGServiceError(
                (
                    "The number of generated embeddings "
                    "does not match the number of chunks."
                )
            )

        return (
            embeddings,
            EMBEDDING_MODEL,
        )

    except RAGServiceError:
        raise

    except Exception as error:
        print(
            "Gemini document embedding error:",
            type(error).__name__,
            str(error),
        )

        raise RAGServiceError(
            (
                "PaperMind could not create the "
                f"paper index: {error}"
            )
        ) from error

    finally:
        client.close()


def create_question_embedding(
    question: str,
) -> list[float]:
    """
    Creates a normalized question embedding with the
    Gemini Embedding API.
    """

    cleaned_question = question.strip()

    if not cleaned_question:
        raise RAGServiceError(
            "The question cannot be empty."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RAGServiceError(
            "GEMINI_API_KEY was not found."
        )

    client = genai.Client(
        api_key=api_key,
    )

    try:
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=cleaned_question,
            config=types.EmbedContentConfig(
                task_type="QUESTION_ANSWERING",
                output_dimensionality=(
                    EMBEDDING_DIMENSIONS
                ),
            ),
        )

        if not result.embeddings:
            raise RAGServiceError(
                "Gemini returned no question embedding."
            )

        embedding = result.embeddings[0]

        if not embedding.values:
            raise RAGServiceError(
                "Gemini returned an empty question embedding."
            )

        return normalize_vector(
            [
                float(value)
                for value
                in embedding.values
            ]
        )

    except RAGServiceError:
        raise

    except Exception as error:
        print(
            "Gemini question embedding error:",
            type(error).__name__,
            str(error),
        )

        raise RAGServiceError(
            (
                "PaperMind could not understand "
                f"the question: {error}"
            )
        ) from error

    finally:
        client.close()


def retrieve_relevant_chunks(
    question: str,
    indexed_chunks: list[IndexedChunk],
) -> list[RetrievedChunk]:
    """
    Retrieves the paper chunks most semantically
    relevant to the user's question.
    """

    if not indexed_chunks:
        raise RAGServiceError(
            "The paper has not been indexed."
        )

    question_embedding = (
        create_question_embedding(question)
    )

    scored_chunks: list[RetrievedChunk] = []

    for chunk in indexed_chunks:
        similarity = cosine_similarity(
            question_embedding,
            chunk.embedding,
        )

        scored_chunks.append(
            RetrievedChunk(
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                similarity=similarity,
            )
        )

    scored_chunks.sort(
        key=lambda chunk: chunk.similarity,
        reverse=True,
    )

    return scored_chunks[
        :MAX_RETRIEVED_CHUNKS
    ]


def build_history_text(
    history: list[dict],
) -> str:
    """
    Formats recent messages for conversational
    continuity.
    """

    if not history:
        return "No previous conversation."

    lines: list[str] = []

    for message in history[-6:]:
        role = str(
            message.get("role", "user")
        ).upper()

        content = str(
            message.get("content", "")
        ).strip()

        if content:
            lines.append(
                f"{role}: {content}"
            )

    return (
        "\n".join(lines)
        or "No previous conversation."
    )


def generate_rag_answer(
    question: str,
    retrieved_chunks: list[RetrievedChunk],
    history: list[dict] | None = None,
) -> tuple[GeneratedRAGAnswer, str]:
    """
    Generates an answer grounded only in retrieved
    research-paper chunks.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RAGServiceError(
            "GEMINI_API_KEY was not found in Backend/.env."
        )

    if not retrieved_chunks:
        raise RAGServiceError(
            "No relevant paper context was found."
        )

    context_sections: list[str] = []

    for chunk in retrieved_chunks:
        context_sections.append(
            (
                f"[Chunk {chunk.chunk_index}]\n"
                f"{chunk.text}"
            )
        )

    context_text = "\n\n".join(
        context_sections
    )

    history_text = build_history_text(
        history or []
    )

    prompt = f"""
You are PaperMind, a research-paper question-answering
assistant.

Answer the user's question using only the retrieved
research-paper context supplied below.

Rules:

1. Do not use outside knowledge.
2. Do not invent facts, results, datasets, or claims.
3. When possible, cite supporting chunks using labels
   such as [Chunk 2].
4. If the context does not contain enough information,
   clearly say that the paper does not provide enough
   information.
5. Distinguish the paper's own contribution from work
   mentioned in its references.
6. Keep the answer clear and directly related to the
   user's question.
7. Previous conversation may help understand a follow-up
   question, but factual claims must still be supported by
   the retrieved paper context.

RECENT CONVERSATION

{history_text}

RETRIEVED PAPER CONTEXT

{context_text}

USER QUESTION

{question.strip()}
""".strip()

    client = genai.Client(
        api_key=api_key
    )

    try:
        interaction = client.interactions.create(
            model=GENERATION_MODEL,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": (
                    GeneratedRAGAnswer
                    .model_json_schema()
                ),
            },
        )

        if not interaction.output_text:
            raise RAGServiceError(
                "Gemini returned an empty answer."
            )

        answer = (
            GeneratedRAGAnswer
            .model_validate_json(
                interaction.output_text
            )
        )

        return answer, GENERATION_MODEL

    except RAGServiceError:
        raise

    except Exception as error:
        raise RAGServiceError(
            "PaperMind could not answer this question."
        ) from error

    finally:
        client.close()
