from datetime import datetime
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


class UserCreate(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class PaperResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    original_filename: str
    file_size: int
    processing_status: str
    uploaded_at: datetime


class PaperTextResponse(BaseModel):
    paper_id: int
    original_filename: str
    processing_status: str
    extraction_status: str
    page_count: int
    character_count: int
    extracted_text: str

class PaperSummaryResponse(BaseModel):
    paper_id: int
    original_filename: str

    paper_title: str
    plain_language_summary: str
    research_problem: str
    methodology: str

    key_findings: list[str]
    limitations: list[str]
    future_work: list[str]
    keywords: list[str]

    model_name: str
    generated_at: datetime

# =========================================================
# Level-based explanation schemas
# =========================================================

class PaperExplanationRequest(BaseModel):
    level: Literal[
        "beginner",
        "intermediate",
        "expert",
    ]


class ExplanationGlossaryItemResponse(BaseModel):
    term: str
    meaning: str


class PaperExplanationResponse(BaseModel):
    paper_id: int
    original_filename: str

    level: str
    explanation_title: str
    explanation: str

    key_concepts: list[str]

    glossary: list[
        ExplanationGlossaryItemResponse
    ]

    study_takeaways: list[str]

    model_name: str
    generated_at: datetime

# =========================================================
# Paper RAG chat schemas
# =========================================================

class PaperChatRequest(BaseModel):
    question: str = Field(
        min_length=2,
        max_length=1000,
    )


class PaperChatSourceResponse(BaseModel):
    chunk_index: int
    excerpt: str


class PaperChatResponse(BaseModel):
    paper_id: int
    question: str
    answer: str

    sources: list[
        PaperChatSourceResponse
    ]

    model_name: str
    created_at: datetime


class PaperChatHistoryMessageResponse(BaseModel):
    id: int
    role: str
    content: str

    sources: list[
        PaperChatSourceResponse
    ]

    model_name: str | None
    created_at: datetime

# =========================================================
# Paper-comparison schemas
# =========================================================

class PaperComparisonRequest(BaseModel):
    paper_a_id: int = Field(
        gt=0,
    )

    paper_b_id: int = Field(
        gt=0,
    )


class PaperComparisonResponse(BaseModel):
    id: int

    paper_a_id: int
    paper_a_filename: str
    paper_a_title: str

    paper_b_id: int
    paper_b_filename: str
    paper_b_title: str

    comparison_title: str
    overview: str

    similarities: list[str]
    differences: list[str]

    research_problem_comparison: str
    methodology_comparison: str
    findings_comparison: str
    limitations_comparison: str
    practical_guidance: str

    model_name: str
    generated_at: datetime

# =========================================================
# Research-roadmap schemas
# =========================================================

class RoadmapStepResponse(BaseModel):
    stage: int

    title: str

    goal: str

    topics: list[str]


class PaperRoadmapResponse(BaseModel):
    paper_id: int

    original_filename: str

    roadmap_title: str

    research_domain: str

    overview: str

    prerequisites: list[str]

    roadmap_steps: list[
        RoadmapStepResponse
    ]

    research_directions: list[str]

    suggested_projects: list[str]

    model_name: str

    generated_at: datetime

# =========================================================
# Citation Generator schemas
# =========================================================

class PaperCitationMetadataResponse(
    BaseModel
):
    paper_id: int

    original_filename: str

    title: str

    authors: list[str]

    publication_year: int | None

    journal_or_conference: (
        str | None
    )

    publisher: str | None

    volume: str | None

    issue: str | None

    pages: str | None

    doi: str | None

    url: str | None

    document_type: str | None

    is_academic_publication: (
        bool | None
    )

    citation_warning: str | None

    missing_fields: list[str]

    model_name: str

    extracted_at: datetime

# =========================================================
# Formatted citation response
# =========================================================

class PaperFormattedCitationsResponse(
    BaseModel
):
    paper_id: int

    original_filename: str

    document_type: str | None

    is_academic_publication: (
        bool | None
    )

    citation_warning: str | None

    apa: str

    mla: str

    ieee: str

    chicago: str

    harvard: str

    bibtex: str