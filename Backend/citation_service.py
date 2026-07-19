import re
from typing import Any


# =========================================================
# General helpers
# =========================================================

def clean_value(
    value: Any,
) -> str:
    """
    Converts an optional metadata value into a clean
    citation-safe string.
    """

    if value is None:
        return ""

    return str(value).strip()


def normalize_doi(
    doi: str | None,
) -> str:
    """
    Converts DOI variants into a canonical DOI URL.
    """

    value = clean_value(doi)

    if not value:
        return ""

    value = re.sub(
        r"^https?://(dx\.)?doi\.org/",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"^doi:\s*",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = value.strip()

    if not value:
        return ""

    return (
        "https://doi.org/"
        + value
    )


def get_best_link(
    metadata: dict,
) -> str:
    """
    DOI is preferred over a general URL.
    """

    doi_url = normalize_doi(
        metadata.get("doi")
    )

    if doi_url:
        return doi_url

    return clean_value(
        metadata.get("url")
    )


# =========================================================
# Author parsing helpers
# =========================================================

def parse_author_name(
    author: str,
) -> tuple[str, str]:
    """
    Returns:

    given_names,
    surname

    Supports both:

    John Michael Smith

    and

    Smith, John Michael
    """

    name = author.strip()

    if not name:
        return "", ""


    if "," in name:

        surname, given_names = (
            name.split(
                ",",
                1,
            )
        )

        return (
            given_names.strip(),
            surname.strip(),
        )


    parts = name.split()

    if len(parts) == 1:
        return "", parts[0]


    surname = parts[-1]

    given_names = " ".join(
        parts[:-1]
    )

    return (
        given_names,
        surname,
    )


def create_initials(
    given_names: str,
    spaced: bool = True,
) -> str:
    """
    John Michael -> J. M.

    or:

    John Michael -> J.M.
    """

    parts = [
        part

        for part
        in re.split(
            r"[\s\-]+",
            given_names,
        )

        if part
    ]


    initials = [
        f"{part[0].upper()}."

        for part
        in parts

        if part
    ]


    separator = (
        " "
        if spaced
        else ""
    )

    return separator.join(
        initials
    )


# =========================================================
# APA authors
# =========================================================

def format_authors_apa(
    authors: list[str],
) -> str:

    formatted = []


    for author in authors:

        given_names, surname = (
            parse_author_name(
                author
            )
        )

        initials = create_initials(
            given_names
        )


        if initials:

            formatted.append(
                (
                    f"{surname}, "
                    f"{initials}"
                )
            )

        else:

            formatted.append(
                surname
            )


    if not formatted:
        return ""


    if len(formatted) == 1:
        return formatted[0]


    if len(formatted) == 2:

        return (
            formatted[0]
            + ", & "
            + formatted[1]
        )


    return (
        ", ".join(
            formatted[:-1]
        )
        + ", & "
        + formatted[-1]
    )


# =========================================================
# MLA authors
# =========================================================

def format_authors_mla(
    authors: list[str],
) -> str:

    if not authors:
        return ""


    first_given, first_surname = (
        parse_author_name(
            authors[0]
        )
    )


    first_author = (
        f"{first_surname}, {first_given}"
        if first_given
        else first_surname
    )


    if len(authors) == 1:
        return first_author


    if len(authors) > 2:

        return (
            first_author
            + ", et al."
        )


    second_given, second_surname = (
        parse_author_name(
            authors[1]
        )
    )


    second_author = " ".join(
        part

        for part in [
            second_given,
            second_surname,
        ]

        if part
    )


    return (
        first_author
        + ", and "
        + second_author
    )


# =========================================================
# IEEE authors
# =========================================================

def format_authors_ieee(
    authors: list[str],
) -> str:

    formatted = []


    for author in authors:

        given_names, surname = (
            parse_author_name(
                author
            )
        )

        initials = create_initials(
            given_names
        )


        formatted_name = " ".join(
            part

            for part in [
                initials,
                surname,
            ]

            if part
        )


        formatted.append(
            formatted_name
        )


    if not formatted:
        return ""


    if len(formatted) == 1:
        return formatted[0]


    if len(formatted) > 6:

        return (
            formatted[0]
            + " et al."
        )


    if len(formatted) == 2:

        return (
            formatted[0]
            + " and "
            + formatted[1]
        )


    return (
        ", ".join(
            formatted[:-1]
        )
        + ", and "
        + formatted[-1]
    )


# =========================================================
# Harvard authors
# =========================================================

def format_authors_harvard(
    authors: list[str],
) -> str:

    formatted = []


    for author in authors:

        given_names, surname = (
            parse_author_name(
                author
            )
        )

        initials = create_initials(
            given_names,
            spaced=False,
        )


        if initials:

            formatted.append(
                (
                    f"{surname}, "
                    f"{initials}"
                )
            )

        else:

            formatted.append(
                surname
            )


    if not formatted:
        return ""


    if len(formatted) == 1:
        return formatted[0]


    return (
        ", ".join(
            formatted[:-1]
        )
        + " & "
        + formatted[-1]
    )


# =========================================================
# APA citation
# =========================================================

def generate_apa(
    metadata: dict,
) -> str:

    authors = metadata.get(
        "authors"
    ) or []

    author_text = (
        format_authors_apa(
            authors
        )
    )

    year = (
        clean_value(
            metadata.get(
                "publication_year"
            )
        )
        or "n.d."
    )

    title = clean_value(
        metadata.get("title")
    )

    venue = clean_value(
        metadata.get(
            "journal_or_conference"
        )
    )

    volume = clean_value(
        metadata.get("volume")
    )

    issue = clean_value(
        metadata.get("issue")
    )

    pages = clean_value(
        metadata.get("pages")
    )

    publisher = clean_value(
        metadata.get("publisher")
    )

    link = get_best_link(
        metadata
    )


    pieces = []


    if author_text:

        pieces.append(
            f"{author_text} ({year})."
        )

    else:

        pieces.append(
            f"{title} ({year})."
        )


    if author_text and title:

        pieces.append(
            f"{title}."
        )


    publication = ""


    if venue:

        publication += venue


    if volume:

        if publication:
            publication += ", "

        publication += volume


    if issue:

        publication += (
            f"({issue})"
        )


    if pages:

        if publication:
            publication += ", "

        publication += pages


    if publication:

        pieces.append(
            publication
            + "."
        )


    if (
        publisher
        and not venue
    ):

        pieces.append(
            publisher
            + "."
        )


    if link:

        pieces.append(
            link
        )


    return " ".join(
        pieces
    ).strip()


# =========================================================
# MLA citation
# =========================================================

def generate_mla(
    metadata: dict,
) -> str:

    authors = metadata.get(
        "authors"
    ) or []

    author_text = (
        format_authors_mla(
            authors
        )
    )

    title = clean_value(
        metadata.get("title")
    )

    venue = clean_value(
        metadata.get(
            "journal_or_conference"
        )
    )

    publisher = clean_value(
        metadata.get("publisher")
    )

    year = clean_value(
        metadata.get(
            "publication_year"
        )
    )

    volume = clean_value(
        metadata.get("volume")
    )

    issue = clean_value(
        metadata.get("issue")
    )

    pages = clean_value(
        metadata.get("pages")
    )

    link = get_best_link(
        metadata
    )


    pieces = []


    if author_text:

        pieces.append(
            author_text + "."
        )


    if title:

        pieces.append(
            f'"{title}."'
        )


    publication_parts = []


    if venue:

        publication_parts.append(
            venue
        )


    if volume:

        publication_parts.append(
            f"vol. {volume}"
        )


    if issue:

        publication_parts.append(
            f"no. {issue}"
        )


    if publisher:

        publication_parts.append(
            publisher
        )


    if year:

        publication_parts.append(
            year
        )


    if pages:

        publication_parts.append(
            f"pp. {pages}"
        )


    if publication_parts:

        pieces.append(
            ", ".join(
                publication_parts
            )
            + "."
        )


    if link:

        pieces.append(
            link
            + "."
        )


    return " ".join(
        pieces
    ).strip()


# =========================================================
# IEEE citation
# =========================================================

def generate_ieee(
    metadata: dict,
) -> str:

    authors = metadata.get(
        "authors"
    ) or []

    author_text = (
        format_authors_ieee(
            authors
        )
    )

    title = clean_value(
        metadata.get("title")
    )

    venue = clean_value(
        metadata.get(
            "journal_or_conference"
        )
    )

    year = clean_value(
        metadata.get(
            "publication_year"
        )
    )

    volume = clean_value(
        metadata.get("volume")
    )

    issue = clean_value(
        metadata.get("issue")
    )

    pages = clean_value(
        metadata.get("pages")
    )

    link = get_best_link(
        metadata
    )


    pieces = []


    if author_text:

        pieces.append(
            author_text + ","
        )


    if title:

        pieces.append(
            f'"{title},"'
        )


    if venue:

        pieces.append(
            venue + ","
        )


    if volume:

        pieces.append(
            f"vol. {volume},"
        )


    if issue:

        pieces.append(
            f"no. {issue},"
        )


    if pages:

        pieces.append(
            f"pp. {pages},"
        )


    if year:

        pieces.append(
            year + "."
        )


    if link:

        pieces.append(
            link
        )


    citation = " ".join(
        pieces
    ).strip()


    citation = re.sub(
        r",\s*\.",
        ".",
        citation,
    )


    return citation


# =========================================================
# Chicago author-date citation
# =========================================================

def generate_chicago(
    metadata: dict,
) -> str:

    authors = metadata.get(
        "authors"
    ) or []

    author_text = (
        format_authors_mla(
            authors
        )
    )

    year = (
        clean_value(
            metadata.get(
                "publication_year"
            )
        )
        or "n.d."
    )

    title = clean_value(
        metadata.get("title")
    )

    venue = clean_value(
        metadata.get(
            "journal_or_conference"
        )
    )

    volume = clean_value(
        metadata.get("volume")
    )

    issue = clean_value(
        metadata.get("issue")
    )

    pages = clean_value(
        metadata.get("pages")
    )

    link = get_best_link(
        metadata
    )


    pieces = []


    if author_text:

        pieces.append(
            author_text + "."
        )


    pieces.append(
        year + "."
    )


    if title:

        pieces.append(
            f'"{title}."'
        )


    publication = ""


    if venue:

        publication += venue


    if volume:

        if publication:
            publication += " "

        publication += volume


    if issue:

        publication += (
            f", no. {issue}"
        )


    if pages:

        publication += (
            f": {pages}"
        )


    if publication:

        pieces.append(
            publication
            + "."
        )


    if link:

        pieces.append(
            link
            + "."
        )


    return " ".join(
        pieces
    ).strip()


# =========================================================
# Harvard citation
# =========================================================

def generate_harvard(
    metadata: dict,
) -> str:

    authors = metadata.get(
        "authors"
    ) or []

    author_text = (
        format_authors_harvard(
            authors
        )
    )

    year = (
        clean_value(
            metadata.get(
                "publication_year"
            )
        )
        or "n.d."
    )

    title = clean_value(
        metadata.get("title")
    )

    venue = clean_value(
        metadata.get(
            "journal_or_conference"
        )
    )

    volume = clean_value(
        metadata.get("volume")
    )

    issue = clean_value(
        metadata.get("issue")
    )

    pages = clean_value(
        metadata.get("pages")
    )

    link = get_best_link(
        metadata
    )


    pieces = []


    if author_text:

        pieces.append(
            f"{author_text} ({year})"
        )

    else:

        pieces.append(
            f"({year})"
        )


    if title:

        pieces.append(
            f"'{title}',"
        )


    if venue:

        pieces.append(
            venue + ","
        )


    if volume:

        pieces.append(
            f"vol. {volume},"
        )


    if issue:

        pieces.append(
            f"no. {issue},"
        )


    if pages:

        pieces.append(
            f"pp. {pages}."
        )


    if link:

        pieces.append(
            f"Available at: {link}."
        )


    return " ".join(
        pieces
    ).strip()


# =========================================================
# BibTeX helpers
# =========================================================

def get_bibtex_entry_type(
    document_type: str | None,
) -> str:

    mapping = {
        "research_article":
            "article",

        "review_paper":
            "article",

        "conference_paper":
            "inproceedings",

        "thesis":
            "phdthesis",

        "preprint":
            "misc",

        "book_chapter":
            "incollection",

        "report":
            "techreport",

        "certificate":
            "misc",

        "other":
            "misc",
    }


    return mapping.get(
        clean_value(
            document_type
        ),
        "misc",
    )


def create_bibtex_key(
    metadata: dict,
) -> str:

    authors = metadata.get(
        "authors"
    ) or []


    if authors:

        _, surname = (
            parse_author_name(
                authors[0]
            )
        )

    else:

        surname = "unknown"


    year = (
        clean_value(
            metadata.get(
                "publication_year"
            )
        )
        or "nd"
    )


    title = clean_value(
        metadata.get("title")
    )


    title_words = re.findall(
        r"[A-Za-z0-9]+",
        title,
    )


    ignored_words = {
        "a",
        "an",
        "the",
        "of",
        "and",
        "in",
        "on",
        "for",
        "to",
    }


    title_word = "work"


    for word in title_words:

        if (
            word.lower()
            not in ignored_words
        ):

            title_word = word

            break


    raw_key = (
        surname
        + year
        + title_word
    )


    return re.sub(
        r"[^A-Za-z0-9]",
        "",
        raw_key,
    )


def escape_bibtex(
    value: str,
) -> str:

    return (
        value
        .replace(
            "\\",
            r"\\",
        )
        .replace(
            "{",
            r"\{",
        )
        .replace(
            "}",
            r"\}",
        )
    )


def generate_bibtex(
    metadata: dict,
) -> str:

    entry_type = (
        get_bibtex_entry_type(
            metadata.get(
                "document_type"
            )
        )
    )

    citation_key = (
        create_bibtex_key(
            metadata
        )
    )


    fields = []


    title = clean_value(
        metadata.get("title")
    )

    authors = metadata.get(
        "authors"
    ) or []

    year = clean_value(
        metadata.get(
            "publication_year"
        )
    )

    venue = clean_value(
        metadata.get(
            "journal_or_conference"
        )
    )

    publisher = clean_value(
        metadata.get("publisher")
    )

    volume = clean_value(
        metadata.get("volume")
    )

    issue = clean_value(
        metadata.get("issue")
    )

    pages = clean_value(
        metadata.get("pages")
    )

    doi = clean_value(
        metadata.get("doi")
    )

    url = clean_value(
        metadata.get("url")
    )


    if title:

        fields.append(
            (
                "  title = "
                f"{{{escape_bibtex(title)}}}"
            )
        )


    if authors:

        fields.append(
            (
                "  author = "
                "{"
                + escape_bibtex(
                    " and ".join(
                        authors
                    )
                )
                + "}"
            )
        )


    if year:

        fields.append(
            (
                "  year = "
                f"{{{year}}}"
            )
        )


    if venue:

        field_name = (
            "booktitle"
            if entry_type
            == "inproceedings"
            else "journal"
        )


        if entry_type in {
            "techreport",
            "phdthesis",
            "misc",
        }:

            field_name = "howpublished"


        fields.append(
            (
                f"  {field_name} = "
                f"{{{escape_bibtex(venue)}}}"
            )
        )


    if publisher:

        fields.append(
            (
                "  publisher = "
                f"{{{escape_bibtex(publisher)}}}"
            )
        )


    if volume:

        fields.append(
            (
                "  volume = "
                f"{{{volume}}}"
            )
        )


    if issue:

        fields.append(
            (
                "  number = "
                f"{{{issue}}}"
            )
        )


    if pages:

        fields.append(
            (
                "  pages = "
                f"{{{pages}}}"
            )
        )


    if doi:

        fields.append(
            (
                "  doi = "
                f"{{{doi}}}"
            )
        )


    if url:

        fields.append(
            (
                "  url = "
                f"{{{url}}}"
            )
        )


    joined_fields = ",\n".join(
        fields
    )


    return (
        f"@{entry_type}"
        f"{{{citation_key},\n"
        f"{joined_fields}\n"
        "}"
    )


# =========================================================
# Generate every supported citation style
# =========================================================

def generate_all_citations(
    metadata: dict,
) -> dict:
    """
    Generates all supported citation styles using
    saved bibliographic metadata only.

    No AI call occurs here.
    """

    return {
        "apa":
            generate_apa(
                metadata
            ),

        "mla":
            generate_mla(
                metadata
            ),

        "ieee":
            generate_ieee(
                metadata
            ),

        "chicago":
            generate_chicago(
                metadata
            ),

        "harvard":
            generate_harvard(
                metadata
            ),

        "bibtex":
            generate_bibtex(
                metadata
            ),
    }