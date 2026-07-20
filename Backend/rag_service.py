import os
import re
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity


load_dotenv()


GENERATION_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash",
)

MAX_CHUNK_CHARACTERS = 4500
CHUNK_OVERLAP_CHARACTERS = 500
MAX_RETRIEVED_CHUNKS = 5

# Stored only as a marker in PaperChunk.embedding_model.
# TF-IDF vectors are computed on demand and are not stored.
RETRIEVAL_MODEL = "tfidf-v1"


class RAGServiceError(Exception):
    """
    Raised when PaperMind cannot index a paper,
    retrieve context, or generate an answer.
    """


@dataclass(slots=True)
class IndexedChunk:
    chunk_index: int
    text: str
    # Kept for compatibility with existing endpoint code.
    # TF-IDF retrieval does not use stored embeddings.
    embedding: list[float] | None = None


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


def chunk_paper_text(
    extracted_text: str,
) -> list[str]:
    """
    Divides extracted paper text into overlapping
    chunks suitable for retrieval.
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


def retrieve_relevant_chunks(
    question: str,
    indexed_chunks: list[IndexedChunk],
) -> list[RetrievedChunk]:
    """
    Retrieves the chunks most relevant to the question
    using lightweight TF-IDF + cosine similarity.

    This avoids local transformer models and embedding
    API calls, so it uses much less RAM and no embedding
    quota.
    """

    cleaned_question = question.strip()

    if not cleaned_question:
        raise RAGServiceError(
            "The question cannot be empty."
        )

    if not indexed_chunks:
        raise RAGServiceError(
            "The paper has not been indexed."
        )

    texts = [
        chunk.text
        for chunk in indexed_chunks
    ]

    try:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=20000,
        )

        document_matrix = vectorizer.fit_transform(
            texts
        )

        question_vector = vectorizer.transform(
            [cleaned_question]
        )

        similarities = sklearn_cosine_similarity(
            question_vector,
            document_matrix,
        ).ravel()

    except Exception as error:
        print(
            "TF-IDF retrieval error:",
            type(error).__name__,
            str(error),
        )

        raise RAGServiceError(
            "PaperMind could not search this paper."
        ) from error

    scored_chunks = [
        RetrievedChunk(
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            similarity=float(similarity),
        )
        for chunk, similarity
        in zip(
            indexed_chunks,
            similarities,
        )
    ]

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

    Temporary Gemini 429 rate-limit errors are retried
    with exponential backoff before failing gracefully.
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

    retry_delays = (5, 15, 30)
    last_error: Exception | None = None

    try:
        for attempt in range(
            len(retry_delays) + 1
        ):
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
                last_error = error
                error_text = str(error).lower()

                is_rate_limited = (
                    "429" in error_text
                    or "resource_exhausted"
                    in error_text
                    or "rate limit" in error_text
                )

                if (
                    is_rate_limited
                    and attempt < len(retry_delays)
                ):
                    delay = retry_delays[attempt]

                    print(
                        "Gemini rate limited. "
                        f"Retrying in {delay}s "
                        f"(attempt {attempt + 2}/"
                        f"{len(retry_delays) + 1})"
                    )

                    time.sleep(delay)
                    continue

                print(
                    "Gemini RAG generation error:",
                    type(error).__name__,
                    str(error),
                )

                if is_rate_limited:
                    raise RAGServiceError(
                        (
                            "Gemini is temporarily rate-limited. "
                            "Please wait about a minute and "
                            "try again."
                        )
                    ) from error

                raise RAGServiceError(
                    "PaperMind could not answer this question."
                ) from error

        raise RAGServiceError(
            "PaperMind could not answer this question."
        ) from last_error

    finally:
        client.close()