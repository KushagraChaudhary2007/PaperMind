import os
import json
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()


DEFAULT_MODEL = "gemini-3.5-flash"

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    DEFAULT_MODEL,
)

MAX_SUMMARY_CHARACTERS = 180_000


class AIServiceError(Exception):
    """
    Raised when PaperMind cannot generate an AI response.
    """


class GeneratedPaperSummary(BaseModel):
    """
    Structure that Gemini must follow when analysing
    a research paper.
    """

    paper_title: str = Field(
        description=(
            "The title of the research paper. "
            "Use the title stated in the paper."
        )
    )

    plain_language_summary: str = Field(
        description=(
            "A clear summary understandable by a "
            "college student, without unnecessary jargon."
        )
    )

    research_problem: str = Field(
        description=(
            "The main research problem or question "
            "addressed by the paper."
        )
    )

    methodology: str = Field(
        description=(
            "The methods, models, experiments, datasets, "
            "or procedures used by the researchers."
        )
    )

    key_findings: list[str] = Field(
        description=(
            "The most important results or conclusions "
            "from the paper."
        )
    )

    limitations: list[str] = Field(
        description=(
            "Limitations explicitly stated or clearly "
            "supported by the paper."
        )
    )

    future_work: list[str] = Field(
        description=(
            "Future research directions stated or "
            "strongly suggested by the paper."
        )
    )

    keywords: list[str] = Field(
        description=(
            "Five to twelve important technical keywords "
            "representing the paper."
        )
    )


def prepare_paper_text(
    extracted_text: str,
) -> str:
    """
    Limits very large papers while retaining material
    from both the beginning and ending sections.
    """

    cleaned_text = extracted_text.strip()

    if len(cleaned_text) <= MAX_SUMMARY_CHARACTERS:
        return cleaned_text

    beginning_length = 120_000
    ending_length = 60_000

    beginning = cleaned_text[:beginning_length]
    ending = cleaned_text[-ending_length:]

    return (
        f"{beginning}\n\n"
        "[... middle section shortened for the initial "
        "summary process ...]\n\n"
        f"{ending}"
    )


def generate_paper_summary(
    extracted_text: str,
) -> tuple[GeneratedPaperSummary, str]:
    """
    Sends paper text to Gemini and returns a validated,
    structured summary.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise AIServiceError(
            "GEMINI_API_KEY was not found in Backend/.env."
        )

    prepared_text = prepare_paper_text(
        extracted_text
    )

    if not prepared_text:
        raise AIServiceError(
            "The research paper has no extracted text."
        )

    prompt = f"""
You are PaperMind, an academic research-paper analysis
assistant.

Analyse only the research-paper text supplied below.

Important rules:

1. Do not invent information.
2. Do not use outside knowledge.
3. If something is not clearly available in the paper,
   write "Not clearly stated in the paper."
4. Keep the plain-language summary understandable for
   a college student.
5. Preserve technical accuracy.
6. Key findings, limitations, future work, and keywords
   must be concise lists.
7. Avoid claiming that correlation proves causation.
8. Do not treat references cited by the paper as findings
   made by the paper itself.

RESEARCH PAPER TEXT START

{prepared_text}

RESEARCH PAPER TEXT END
""".strip()

    client = genai.Client(
        api_key=api_key
    )

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": (
                    GeneratedPaperSummary
                    .model_json_schema()
                ),
            },
        )

        if not interaction.output_text:
            raise AIServiceError(
                "Gemini returned an empty response."
            )

        generated_summary = (
            GeneratedPaperSummary
            .model_validate_json(
                interaction.output_text
            )
        )

        return generated_summary, MODEL_NAME

    except AIServiceError:
        raise

    except Exception as error:
        raise AIServiceError(
            "PaperMind could not generate the AI summary."
        ) from error

    finally:
        client.close()

# =========================================================
# Level-based explanation generation
# =========================================================

class ExplanationGlossaryItem(BaseModel):
    term: str = Field(
        description=(
            "A technical term used in the paper."
        )
    )

    meaning: str = Field(
        description=(
            "A clear meaning of the technical term "
            "based only on the paper."
        )
    )


class GeneratedLevelExplanation(BaseModel):
    explanation_title: str = Field(
        description=(
            "A short descriptive title for the "
            "level-based explanation."
        )
    )

    explanation: str = Field(
        description=(
            "The main explanation written for the "
            "requested understanding level."
        )
    )

    key_concepts: list[str] = Field(
        description=(
            "The most important concepts that the "
            "reader should understand."
        )
    )

    glossary: list[
        ExplanationGlossaryItem
    ] = Field(
        description=(
            "Important technical terms and their "
            "clear meanings."
        )
    )

    study_takeaways: list[str] = Field(
        description=(
            "Short revision points the reader should "
            "remember after studying the explanation."
        )
    )


EXPLANATION_LEVEL_GUIDANCE = {
    "beginner": """
Write for a beginner who has little background in the
subject.

Use:
- simple vocabulary
- short paragraphs
- easy examples or analogies
- explanations for technical terms and abbreviations

Avoid unexplained jargon and unnecessary mathematical
detail.
""".strip(),

    "intermediate": """
Write for a B.Tech or undergraduate student who knows
basic programming, mathematics, and machine learning.

Use:
- important academic terminology
- clear explanations of the methodology
- meaningful technical detail
- explanations of the main results

Do not oversimplify the paper.
""".strip(),

    "expert": """
Write for an advanced student, researcher, or technical
professional.

Use:
- precise research terminology
- detailed methodology
- assumptions and technical mechanisms
- model, dataset, experiment, and evaluation details
- technically accurate discussion of the findings

Do not remove important complexity.
""".strip(),
}


def generate_level_explanation(
    extracted_text: str,
    level: str,
) -> tuple[GeneratedLevelExplanation, str]:
    """
    Generates a paper explanation for beginner,
    intermediate, or expert level.
    """

    normalized_level = (
        level
        .strip()
        .lower()
    )

    if (
        normalized_level
        not in EXPLANATION_LEVEL_GUIDANCE
    ):
        raise AIServiceError(
            "Invalid explanation level."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise AIServiceError(
            "GEMINI_API_KEY was not found in Backend/.env."
        )

    prepared_text = prepare_paper_text(
        extracted_text
    )

    if not prepared_text:
        raise AIServiceError(
            "The research paper has no extracted text."
        )

    level_guidance = (
        EXPLANATION_LEVEL_GUIDANCE[
            normalized_level
        ]
    )

    prompt = f"""
You are PaperMind, an academic research-paper teaching
assistant.

Explain the supplied research paper at the following
understanding level:

LEVEL: {normalized_level.upper()}

LEVEL INSTRUCTIONS:

{level_guidance}

Important rules:

1. Use only information found in the supplied paper.
2. Do not invent findings, datasets, results, or claims.
3. Clearly distinguish the paper's contribution from
   information mentioned in its references.
4. When information is unavailable, say:
   "Not clearly stated in the paper."
5. Preserve the meaning and conclusions of the paper.
6. The glossary must contain useful technical terms.
7. Study takeaways must be concise and useful for revision.
8. Do not claim that correlation proves causation.

RESEARCH PAPER TEXT START

{prepared_text}

RESEARCH PAPER TEXT END
""".strip()

    client = genai.Client(
        api_key=api_key
    )

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": (
                    GeneratedLevelExplanation
                    .model_json_schema()
                ),
            },
        )

        if not interaction.output_text:
            raise AIServiceError(
                "Gemini returned an empty explanation."
            )

        explanation = (
            GeneratedLevelExplanation
            .model_validate_json(
                interaction.output_text
            )
        )

        return explanation, MODEL_NAME

    except AIServiceError:
        raise

    except Exception as error:
        raise AIServiceError(
            "PaperMind could not generate the explanation."
        ) from error

    finally:
        client.close()

# =========================================================
# AI paper-comparison generation
# =========================================================

class GeneratedPaperComparison(BaseModel):
    comparison_title: str = Field(
        description=(
            "A concise title describing the comparison."
        )
    )

    overview: str = Field(
        description=(
            "A clear overall comparison of the two "
            "research papers."
        )
    )

    similarities: list[str] = Field(
        description=(
            "Important similarities between the papers."
        )
    )

    differences: list[str] = Field(
        description=(
            "Important differences between the papers."
        )
    )

    research_problem_comparison: str = Field(
        description=(
            "Comparison of the research problems or "
            "questions addressed by both papers."
        )
    )

    methodology_comparison: str = Field(
        description=(
            "Comparison of the methods, models, datasets, "
            "experiments, and procedures."
        )
    )

    findings_comparison: str = Field(
        description=(
            "Comparison of the main findings and "
            "conclusions."
        )
    )

    limitations_comparison: str = Field(
        description=(
            "Comparison of the limitations of both papers."
        )
    )

    practical_guidance: str = Field(
        description=(
            "Explain when each paper is more useful "
            "for a student, researcher, or practitioner."
        )
    )


def generate_paper_comparison(
    paper_a: dict,
    paper_b: dict,
) -> tuple[GeneratedPaperComparison, str]:
    """
    Generates a structured comparison using two
    previously saved paper summaries.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise AIServiceError(
            "GEMINI_API_KEY was not found in Backend/.env."
        )

    paper_a_json = json.dumps(
        paper_a,
        ensure_ascii=False,
        indent=2,
    )

    paper_b_json = json.dumps(
        paper_b,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are PaperMind, an academic research-paper comparison
assistant.

Compare the two structured research-paper analyses below.

Important rules:

1. Use only the supplied information.
2. Do not invent results, datasets, methods, limitations,
   or conclusions.
3. Clearly identify which statement relates to Paper A
   and which relates to Paper B.
4. Explain similarities and differences accurately.
5. Avoid declaring one paper universally better.
6. Practical guidance should explain when each paper is
   more useful.
7. When information is unavailable, write:
   "Not clearly stated in the available paper analysis."

PAPER A

{paper_a_json}

PAPER B

{paper_b_json}
""".strip()

    client = genai.Client(
        api_key=api_key
    )

    try:
        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": (
                    GeneratedPaperComparison
                    .model_json_schema()
                ),
            },
        )

        if not interaction.output_text:
            raise AIServiceError(
                "Gemini returned an empty comparison."
            )

        comparison = (
            GeneratedPaperComparison
            .model_validate_json(
                interaction.output_text
            )
        )

        return comparison, MODEL_NAME

    except AIServiceError:
        raise

    except Exception as error:
        print(
            "Paper comparison error:",
            type(error).__name__,
            str(error),
        )

        raise AIServiceError(
            "PaperMind could not compare these papers."
        ) from error

    finally:
        client.close()

# =========================================================
# AI research-roadmap generation
# =========================================================

class GeneratedRoadmapStep(BaseModel):
    stage: int = Field(
        description=(
            "The numerical learning stage, "
            "starting from 1."
        )
    )

    title: str = Field(
        description=(
            "A short descriptive title "
            "for this learning stage."
        )
    )

    goal: str = Field(
        description=(
            "Explain what the learner should "
            "understand or achieve in this stage."
        )
    )

    topics: list[str] = Field(
        description=(
            "The important concepts, technologies, "
            "methods, or topics to study."
        )
    )


class GeneratedPaperRoadmap(BaseModel):
    roadmap_title: str = Field(
        description=(
            "A concise personalized title for "
            "the research learning roadmap."
        )
    )

    research_domain: str = Field(
        description=(
            "The main academic or technical domain "
            "of the research paper."
        )
    )

    overview: str = Field(
        description=(
            "A concise explanation of how this "
            "roadmap helps someone understand and "
            "continue learning from the paper."
        )
    )

    prerequisites: list[str] = Field(
        description=(
            "Essential knowledge or skills someone "
            "should learn before studying this topic."
        )
    )

    roadmap_steps: list[
        GeneratedRoadmapStep
    ] = Field(
        description=(
            "A sequential learning roadmap from "
            "foundational concepts to advanced topics."
        )
    )

    research_directions: list[str] = Field(
        description=(
            "Promising research questions or future "
            "directions related to the paper."
        )
    )

    suggested_projects: list[str] = Field(
        description=(
            "Practical project ideas that help a "
            "student learn or experiment with the "
            "paper's concepts."
        )
    )
    

def generate_research_roadmap(
    paper_context: dict,
) -> tuple[
    GeneratedPaperRoadmap,
    str,
]:
    """
    Generates a personalized research learning roadmap
    from an existing structured paper analysis.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise AIServiceError(
            (
                "GEMINI_API_KEY was not found "
                "in Backend/.env."
            )
        )

    paper_context_json = json.dumps(
        paper_context,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
You are PaperMind, an AI research-learning assistant.

Create a personalized learning and research roadmap for
a student who wants to deeply understand the research
paper described below.

The roadmap must help the student progress from the
required prerequisites to understanding the paper,
then toward advanced research in the same field.

IMPORTANT RULES:

1. Base the roadmap only on the supplied paper analysis.

2. Do not invent specific facts about the paper that
   are not present in the supplied analysis.

3. Identify the main research domain accurately.

4. Give practical prerequisites.

5. Create approximately 4 to 6 sequential roadmap
   stages.

6. The stages should progress logically, for example:

   Stage 1:
   Required fundamentals

   Stage 2:
   Core domain knowledge

   Stage 3:
   Important methods and technologies

   Stage 4:
   Understanding the paper deeply

   Stage 5:
   Advanced concepts

   Stage 6:
   Research exploration

   Adjust this structure when appropriate for the
   actual paper.

7. Each stage should contain useful and specific topics,
   not vague phrases such as "learn more".

8. Research directions should represent realistic areas
   the learner could investigate after understanding
   the paper.

9. Suggested projects should be practical enough for a
   university student to build, reproduce, experiment
   with, or research.

10. Do not claim that every listed research direction
    was explicitly proposed by the paper. They may be
    logically related learning or research directions.

11. Keep the roadmap educational and actionable.

STRUCTURED PAPER ANALYSIS:

{paper_context_json}
""".strip()

    client = genai.Client(
        api_key=api_key,
    )

    try:
        interaction = (
            client.interactions.create(
                model=MODEL_NAME,

                input=prompt,

                response_format={
                    "type": "text",

                    "mime_type":
                        "application/json",

                    "schema": (
                        GeneratedPaperRoadmap
                        .model_json_schema()
                    ),
                },
            )
        )

        if not interaction.output_text:
            raise AIServiceError(
                (
                    "Gemini returned an empty "
                    "research roadmap."
                )
            )

        generated_roadmap = (
            GeneratedPaperRoadmap
            .model_validate_json(
                interaction.output_text
            )
        )

        # Extra safety:
        # Keep stages sorted correctly.
        generated_roadmap.roadmap_steps.sort(
            key=lambda step: step.stage
        )

        return (
            generated_roadmap,
            MODEL_NAME,
        )

    except AIServiceError:
        raise

    except Exception as error:
        print(
            "Research roadmap error:",
            type(error).__name__,
            str(error),
        )

        raise AIServiceError(
            (
                "PaperMind could not generate "
                "the research roadmap."
            )
        ) from error

    finally:
        client.close()

# =========================================================
# Citation metadata extraction
# =========================================================

class GeneratedCitationMetadata(
    BaseModel
):
    title: str = Field(
        description=(
            "The exact title of the research paper."
        )
    )

    authors: list[str] = Field(
        description=(
            "Authors explicitly listed in the paper. "
            "Return an empty list if authors cannot "
            "be confidently identified."
        )
    )

    publication_year: int | None = Field(
        default=None,

        description=(
            "Publication year only when explicitly "
            "supported by the paper."
        ),
    )

    journal_or_conference: str | None = Field(
        default=None,

        description=(
            "Journal, conference, proceedings, "
            "repository, or publication venue when "
            "explicitly stated."
        ),
    )

    publisher: str | None = Field(
        default=None,

        description=(
            "Publisher when explicitly stated."
        ),
    )

    volume: str | None = Field(
        default=None,

        description=(
            "Publication volume when explicitly stated."
        ),
    )

    issue: str | None = Field(
        default=None,

        description=(
            "Publication issue or number when "
            "explicitly stated."
        ),
    )

    pages: str | None = Field(
        default=None,

        description=(
            "Page range when explicitly stated."
        ),
    )

    doi: str | None = Field(
        default=None,

        description=(
            "DOI when explicitly present. "
            "Do not invent a DOI."
        ),
    )

    url: str | None = Field(
        default=None,

        description=(
            "Canonical publication URL only when "
            "explicitly present in the paper."
        ),
    )

    document_type: Literal[
        "research_article",
        "conference_paper",
        "review_paper",
        "thesis",
        "preprint",
        "book_chapter",
        "report",
        "certificate",
        "other",
    ] = Field(
        description=(
            "Classification of the uploaded "
            "document based only on evidence "
            "present in the document."
        )
    )


    is_academic_publication: bool = Field(
        description=(
            "True when the document appears to "
            "be an academic or scholarly "
            "publication suitable for standard "
            "academic citation formatting."
        )
    )


    citation_warning: str | None = Field(
        default=None,

        description=(
            "A short warning when the document "
            "is not a standard academic "
            "publication or important citation "
            "metadata is uncertain."
        ),
    )

    missing_fields: list[str] = Field(
        description=(
            "Names of important citation fields that "
            "could not be confidently determined."
        )
    )

def prepare_citation_source_text(
    extracted_text: str,
) -> str:
    """
    Selects the most useful parts of the paper for
    bibliographic metadata extraction.
    """

    cleaned_text = (
        extracted_text
        .strip()
    )

    if not cleaned_text:
        raise AIServiceError(
            (
                "The paper does not contain "
                "extractable text."
            )
        )

    maximum_characters = 30000

    if (
        len(cleaned_text)
        <= maximum_characters
    ):
        return cleaned_text


    beginning = cleaned_text[
        :24000
    ]

    ending = cleaned_text[
        -6000:
    ]

    return (
        beginning
        + "\n\n"
        + "--- ENDING SECTION ---"
        + "\n\n"
        + ending
    )

def extract_citation_metadata(
    extracted_text: str,
) -> tuple[
    GeneratedCitationMetadata,
    str,
]:
    """
    Extracts bibliographic metadata from a research
    paper without inventing missing information.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise AIServiceError(
            (
                "GEMINI_API_KEY was not found "
                "in Backend/.env."
            )
        )


    citation_source_text = (
        prepare_citation_source_text(
            extracted_text
        )
    )


    prompt = f"""
You are PaperMind's bibliographic metadata extraction
system.

Extract citation metadata from the supplied research
paper text.

CRITICAL RULES:

1. Extract only information that is explicitly present
   or can be confidently identified from the document.

2. Never invent:
   - authors
   - publication year
   - journal
   - conference
   - publisher
   - volume
   - issue
   - pages
   - DOI
   - URL

3. If a field cannot be confidently identified,
   return null.

4. For authors:
   - preserve the author's normal published name
   - do not include affiliations
   - do not include email addresses
   - do not include academic titles
   - return an empty list if authors are unclear

5. For title:
   identify the actual document title, not:
   - a section heading
   - filename
   - journal name
   - conference name

6. DOI:
   only return a DOI when it actually appears in
   the supplied document.

7. URL:
   only return a relevant publication URL when it
   appears explicitly.

8. missing_fields should list citation fields whose
   values could not be confidently determined.

9. Do not treat references cited by the paper as
   metadata belonging to this paper.

10. Pay particular attention to the first page,
    headers, footers, publication information,
    and bibliographic text.

11. Classify the document into exactly one of:

    - research_article
    - conference_paper
    - review_paper
    - thesis
    - preprint
    - book_chapter
    - report
    - certificate
    - other

12. Do not automatically assume that every uploaded
    PDF is a research paper.

13. Set is_academic_publication to false for documents
    such as:

    - certificates
    - completion records
    - invoices
    - unrelated forms
    - non-academic documents

14. Academic reports, theses, preprints, conference
    papers, and scholarly articles may have
    is_academic_publication=true when supported by
    the document.

15. If the document is not a standard academic
    publication, provide a short citation_warning.

16. Do not treat a date printed on a certificate or
    completion document as an academic publication
    year unless the document is genuinely a published
    scholarly work.

17. The classification must be based on the supplied
    document itself, not on assumptions from the
    filename.

RESEARCH PAPER TEXT:

{citation_source_text}
""".strip()


    client = genai.Client(
        api_key=api_key,
    )


    try:

        interaction = (
            client.interactions.create(
                model=MODEL_NAME,

                input=prompt,

                response_format={
                    "type": "text",

                    "mime_type":
                        "application/json",

                    "schema": (
                        GeneratedCitationMetadata
                        .model_json_schema()
                    ),
                },
            )
        )


        if not interaction.output_text:
            raise AIServiceError(
                (
                    "Gemini returned empty "
                    "citation metadata."
                )
            )


        metadata = (
            GeneratedCitationMetadata
            .model_validate_json(
                interaction.output_text
            )
        )


        metadata.title = (
            metadata.title.strip()
        )


        metadata.authors = [
            author.strip()

            for author
            in metadata.authors

            if author.strip()
        ]


        if not metadata.title:
            raise AIServiceError(
                (
                    "PaperMind could not determine "
                    "the research paper title."
                )
            )


        return (
            metadata,
            MODEL_NAME,
        )


    except AIServiceError:
        raise


    except Exception as error:

        print(
            "Citation metadata error:",
            type(error).__name__,
            str(error),
        )


        raise AIServiceError(
            (
                "PaperMind could not extract "
                "citation metadata."
            )
        ) from error


    finally:
        client.close()
    