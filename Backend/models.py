from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from database import Base


# =========================================================
# User model
# =========================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # One user can upload multiple papers.
    papers: Mapped[list["Paper"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


# =========================================================
# Research-paper model
# =========================================================

class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    processing_status: Mapped[str] = mapped_column(
        String(30),
        default="uploaded",
        nullable=False,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # User who uploaded the paper.
    owner: Mapped["User"] = relationship(
        back_populates="papers",
    )

    # One paper has one extracted-text record.
    content: Mapped[
        Optional["PaperContent"]
    ] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # One paper has at most one AI summary.
    summary: Mapped[
        Optional["PaperSummary"]
    ] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # One paper can have beginner, intermediate,
    # and expert explanations.
    explanations: Mapped[
        list["PaperExplanation"]
    ] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    # Semantic-search chunks used by RAG chat.
    chunks: Mapped[
        list["PaperChunk"]
    ] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    # Saved user and assistant chat messages.
    chat_messages: Mapped[
        list["PaperChatMessage"]
    ] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
    )

    # One paper can have one AI-generated
    # research learning roadmap.
    roadmap: Mapped[
        Optional["PaperRoadmap"]
    ] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
        uselist=False,
    )

    # One paper can have one extracted
    # bibliographic citation record.
    citation: Mapped[
        Optional["PaperCitation"]
    ] = relationship(
        back_populates="paper",
        cascade="all, delete-orphan",
        uselist=False,
    )


# =========================================================
# Extracted PDF text model
# =========================================================

class PaperContent(Base):
    __tablename__ = "paper_contents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    extracted_text: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    page_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    character_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    extraction_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="content",
    )


# =========================================================
# AI-generated paper summary model
# =========================================================

class PaperSummary(Base):
    __tablename__ = "paper_summaries"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    paper_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    plain_language_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    research_problem: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    methodology: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    key_findings: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    limitations: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    future_work: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    keywords: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="summary",
    )


# =========================================================
# Level-based AI explanation model
# =========================================================

class PaperExplanation(Base):
    __tablename__ = "paper_explanations"

    __table_args__ = (
        UniqueConstraint(
            "paper_id",
            "level",
            name="uq_paper_explanation_level",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        nullable=False,
        index=True,
    )

    level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    explanation_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    explanation_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    key_concepts: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    glossary: Mapped[list[dict]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    study_takeaways: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="explanations",
    )


# =========================================================
# RAG semantic-search chunk model
# =========================================================

class PaperChunk(Base):
    __tablename__ = "paper_chunks"

    __table_args__ = (
        UniqueConstraint(
            "paper_id",
            "chunk_index",
            name="uq_paper_chunk_index",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    embedding: Mapped[list[float]] = mapped_column(
        JSON,
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="chunks",
    )


# =========================================================
# Paper chat-history model
# =========================================================

class PaperChatMessage(Base):
    __tablename__ = "paper_chat_messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_chunks: Mapped[list[dict]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    model_name: Mapped[
        Optional[str]
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="chat_messages",
    )

    # =========================================================
# AI paper-comparison model
# =========================================================

class PaperComparison(Base):
    __tablename__ = "paper_comparisons"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "paper_a_id",
            "paper_b_id",
            name="uq_user_paper_comparison",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    paper_a_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        nullable=False,
        index=True,
    )

    paper_b_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        nullable=False,
        index=True,
    )

    comparison_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    overview: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    similarities: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    differences: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    research_problem_comparison: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )

    methodology_comparison: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    findings_comparison: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    limitations_comparison: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    practical_guidance: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

# =========================================================
# AI research-roadmap model
# =========================================================

class PaperRoadmap(Base):
    __tablename__ = "paper_roadmaps"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    roadmap_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    research_domain: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    overview: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    prerequisites: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    roadmap_steps: Mapped[list[dict]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    research_directions: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    suggested_projects: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="roadmap",
    )

    # =========================================================
# Research-paper citation metadata model
# =========================================================

class PaperCitation(Base):
    __tablename__ = "paper_citations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("papers.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    authors: Mapped[list[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    publication_year: Mapped[
        Optional[int]
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    journal_or_conference: Mapped[
        Optional[str]
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    publisher: Mapped[
        Optional[str]
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    volume: Mapped[
        Optional[str]
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    issue: Mapped[
        Optional[str]
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    pages: Mapped[
        Optional[str]
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    doi: Mapped[
        Optional[str]
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    url: Mapped[
        Optional[str]
    ] = mapped_column(
        Text,
        nullable=True,
    )

    document_type: Mapped[
        Optional[str]
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    is_academic_publication: Mapped[
        Optional[bool]
    ] = mapped_column(
        Boolean,
        nullable=True,
    )

    citation_warning: Mapped[
        Optional[str]
    ] = mapped_column(
        Text,
        nullable=True,
    )

    missing_fields: Mapped[
        list[str]
    ] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
    )

    paper: Mapped["Paper"] = relationship(
        back_populates="citation",
    )