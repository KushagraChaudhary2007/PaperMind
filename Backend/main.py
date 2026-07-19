import os
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ai_service import (
    AIServiceError,
    extract_citation_metadata,
    generate_level_explanation,
    generate_paper_comparison,
    generate_paper_summary,
    generate_research_roadmap,
)
from auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from database import Base, engine, get_db
from models import (
    Paper,
    PaperChatMessage,
    PaperChunk,
    PaperCitation,
    PaperComparison,
    PaperContent,
    PaperExplanation,
    PaperRoadmap,
    PaperSummary,
    User,
)
from pdf_service import (
    PDFExtractionError,
    extract_pdf_text,
)
from rag_service import (
    IndexedChunk,
    RAGServiceError,
    chunk_paper_text,
    create_document_embeddings,
    generate_rag_answer,
    retrieve_relevant_chunks,
)
from citation_service import (
    generate_all_citations,
)
from schemas import (
    PaperChatHistoryMessageResponse,
    PaperChatRequest,
    PaperChatResponse,
    PaperCitationMetadataResponse,
    PaperComparisonRequest,
    PaperComparisonResponse,
    PaperExplanationRequest,
    PaperExplanationResponse,
    PaperFormattedCitationsResponse,
    PaperResponse,
    PaperRoadmapResponse,
    PaperSummaryResponse,
    PaperTextResponse,
    Token,
    UserCreate,
    UserResponse,
)


# =========================================================
# Database setup
# =========================================================

# Creates database tables that do not already exist.
# All models must be imported before this line.
Base.metadata.create_all(bind=engine)


# =========================================================
# File upload configuration
# =========================================================

BACKEND_DIRECTORY = (
    Path(__file__)
    .resolve()
    .parent
)


# Local:
#
# Backend/uploads
#
# Production:
#
# Railway persistent volume:
# /data/uploads

UPLOAD_DIRECTORY = Path(
    os.getenv(
        "UPLOAD_DIRECTORY",
        str(
            BACKEND_DIRECTORY
            / "uploads"
        ),
    )
).resolve()


UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

MAX_FILE_SIZE = 20 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
}


# =========================================================
# FastAPI application
# =========================================================

app = FastAPI(
    title="PaperMind API",
    description=(
        "Authentication, secure PDF upload, text "
        "extraction, AI summaries, adaptive explanations, "
        "research-paper chat, paper comparisons, "
        "and personalized research roadmaps."
    ),
    version="1.5.0",
)


# =========================================================
# CORS configuration
# =========================================================

FRONTEND_URL = (
    os.getenv(
        "FRONTEND_URL",
        "",
    )
    .strip()
    .rstrip("/")
)


ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# Add the deployed frontend URL when running
# PaperMind in production.

if FRONTEND_URL:

    ALLOWED_ORIGINS.append(
        FRONTEND_URL
    )


app.add_middleware(
    CORSMiddleware,

    allow_origins=(
        ALLOWED_ORIGINS
    ),

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# =========================================================
# Authentication configuration
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
)


def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
) -> User:
    """
    Validates the JWT token and returns the currently
    authenticated PaperMind user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Could not validate authentication "
            "credentials."
        ),
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = decode_access_token(token)

        subject = payload.get("sub")

        if subject is None:
            raise credentials_exception

        user_id = int(subject)

    except (
        InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise credentials_exception

    user = db.scalar(
        select(User).where(
            User.id == user_id,
        )
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    return user


# =========================================================
# Shared database helper functions
# =========================================================

def get_owned_paper(
    paper_id: int,
    current_user: User,
    db: Session,
) -> Paper:
    """
    Returns a paper only when it belongs to the
    authenticated user.
    """

    paper = db.scalar(
        select(Paper).where(
            Paper.id == paper_id,
            Paper.user_id == current_user.id,
        )
    )

    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research paper not found.",
        )

    return paper


def get_ready_paper_content(
    paper: Paper,
    db: Session,
) -> PaperContent:
    """
    Returns readable extracted text for a paper.
    """

    paper_content = db.scalar(
        select(PaperContent).where(
            PaperContent.paper_id == paper.id,
        )
    )

    if paper_content is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Text has not been extracted "
                "from this paper."
            ),
        )

    if (
        paper_content.extraction_status != "ready"
        or not paper_content.extracted_text.strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This PDF does not contain readable "
                "digital text. OCR may be required."
            ),
        )

    return paper_content


def get_paper_summary_or_error(
    paper: Paper,
    db: Session,
) -> PaperSummary:
    """
    Returns a saved AI summary required by
    summary-based AI features.
    """

    summary = db.scalar(
        select(PaperSummary).where(
            PaperSummary.paper_id == paper.id,
        )
    )

    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Generate an AI summary for "
                f"'{paper.original_filename}' before "
                "using this AI feature."
            ),
        )

    return summary


# =========================================================
# API response helper functions
# =========================================================

def create_summary_response(
    paper: Paper,
    summary: PaperSummary,
) -> dict:
    """
    Creates the public response for a saved summary.
    """

    return {
        "paper_id": paper.id,
        "original_filename": paper.original_filename,
        "paper_title": summary.paper_title,
        "plain_language_summary": (
            summary.plain_language_summary
        ),
        "research_problem": summary.research_problem,
        "methodology": summary.methodology,
        "key_findings": summary.key_findings,
        "limitations": summary.limitations,
        "future_work": summary.future_work,
        "keywords": summary.keywords,
        "model_name": summary.model_name,
        "generated_at": summary.generated_at,
    }


def create_explanation_response(
    paper: Paper,
    explanation: PaperExplanation,
) -> dict:
    """
    Creates the public response for a saved
    level-based explanation.
    """

    return {
        "paper_id": paper.id,
        "original_filename": paper.original_filename,
        "level": explanation.level,
        "explanation_title": (
            explanation.explanation_title
        ),
        "explanation": explanation.explanation_text,
        "key_concepts": explanation.key_concepts,
        "glossary": explanation.glossary,
        "study_takeaways": (
            explanation.study_takeaways
        ),
        "model_name": explanation.model_name,
        "generated_at": explanation.generated_at,
    }


def create_source_excerpt(
    text: str,
    maximum_length: int = 320,
) -> str:
    """
    Creates a short readable excerpt from a
    retrieved RAG chunk.
    """

    single_line_text = " ".join(
        text.split()
    )

    if len(single_line_text) <= maximum_length:
        return single_line_text

    return (
        single_line_text[:maximum_length].rstrip()
        + "..."
    )


def create_summary_context(
    paper: Paper,
    summary: PaperSummary,
) -> dict:
    """
    Creates the structured paper information sent
    to the AI comparison service.
    """

    return {
        "paper_id": paper.id,
        "filename": paper.original_filename,
        "paper_title": summary.paper_title,
        "plain_language_summary": (
            summary.plain_language_summary
        ),
        "research_problem": summary.research_problem,
        "methodology": summary.methodology,
        "key_findings": summary.key_findings,
        "limitations": summary.limitations,
        "future_work": summary.future_work,
        "keywords": summary.keywords,
    }


def create_roadmap_context(
    paper: Paper,
    summary: PaperSummary,
) -> dict:
    """
    Creates the structured paper information used
    to generate a personalized research roadmap.
    """

    return {
        "paper_id": paper.id,
        "filename": paper.original_filename,
        "paper_title": summary.paper_title,
        "plain_language_summary": (
            summary.plain_language_summary
        ),
        "research_problem": summary.research_problem,
        "methodology": summary.methodology,
        "key_findings": summary.key_findings,
        "limitations": summary.limitations,
        "future_work": summary.future_work,
        "keywords": summary.keywords,
    }


def create_roadmap_response(
    paper: Paper,
    roadmap: PaperRoadmap,
) -> dict:
    """
    Creates the public API response for a saved
    research roadmap.
    """

    return {
        "paper_id": paper.id,
        "original_filename": paper.original_filename,
        "roadmap_title": roadmap.roadmap_title,
        "research_domain": roadmap.research_domain,
        "overview": roadmap.overview,
        "prerequisites": roadmap.prerequisites,
        "roadmap_steps": roadmap.roadmap_steps,
        "research_directions": (
            roadmap.research_directions
        ),
        "suggested_projects": (
            roadmap.suggested_projects
        ),
        "model_name": roadmap.model_name,
        "generated_at": roadmap.generated_at,
    }


def create_comparison_response(
    comparison: PaperComparison,
    paper_a: Paper,
    summary_a: PaperSummary,
    paper_b: Paper,
    summary_b: PaperSummary,
) -> dict:
    """
    Creates the public response for a saved
    paper comparison.
    """

    return {
        "id": comparison.id,

        "paper_a_id": paper_a.id,
        "paper_a_filename": paper_a.original_filename,
        "paper_a_title": summary_a.paper_title,

        "paper_b_id": paper_b.id,
        "paper_b_filename": paper_b.original_filename,
        "paper_b_title": summary_b.paper_title,

        "comparison_title": (
            comparison.comparison_title
        ),
        "overview": comparison.overview,
        "similarities": comparison.similarities,
        "differences": comparison.differences,

        "research_problem_comparison": (
            comparison.research_problem_comparison
        ),
        "methodology_comparison": (
            comparison.methodology_comparison
        ),
        "findings_comparison": (
            comparison.findings_comparison
        ),
        "limitations_comparison": (
            comparison.limitations_comparison
        ),
        "practical_guidance": (
            comparison.practical_guidance
        ),

        "model_name": comparison.model_name,
        "generated_at": comparison.generated_at,
    }

def create_citation_metadata_response(
    paper: Paper,
    citation: PaperCitation,
) -> dict:
    """
    Creates the public API response for saved
    bibliographic citation metadata.
    """

    return {
        "paper_id": paper.id,

        "original_filename": (
            paper.original_filename
        ),

        "title": (
            citation.title
        ),

        "authors": (
            citation.authors
        ),

        "publication_year": (
            citation.publication_year
        ),

        "journal_or_conference": (
            citation.journal_or_conference
        ),

        "publisher": (
            citation.publisher
        ),

        "volume": (
            citation.volume
        ),

        "issue": (
            citation.issue
        ),

        "pages": (
            citation.pages
        ),

        "doi": (
            citation.doi
        ),

        "url": (
            citation.url
        ),

        "document_type": (
            citation.document_type
        ),

        "is_academic_publication": (
            citation.is_academic_publication
        ),

        "citation_warning": (
            citation.citation_warning
        ),

        "missing_fields": (
            citation.missing_fields
        ),

        "model_name": (
            citation.model_name
        ),

        "extracted_at": (
            citation.extracted_at
        ),
    }

def create_citation_formatter_metadata(
    citation: PaperCitation,
) -> dict:
    """
    Creates the normalized metadata dictionary
    consumed by citation_service.py.
    """

    return {
        "title":
            citation.title,

        "authors":
            citation.authors,

        "publication_year":
            citation.publication_year,

        "journal_or_conference":
            citation.journal_or_conference,

        "publisher":
            citation.publisher,

        "volume":
            citation.volume,

        "issue":
            citation.issue,

        "pages":
            citation.pages,

        "doi":
            citation.doi,

        "url":
            citation.url,

        "document_type":
            citation.document_type,

        "is_academic_publication":
            (
                citation
                .is_academic_publication
            ),

        "citation_warning":
            citation.citation_warning,
    }


# =========================================================
# RAG index helper
# =========================================================

def get_or_create_paper_chunks(
    paper: Paper,
    paper_content: PaperContent,
    db: Session,
) -> list[PaperChunk]:
    """
    Returns an existing semantic-search index.

    When no index exists, the paper is split into
    chunks, embedded locally, and stored.
    """

    existing_chunks = list(
        db.scalars(
            select(PaperChunk)
            .where(
                PaperChunk.paper_id == paper.id,
            )
            .order_by(
                PaperChunk.chunk_index.asc(),
            )
        ).all()
    )

    if existing_chunks:
        return existing_chunks

    chunk_texts = chunk_paper_text(
        paper_content.extracted_text,
    )

    embeddings, embedding_model = (
        create_document_embeddings(
            chunk_texts,
        )
    )

    if len(chunk_texts) != len(embeddings):
        raise RAGServiceError(
            "Paper chunks and embeddings do not match."
        )

    new_chunks: list[PaperChunk] = []

    try:
        for index, (
            chunk_text,
            embedding,
        ) in enumerate(
            zip(
                chunk_texts,
                embeddings,
            ),
            start=1,
        ):
            chunk = PaperChunk(
                paper_id=paper.id,
                chunk_index=index,
                chunk_text=chunk_text,
                embedding=embedding,
                embedding_model=embedding_model,
            )

            db.add(chunk)
            new_chunks.append(chunk)

        db.commit()

        for chunk in new_chunks:
            db.refresh(chunk)

        return new_chunks

    except IntegrityError:
        db.rollback()

        # Another request may have created the index
        # while embeddings were being generated.
        existing_chunks = list(
            db.scalars(
                select(PaperChunk)
                .where(
                    PaperChunk.paper_id == paper.id,
                )
                .order_by(
                    PaperChunk.chunk_index.asc(),
                )
            ).all()
        )

        if existing_chunks:
            return existing_chunks

        raise RAGServiceError(
            "The paper index could not be saved."
        )

    except Exception:
        db.rollback()
        raise


# =========================================================
# Basic routes
# =========================================================

@app.get("/")
def home():
    """
    Confirms that the backend is running.
    """

    return {
        "message": "PaperMind backend is running!",
    }


@app.get("/health")
def health_check():
    """
    Basic backend health check.
    """

    return {
        "status": "healthy",
        "service": "PaperMind API",
        "version": "1.5.0",
    }


# =========================================================
# User registration
# =========================================================

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Creates a new PaperMind user account.
    """

    normalized_email = (
        str(user_data.email)
        .strip()
        .lower()
    )

    normalized_name = (
        user_data.full_name
        .strip()
    )

    if len(normalized_name) < 2:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Full name must contain at least "
                "2 characters."
            ),
        )

    existing_user = db.scalar(
        select(User).where(
            User.email == normalized_email,
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An account with this email "
                "already exists."
            ),
        )

    new_user = User(
        full_name=normalized_name,
        email=normalized_email,
        hashed_password=hash_password(
            user_data.password,
        ),
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An account with this email "
                "already exists."
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The user account could not be created."
            ),
        )


# =========================================================
# User login
# =========================================================

@app.post(
    "/auth/login",
    response_model=Token,
)
def login_user(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Verifies email and password and returns a JWT.

    OAuth2 calls the email input "username".
    """

    normalized_email = (
        form_data.username
        .strip()
        .lower()
    )

    user = db.scalar(
        select(User).where(
            User.email == normalized_email,
        )
    )

    invalid_login_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    if user is None:
        raise invalid_login_exception

    if not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise invalid_login_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    access_token = create_access_token(
        subject=str(user.id),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# =========================================================
# Current authenticated user
# =========================================================

@app.get(
    "/auth/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    """
    Returns the authenticated user's profile.
    """

    return current_user


@app.get("/protected-test")
def protected_test(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    """
    Tests JWT authentication.
    """

    return {
        "message": (
            f"Welcome {current_user.full_name}. "
            "This is a protected PaperMind route."
        ),
        "user_id": current_user.id,
    }


# =========================================================
# Upload PDF and extract text
# =========================================================

@app.post(
    "/papers/upload",
    response_model=PaperResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_paper(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    file: Annotated[
        UploadFile,
        File(
            description=(
                "Research paper in PDF format."
            ),
        ),
    ],
):
    """
    Uploads a PDF, validates it, saves it, extracts
    its text, and stores its database records.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file has no filename.",
        )

    original_filename = (
        Path(file.filename)
        .name
        .strip()
    )

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The uploaded file has no valid filename."
            ),
        )

    if not original_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=415,
            detail="Only PDF files are allowed.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="The uploaded file must be a PDF.",
        )

    file_header = await file.read(1024)

    await file.seek(0)

    if b"%PDF-" not in file_header:
        raise HTTPException(
            status_code=415,
            detail=(
                "The selected file is not a valid PDF."
            ),
        )

    user_directory = (
        UPLOAD_DIRECTORY
        / f"user_{current_user.id}"
    )

    user_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_filename = f"{uuid4().hex}.pdf"

    destination_path = (
        user_directory
        / stored_filename
    )

    total_size = 0
    chunk_size = 1024 * 1024

    try:
        with destination_path.open("wb") as output_file:
            while True:
                chunk = await file.read(
                    chunk_size,
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            "PDF size cannot exceed "
                            "20 MB."
                        ),
                    )

                output_file.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded PDF is empty.",
            )

        extraction_result = extract_pdf_text(
            destination_path,
        )

        paper = Paper(
            user_id=current_user.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(destination_path),
            file_size=total_size,
            processing_status=(
                extraction_result.extraction_status
            ),
        )

        db.add(paper)
        db.flush()

        paper_content = PaperContent(
            paper_id=paper.id,
            extracted_text=extraction_result.text,
            page_count=extraction_result.page_count,
            character_count=(
                extraction_result.character_count
            ),
            extraction_status=(
                extraction_result.extraction_status
            ),
        )

        db.add(paper_content)
        db.commit()
        db.refresh(paper)

        return paper

    except PDFExtractionError as error:
        db.rollback()

        if destination_path.exists():
            destination_path.unlink()

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        )

    except HTTPException:
        db.rollback()

        if destination_path.exists():
            destination_path.unlink()

        raise

    except Exception as error:
        db.rollback()

        if destination_path.exists():
            destination_path.unlink()

        print(
            "PDF processing error:",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The PDF could not be processed."
            ),
        )

    finally:
        await file.close()


# =========================================================
# List authenticated user's papers
# =========================================================

@app.get(
    "/papers",
    response_model=list[PaperResponse],
)
def list_user_papers(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns the authenticated user's papers from
    newest to oldest.
    """

    papers = db.scalars(
        select(Paper)
        .where(
            Paper.user_id == current_user.id,
        )
        .order_by(
            Paper.uploaded_at.desc(),
        )
    ).all()

    return list(papers)


# =========================================================
# Read extracted paper text
# =========================================================

@app.get(
    "/papers/{paper_id}/text",
    response_model=PaperTextResponse,
)
def read_paper_text(
    paper_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns extracted text and document information.
    """

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    paper_content = db.scalar(
        select(PaperContent).where(
            PaperContent.paper_id == paper.id,
        )
    )

    if paper_content is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Text has not been extracted "
                "from this paper."
            ),
        )

    return {
        "paper_id": paper.id,
        "original_filename": paper.original_filename,
        "processing_status": paper.processing_status,
        "extraction_status": (
            paper_content.extraction_status
        ),
        "page_count": paper_content.page_count,
        "character_count": (
            paper_content.character_count
        ),
        "extracted_text": (
            paper_content.extracted_text
        ),
    }


# =========================================================
# Generate AI summary
# =========================================================

@app.post(
    "/papers/{paper_id}/summary",
    response_model=PaperSummaryResponse,
)
def generate_summary(
    paper_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Generates and stores a structured AI summary.
    """

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    existing_summary = db.scalar(
        select(PaperSummary).where(
            PaperSummary.paper_id == paper.id,
        )
    )

    if existing_summary is not None:
        return create_summary_response(
            paper,
            existing_summary,
        )

    paper_content = get_ready_paper_content(
        paper,
        db,
    )

    try:
        generated_summary, model_name = (
            generate_paper_summary(
                paper_content.extracted_text,
            )
        )

        saved_summary = PaperSummary(
            paper_id=paper.id,
            paper_title=(
                generated_summary.paper_title
            ),
            plain_language_summary=(
                generated_summary
                .plain_language_summary
            ),
            research_problem=(
                generated_summary.research_problem
            ),
            methodology=(
                generated_summary.methodology
            ),
            key_findings=(
                generated_summary.key_findings
            ),
            limitations=(
                generated_summary.limitations
            ),
            future_work=(
                generated_summary.future_work
            ),
            keywords=generated_summary.keywords,
            model_name=model_name,
        )

        paper.processing_status = "summarized"

        db.add(saved_summary)
        db.commit()
        db.refresh(saved_summary)

        return create_summary_response(
            paper,
            saved_summary,
        )

    except AIServiceError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        )

    except IntegrityError:
        db.rollback()

        existing_summary = db.scalar(
            select(PaperSummary).where(
                PaperSummary.paper_id == paper.id,
            )
        )

        if existing_summary is not None:
            return create_summary_response(
                paper,
                existing_summary,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A summary for this paper "
                "already exists."
            ),
        )

    except Exception as error:
        db.rollback()

        print(
            "Summary storage error:",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The AI summary could not be saved."
            ),
        )


# =========================================================
# Read stored AI summary
# =========================================================

@app.get(
    "/papers/{paper_id}/summary",
    response_model=PaperSummaryResponse,
)
def read_paper_summary(
    paper_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns a previously generated summary.
    """

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    summary = db.scalar(
        select(PaperSummary).where(
            PaperSummary.paper_id == paper.id,
        )
    )

    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No AI summary has been generated "
                "for this paper."
            ),
        )

    return create_summary_response(
        paper,
        summary,
    )


# =========================================================
# Generate level-based explanation
# =========================================================

@app.post(
    "/papers/{paper_id}/explanations",
    response_model=PaperExplanationResponse,
)
def generate_explanation(
    paper_id: int,
    request_data: PaperExplanationRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Generates a beginner, intermediate, or expert
    paper explanation.
    """

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    level = request_data.level

    existing_explanation = db.scalar(
        select(PaperExplanation).where(
            PaperExplanation.paper_id == paper.id,
            PaperExplanation.level == level,
        )
    )

    if existing_explanation is not None:
        return create_explanation_response(
            paper,
            existing_explanation,
        )

    paper_content = get_ready_paper_content(
        paper,
        db,
    )

    try:
        generated_explanation, model_name = (
            generate_level_explanation(
                paper_content.extracted_text,
                level,
            )
        )

        saved_explanation = PaperExplanation(
            paper_id=paper.id,
            level=level,
            explanation_title=(
                generated_explanation
                .explanation_title
            ),
            explanation_text=(
                generated_explanation.explanation
            ),
            key_concepts=(
                generated_explanation.key_concepts
            ),
            glossary=[
                item.model_dump()
                for item
                in generated_explanation.glossary
            ],
            study_takeaways=(
                generated_explanation
                .study_takeaways
            ),
            model_name=model_name,
        )

        db.add(saved_explanation)
        db.commit()
        db.refresh(saved_explanation)

        return create_explanation_response(
            paper,
            saved_explanation,
        )

    except AIServiceError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        )

    except IntegrityError:
        db.rollback()

        existing_explanation = db.scalar(
            select(PaperExplanation).where(
                PaperExplanation.paper_id == paper.id,
                PaperExplanation.level == level,
            )
        )

        if existing_explanation is not None:
            return create_explanation_response(
                paper,
                existing_explanation,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This explanation already exists."
            ),
        )

    except Exception as error:
        db.rollback()

        print(
            "Explanation storage error:",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The explanation could not be saved."
            ),
        )


# =========================================================
# Read saved level-based explanation
# =========================================================

@app.get(
    "/papers/{paper_id}/explanations/{level}",
    response_model=PaperExplanationResponse,
)
def read_paper_explanation(
    paper_id: int,
    level: str,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns a saved level-based explanation.
    """

    normalized_level = (
        level.strip().lower()
    )

    valid_levels = {
        "beginner",
        "intermediate",
        "expert",
    }

    if normalized_level not in valid_levels:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Level must be beginner, "
                "intermediate, or expert."
            ),
        )

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    explanation = db.scalar(
        select(PaperExplanation).where(
            PaperExplanation.paper_id == paper.id,
            PaperExplanation.level == normalized_level,
        )
    )

    if explanation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No explanation has been generated "
                "for this level."
            ),
        )

    return create_explanation_response(
        paper,
        explanation,
    )


# =========================================================
# Ask a question about a paper
# =========================================================

@app.post(
    "/papers/{paper_id}/chat",
    response_model=PaperChatResponse,
)
def ask_paper_question(
    paper_id: int,
    request_data: PaperChatRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Answers a question using semantic retrieval over
    the authenticated user's research paper.
    """

    question = (
        request_data.question
        .strip()
    )

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    paper_content = get_ready_paper_content(
        paper,
        db,
    )

    try:
        stored_chunks = get_or_create_paper_chunks(
            paper,
            paper_content,
            db,
        )

        indexed_chunks = [
            IndexedChunk(
                chunk_index=chunk.chunk_index,
                text=chunk.chunk_text,
                embedding=[
                    float(value)
                    for value in chunk.embedding
                ],
            )
            for chunk in stored_chunks
        ]

        retrieved_chunks = (
            retrieve_relevant_chunks(
                question,
                indexed_chunks,
            )
        )

        recent_messages = list(
            db.scalars(
                select(PaperChatMessage)
                .where(
                    PaperChatMessage.paper_id
                    == paper.id,
                )
                .order_by(
                    PaperChatMessage.created_at.desc(),
                    PaperChatMessage.id.desc(),
                )
                .limit(6)
            ).all()
        )

        recent_messages.reverse()

        history = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in recent_messages
        ]

        generated_answer, model_name = (
            generate_rag_answer(
                question,
                retrieved_chunks,
                history,
            )
        )

        sources = [
            {
                "chunk_index": chunk.chunk_index,
                "excerpt": create_source_excerpt(
                    chunk.text,
                ),
            }
            for chunk in retrieved_chunks
        ]

        user_message = PaperChatMessage(
            paper_id=paper.id,
            role="user",
            content=question,
            source_chunks=[],
            model_name=None,
        )

        assistant_message = PaperChatMessage(
            paper_id=paper.id,
            role="assistant",
            content=generated_answer.answer,
            source_chunks=sources,
            model_name=model_name,
        )

        db.add(user_message)
        db.add(assistant_message)

        db.commit()
        db.refresh(assistant_message)

        return {
            "paper_id": paper.id,
            "question": question,
            "answer": generated_answer.answer,
            "sources": sources,
            "model_name": model_name,
            "created_at": assistant_message.created_at,
        }

    except RAGServiceError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        )

    except Exception as error:
        db.rollback()

        print(
            "Paper chat error:",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "PaperMind could not answer "
                "this question."
            ),
        )


# =========================================================
# Read paper-chat history
# =========================================================

@app.get(
    "/papers/{paper_id}/chat",
    response_model=list[
        PaperChatHistoryMessageResponse
    ],
)
def read_paper_chat_history(
    paper_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns saved user and assistant messages for
    one research paper.
    """

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    messages = db.scalars(
        select(PaperChatMessage)
        .where(
            PaperChatMessage.paper_id == paper.id,
        )
        .order_by(
            PaperChatMessage.created_at.asc(),
            PaperChatMessage.id.asc(),
        )
    ).all()

    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "sources": (
                message.source_chunks
                if message.role == "assistant"
                else []
            ),
            "model_name": message.model_name,
            "created_at": message.created_at,
        }
        for message in messages
    ]


# =========================================================
# Generate paper comparison
# =========================================================

@app.post(
    "/comparisons",
    response_model=PaperComparisonResponse,
)
def compare_research_papers(
    request_data: PaperComparisonRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Compares two papers owned by the authenticated
    user using their saved structured summaries.
    """

    if (
        request_data.paper_a_id
        == request_data.paper_b_id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Select two different research papers."
            ),
        )

    # Preserve the exact order selected by the user.
    # Paper A stays Paper A and Paper B stays Paper B.
    paper_a_id = request_data.paper_a_id
    paper_b_id = request_data.paper_b_id

    paper_a = get_owned_paper(
        paper_a_id,
        current_user,
        db,
    )

    paper_b = get_owned_paper(
        paper_b_id,
        current_user,
        db,
    )

    summary_a = get_paper_summary_or_error(
        paper_a,
        db,
    )

    summary_b = get_paper_summary_or_error(
        paper_b,
        db,
    )

    existing_comparison = db.scalar(
        select(PaperComparison).where(
            PaperComparison.user_id
            == current_user.id,
            PaperComparison.paper_a_id
            == paper_a.id,
            PaperComparison.paper_b_id
            == paper_b.id,
        )
    )

    if existing_comparison is not None:
        return create_comparison_response(
            existing_comparison,
            paper_a,
            summary_a,
            paper_b,
            summary_b,
        )

    try:
        generated_comparison, model_name = (
            generate_paper_comparison(
                create_summary_context(
                    paper_a,
                    summary_a,
                ),
                create_summary_context(
                    paper_b,
                    summary_b,
                ),
            )
        )

        comparison = PaperComparison(
            user_id=current_user.id,
            paper_a_id=paper_a.id,
            paper_b_id=paper_b.id,
            comparison_title=(
                generated_comparison
                .comparison_title
            ),
            overview=generated_comparison.overview,
            similarities=(
                generated_comparison.similarities
            ),
            differences=(
                generated_comparison.differences
            ),
            research_problem_comparison=(
                generated_comparison
                .research_problem_comparison
            ),
            methodology_comparison=(
                generated_comparison
                .methodology_comparison
            ),
            findings_comparison=(
                generated_comparison
                .findings_comparison
            ),
            limitations_comparison=(
                generated_comparison
                .limitations_comparison
            ),
            practical_guidance=(
                generated_comparison
                .practical_guidance
            ),
            model_name=model_name,
        )

        db.add(comparison)
        db.commit()
        db.refresh(comparison)

        return create_comparison_response(
            comparison,
            paper_a,
            summary_a,
            paper_b,
            summary_b,
        )

    except AIServiceError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        )

    except IntegrityError:
        db.rollback()

        existing_comparison = db.scalar(
            select(PaperComparison).where(
                PaperComparison.user_id
                == current_user.id,
                PaperComparison.paper_a_id
                == paper_a.id,
                PaperComparison.paper_b_id
                == paper_b.id,
            )
        )

        if existing_comparison is not None:
            return create_comparison_response(
                existing_comparison,
                paper_a,
                summary_a,
                paper_b,
                summary_b,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This paper comparison already exists."
            ),
        )

    except Exception as error:
        db.rollback()

        print(
            "Comparison storage error:",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The paper comparison could not be saved."
            ),
        )


# =========================================================
# List saved paper comparisons
# =========================================================

@app.get(
    "/comparisons",
    response_model=list[
        PaperComparisonResponse
    ],
)
def list_paper_comparisons(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns the authenticated user's saved
    paper comparisons.
    """

    comparisons = db.scalars(
        select(PaperComparison)
        .where(
            PaperComparison.user_id
            == current_user.id,
        )
        .order_by(
            PaperComparison.generated_at.desc(),
        )
    ).all()

    responses: list[dict] = []

    for comparison in comparisons:
        paper_a = db.scalar(
            select(Paper).where(
                Paper.id == comparison.paper_a_id,
                Paper.user_id == current_user.id,
            )
        )

        paper_b = db.scalar(
            select(Paper).where(
                Paper.id == comparison.paper_b_id,
                Paper.user_id == current_user.id,
            )
        )

        if paper_a is None or paper_b is None:
            continue

        summary_a = db.scalar(
            select(PaperSummary).where(
                PaperSummary.paper_id == paper_a.id,
            )
        )

        summary_b = db.scalar(
            select(PaperSummary).where(
                PaperSummary.paper_id == paper_b.id,
            )
        )

        if summary_a is None or summary_b is None:
            continue

        responses.append(
            create_comparison_response(
                comparison,
                paper_a,
                summary_a,
                paper_b,
                summary_b,
            )
        )

    return responses


# =========================================================
# Read one saved paper comparison
# =========================================================

@app.get(
    "/comparisons/{comparison_id}",
    response_model=PaperComparisonResponse,
)
def read_paper_comparison(
    comparison_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns one saved paper comparison owned
    by the authenticated user.
    """

    comparison = db.scalar(
        select(PaperComparison).where(
            PaperComparison.id == comparison_id,
            PaperComparison.user_id
            == current_user.id,
        )
    )

    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper comparison not found.",
        )

    paper_a = get_owned_paper(
        comparison.paper_a_id,
        current_user,
        db,
    )

    paper_b = get_owned_paper(
        comparison.paper_b_id,
        current_user,
        db,
    )

    summary_a = get_paper_summary_or_error(
        paper_a,
        db,
    )

    summary_b = get_paper_summary_or_error(
        paper_b,
        db,
    )

    return create_comparison_response(
        comparison,
        paper_a,
        summary_a,
        paper_b,
        summary_b,
    )

# =========================================================
# Generate AI research roadmap
# =========================================================

@app.post(
    "/papers/{paper_id}/roadmap",
    response_model=PaperRoadmapResponse,
)
def generate_paper_roadmap(
    paper_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Generates and saves a personalized learning and
    research roadmap for one research paper.
    """

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    existing_roadmap = db.scalar(
        select(PaperRoadmap).where(
            PaperRoadmap.paper_id == paper.id,
        )
    )

    if existing_roadmap is not None:
        return create_roadmap_response(
            paper,
            existing_roadmap,
        )

    summary = get_paper_summary_or_error(
        paper,
        db,
    )

    try:
        generated_roadmap, model_name = (
            generate_research_roadmap(
                create_roadmap_context(
                    paper,
                    summary,
                )
            )
        )

        roadmap_steps = [
            step.model_dump()
            for step in generated_roadmap.roadmap_steps
        ]

        roadmap = PaperRoadmap(
            paper_id=paper.id,
            roadmap_title=(
                generated_roadmap.roadmap_title
            ),
            research_domain=(
                generated_roadmap.research_domain
            ),
            overview=generated_roadmap.overview,
            prerequisites=(
                generated_roadmap.prerequisites
            ),
            roadmap_steps=roadmap_steps,
            research_directions=(
                generated_roadmap.research_directions
            ),
            suggested_projects=(
                generated_roadmap.suggested_projects
            ),
            model_name=model_name,
        )

        db.add(roadmap)
        db.commit()
        db.refresh(roadmap)

        return create_roadmap_response(
            paper,
            roadmap,
        )

    except AIServiceError as error:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        )

    except IntegrityError:
        db.rollback()

        existing_roadmap = db.scalar(
            select(PaperRoadmap).where(
                PaperRoadmap.paper_id == paper.id,
            )
        )

        if existing_roadmap is not None:
            return create_roadmap_response(
                paper,
                existing_roadmap,
            )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A research roadmap for this "
                "paper already exists."
            ),
        )

    except Exception as error:
        db.rollback()

        print(
            "Research roadmap storage error:",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The research roadmap could not "
                "be saved."
            ),
        )


# =========================================================
# Read saved AI research roadmap
# =========================================================

@app.get(
    "/papers/{paper_id}/roadmap",
    response_model=PaperRoadmapResponse,
)
def read_paper_roadmap(
    paper_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns a previously generated research roadmap.
    """

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )

    roadmap = db.scalar(
        select(PaperRoadmap).where(
            PaperRoadmap.paper_id == paper.id,
        )
    )

    if roadmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No research roadmap has been "
                "generated for this paper."
            ),
        )

    return create_roadmap_response(
        paper,
        roadmap,
    )

# =========================================================
# Extract citation metadata
# =========================================================

@app.post(
    "/papers/{paper_id}/citation/metadata",
    response_model=PaperCitationMetadataResponse,
)
def generate_paper_citation_metadata(
    paper_id: int,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Extracts and saves bibliographic metadata for
    one research paper.

    Existing saved metadata is returned instead of
    making another AI request.
    """

    # -----------------------------------------------------
    # Verify paper ownership
    # -----------------------------------------------------

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )


    # -----------------------------------------------------
    # Return existing metadata when already extracted
    # -----------------------------------------------------

    existing_citation = db.scalar(
        select(PaperCitation).where(
            PaperCitation.paper_id
            == paper.id,
        )
    )

    if existing_citation is not None:

        return create_citation_metadata_response(
            paper,
            existing_citation,
        )


    # -----------------------------------------------------
    # Citation extraction requires readable paper text
    # -----------------------------------------------------

    paper_content = get_ready_paper_content(
        paper,
        db,
    )


    try:

        # -------------------------------------------------
        # Extract metadata using AI
        # -------------------------------------------------

        generated_metadata, model_name = (
            extract_citation_metadata(
                paper_content.extracted_text
            )
        )


        # -------------------------------------------------
        # Save metadata
        # -------------------------------------------------

        citation = PaperCitation(
            paper_id=paper.id,

            title=(
                generated_metadata.title
            ),

            authors=(
                generated_metadata.authors
            ),

            publication_year=(
                generated_metadata
                .publication_year
            ),

            journal_or_conference=(
                generated_metadata
                .journal_or_conference
            ),

            publisher=(
                generated_metadata.publisher
            ),

            volume=(
                generated_metadata.volume
            ),

            issue=(
                generated_metadata.issue
            ),

            pages=(
                generated_metadata.pages
            ),

            doi=(
                generated_metadata.doi
            ),

            url=(
                generated_metadata.url
            ),

            document_type=(
                generated_metadata.document_type
            ),

            is_academic_publication=(
                generated_metadata
                .is_academic_publication
            ),

            citation_warning=(
                generated_metadata
                .citation_warning
            ),

            missing_fields=(
                generated_metadata
                .missing_fields
            ),

            model_name=(
                model_name
            ),
        )


        db.add(citation)

        db.commit()

        db.refresh(citation)


        return create_citation_metadata_response(
            paper,
            citation,
        )


    # -----------------------------------------------------
    # AI extraction error
    # -----------------------------------------------------

    except AIServiceError as error:

        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),

            detail=str(error),
        )


    # -----------------------------------------------------
    # Duplicate race protection
    # -----------------------------------------------------

    except IntegrityError:

        db.rollback()

        existing_citation = db.scalar(
            select(PaperCitation).where(
                PaperCitation.paper_id
                == paper.id,
            )
        )

        if existing_citation is not None:

            return create_citation_metadata_response(
                paper,
                existing_citation,
            )


        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),

            detail=(
                "Citation metadata for this "
                "paper already exists."
            ),
        )


    # -----------------------------------------------------
    # Unexpected error
    # -----------------------------------------------------

    except Exception as error:

        db.rollback()

        print(
            "Citation metadata storage error:",
            type(error).__name__,
            str(error),
        )

        raise HTTPException(
            status_code=(
                status
                .HTTP_500_INTERNAL_SERVER_ERROR
            ),

            detail=(
                "The citation metadata could "
                "not be saved."
            ),
        )
    # =========================================================
# Read saved citation metadata
# =========================================================

@app.get(
    "/papers/{paper_id}/citation/metadata",
    response_model=PaperCitationMetadataResponse,
)
def read_paper_citation_metadata(
    paper_id: int,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Returns previously extracted citation metadata.
    """

    # -----------------------------------------------------
    # Verify ownership
    # -----------------------------------------------------

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )


    # -----------------------------------------------------
    # Load metadata
    # -----------------------------------------------------

    citation = db.scalar(
        select(PaperCitation).where(
            PaperCitation.paper_id
            == paper.id,
        )
    )


    if citation is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail=(
                "No citation metadata has been "
                "extracted for this paper."
            ),
        )


    return create_citation_metadata_response(
        paper,
        citation,
    )

# =========================================================
# Generate formatted citations
# =========================================================

@app.get(
    "/papers/{paper_id}/citations",
    response_model=(
        PaperFormattedCitationsResponse
    ),
)
def read_formatted_paper_citations(
    paper_id: int,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        Session,
        Depends(get_db),
    ],
):
    """
    Generates formatted citations from previously
    extracted bibliographic metadata.

    No AI request is made here.
    """

    # -----------------------------------------------------
    # Verify ownership
    # -----------------------------------------------------

    paper = get_owned_paper(
        paper_id,
        current_user,
        db,
    )


    # -----------------------------------------------------
    # Load saved citation metadata
    # -----------------------------------------------------

    citation = db.scalar(
        select(PaperCitation).where(
            PaperCitation.paper_id
            == paper.id,
        )
    )


    if citation is None:

        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),

            detail=(
                "Citation metadata has not "
                "been extracted for this paper."
            ),
        )


    # -----------------------------------------------------
    # Generate deterministic citations
    # -----------------------------------------------------

    formatted = generate_all_citations(
        create_citation_formatter_metadata(
            citation
        )
    )


    return {
        "paper_id":
            paper.id,

        "original_filename":
            paper.original_filename,

        "document_type":
            citation.document_type,

        "is_academic_publication":
            (
                citation
                .is_academic_publication
            ),

        "citation_warning":
            citation.citation_warning,

        "apa":
            formatted["apa"],

        "mla":
            formatted["mla"],

        "ieee":
            formatted["ieee"],

        "chicago":
            formatted["chicago"],

        "harvard":
            formatted["harvard"],

        "bibtex":
            formatted["bibtex"],
    }