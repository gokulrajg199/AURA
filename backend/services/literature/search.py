from __future__ import annotations

import asyncio
import difflib
import html
import math
import os
import re
import xml.etree.ElementTree as ET

from collections import Counter
from datetime import datetime
from typing import Any

import httpx


# ============================================================================
# CONFIGURATION
# ============================================================================

OPENALEX_URL = "https://api.openalex.org/works"
CROSSREF_URL = "https://api.crossref.org/v1/works"

SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

ARXIV_URL = "https://export.arxiv.org/api/query"

IEEE_XPLORE_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

# Replace with a real project email if deploying publicly.
CROSSREF_EMAIL = os.getenv(
    "CROSSREF_EMAIL",
    "aura.research.platform@example.com",
)

SEMANTIC_SCHOLAR_API_KEY = os.getenv(
    "SEMANTIC_SCHOLAR_API_KEY",
)

IEEE_XPLORE_API_KEY = os.getenv(
    "IEEE_XPLORE_API_KEY",
)

DEFAULT_YEAR_FROM = 2022
DEFAULT_YEAR_TO = 2026
DEFAULT_MAX_RESULTS = 20

REQUEST_TIMEOUT = 20.0

USER_AGENT = (
    "AURA-Research-Platform/3.0 "
    "(Academic Literature Discovery; "
    f"mailto:{CROSSREF_EMAIL})"
)


# ============================================================================
# HTTP CLIENT
# ============================================================================

def _headers() -> dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    if SEMANTIC_SCHOLAR_API_KEY:
        headers["x-api-key"] = SEMANTIC_SCHOLAR_API_KEY

    return headers


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    response = await client.get(
        url,
        params=params,
        headers=headers or _headers(),
    )
    response.raise_for_status()
    return response.json()


async def _get_text(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> str:
    response = await client.get(
        url,
        params=params,
        headers=headers or _headers(),
    )
    response.raise_for_status()
    return response.text


# ============================================================================
# TEXT / NORMALIZATION HELPERS
# ============================================================================

def _clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)

    text = html.unescape(text)

    text = re.sub(r"<[^>]+>", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _normalize_title(title: Any) -> str:
    title = _clean_text(title).lower()

    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title,
    )

    title = re.sub(
        r"\s+",
        " ",
        title,
    )

    return title.strip()


def _normalize_doi(value: Any) -> str:
    if not value:
        return ""

    doi = str(value).strip()

    doi = re.sub(
        r"^https?://doi\.org/",
        "",
        doi,
        flags=re.IGNORECASE,
    )

    doi = re.sub(
        r"^doi:\s*",
        "",
        doi,
        flags=re.IGNORECASE,
    )

    return doi.strip().lower()


def _normalize_identifier(value: Any) -> str:
    if not value:
        return ""

    return re.sub(
        r"\s+",
        "",
        str(value).strip().lower(),
    )


def _tokenize(text: str) -> set[str]:
    text = _clean_text(text).lower()

    return {
        token
        for token in re.findall(r"[a-z0-9]+", text)
        if len(token) > 2
    }


def _keyword_relevance(
    query: str,
    title: str,
    abstract: str,
) -> float:
    query_tokens = _tokenize(query)

    if not query_tokens:
        return 0.0

    title_tokens = _tokenize(title)
    abstract_tokens = _tokenize(abstract)

    title_overlap = len(query_tokens & title_tokens)
    abstract_overlap = len(query_tokens & abstract_tokens)

    title_score = title_overlap / len(query_tokens)
    abstract_score = abstract_overlap / len(query_tokens)

    score = (
        title_score * 0.70
        + abstract_score * 0.30
    )

    return round(
        min(1.0, max(0.0, score)),
        4,
    )


def _title_similarity(
    title_a: str,
    title_b: str,
) -> float:
    a = _normalize_title(title_a)
    b = _normalize_title(title_b)

    if not a or not b:
        return 0.0

    return round(
        difflib.SequenceMatcher(
            None,
            a,
            b,
        ).ratio(),
        4,
    )


def _author_overlap(
    authors_a: list[str],
    authors_b: list[str],
) -> float:
    a = {
        _clean_text(name).lower()
        for name in authors_a
        if _clean_text(name)
    }

    b = {
        _clean_text(name).lower()
        for name in authors_b
        if _clean_text(name)
    }

    if not a or not b:
        return 0.0

    intersection = len(a & b)

    return round(
        intersection / min(len(a), len(b)),
        4,
    )


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None

        return int(value)

    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def _year_from_date(value: Any) -> int | None:
    if not value:
        return None

    match = re.search(
        r"(19|20)\d{2}",
        str(value),
    )

    if not match:
        return None

    return int(match.group(0))


def _extract_year(record: dict[str, Any]) -> int | None:
    for key in (
        "publication_year",
        "year",
        "published_year",
        "created_year",
    ):
        year = _safe_int(record.get(key))

        if year:
            return year

    return _year_from_date(
        record.get("publication_date")
        or record.get("published")
        or record.get("created")
    )


# ============================================================================
# ABSTRACT RECONSTRUCTION
# ============================================================================

def _reconstruct_openalex_abstract(
    inverted_index: Any,
) -> str:
    if not isinstance(inverted_index, dict):
        return ""

    words: list[tuple[int, str]] = []

    for word, positions in inverted_index.items():
        if not isinstance(positions, list):
            continue

        for position in positions:
            try:
                words.append(
                    (
                        int(position),
                        str(word),
                    )
                )
            except (TypeError, ValueError):
                continue

    words.sort(
        key=lambda item: item[0]
    )

    return " ".join(
        word
        for _, word in words
    )


# ============================================================================
# OPEN ACCESS / URL HELPERS
# ============================================================================

def _detect_openalex_oa_url(
    work: dict[str, Any],
) -> str:
    open_access = work.get("open_access") or {}

    if isinstance(open_access, dict):
        url = (
            open_access.get("oa_url")
            or ""
        )

        if url:
            return str(url)

    locations = work.get("locations") or []

    if isinstance(locations, list):
        for location in locations:
            if not isinstance(location, dict):
                continue

            landing_page = (
                location.get("landing_page_url")
                or ""
            )

            pdf_url = (
                location.get("pdf_url")
                or ""
            )

            if pdf_url:
                return str(pdf_url)

            if landing_page:
                return str(landing_page)

    return ""


def _canonical_url(
    *,
    doi: str = "",
    url: str = "",
) -> str:
    if doi:
        return f"https://doi.org/{doi}"

    return url or ""


# ============================================================================
# OPENALEX
# ============================================================================

async def search_openalex(
    client: httpx.AsyncClient,
    query: str,
    year_from: int,
    year_to: int,
    max_results: int,
) -> dict[str, Any]:
    params = {
        "search": query,
        "filter": (
            f"from_publication_date:"
            f"{year_from}-01-01,"
            f"to_publication_date:"
            f"{year_to}-12-31"
        ),
        "sort": "relevance_score:desc",
        "per-page": max_results,
        "mailto": CROSSREF_EMAIL,
    }

    data = await _get_json(
        client,
        OPENALEX_URL,
        params=params,
    )

    papers: list[dict[str, Any]] = []

    for work in data.get("results", []):
        if not isinstance(work, dict):
            continue

        title = _clean_text(
            work.get("display_name")
            or work.get("title")
        )

        abstract = _reconstruct_openalex_abstract(
            work.get("abstract_inverted_index")
        )

        doi = _normalize_doi(
            work.get("doi")
        )

        publication_year = _safe_int(
            work.get("publication_year")
        )

        authors: list[str] = []

        for authorship in work.get(
            "authorships",
            [],
        ):
            if not isinstance(authorship, dict):
                continue

            author = authorship.get(
                "author"
            ) or {}

            name = _clean_text(
                author.get("display_name")
            )

            if name:
                authors.append(name)

        primary_location = (
            work.get("primary_location")
            or {}
        )

        source = (
            primary_location.get("source")
            or {}
        )

        journal = _clean_text(
            source.get("display_name")
        )

        source_url = _detect_openalex_oa_url(
            work
        )

        openalex_id = _normalize_identifier(
            work.get("id")
        )

        citation_count = _safe_int(
            work.get("cited_by_count")
        ) or 0

        topics = []

        for topic in work.get(
            "topics",
            [],
        ):
            if not isinstance(topic, dict):
                continue

            topic_name = _clean_text(
                topic.get("display_name")
            )

            if topic_name:
                topics.append(topic_name)

        paper = _make_paper(
            provider="OpenAlex",
            title=title,
            abstract=abstract,
            authors=authors,
            publication_year=publication_year,
            doi=doi,
            citation_count=citation_count,
            journal=journal,
            url=_canonical_url(
                doi=doi,
                url=source_url,
            ),
            source_type="scholarly_index",
            retrieval_mode="keyword",
            external_ids={
                "openalex_id": openalex_id,
            },
            topics=topics,
            raw_metadata={
                "openalex_id": openalex_id,
                "type": work.get("type"),
                "language": work.get("language"),
                "is_oa": (
                    work.get("open_access", {})
                    or {}
                ).get("is_oa", False),
            },
        )

        papers.append(paper)

    return {
        "provider": "OpenAlex",
        "status": "success",
        "papers": papers,
        "count": len(papers),
        "retrieval_mode": "keyword",
    }


async def search_openalex_semantic(
    client: httpx.AsyncClient,
    query: str,
    year_from: int,
    year_to: int,
    max_results: int,
) -> dict[str, Any]:
    params = {
        "search": query,
        "filter": (
            f"from_publication_date:"
            f"{year_from}-01-01,"
            f"to_publication_date:"
            f"{year_to}-12-31"
        ),
        "sort": "relevance_score:desc",
        "per-page": max_results,
        "mailto": CROSSREF_EMAIL,
    }

    data = await _get_json(
        client,
        OPENALEX_URL,
        params=params,
    )

    papers: list[dict[str, Any]] = []

    for work in data.get("results", []):
        if not isinstance(work, dict):
            continue

        title = _clean_text(
            work.get("display_name")
            or work.get("title")
        )

        abstract = _reconstruct_openalex_abstract(
            work.get("abstract_inverted_index")
        )

        doi = _normalize_doi(
            work.get("doi")
        )

        authors: list[str] = []

        for authorship in work.get(
            "authorships",
            [],
        ):
            author = (
                authorship.get("author")
                if isinstance(authorship, dict)
                else {}
            ) or {}

            name = _clean_text(
                author.get("display_name")
            )

            if name:
                authors.append(name)

        primary_location = (
            work.get("primary_location")
            or {}
        )

        source = (
            primary_location.get("source")
            or {}
        )

        journal = _clean_text(
            source.get("display_name")
        )

        url = _detect_openalex_oa_url(
            work
        )

        openalex_id = _normalize_identifier(
            work.get("id")
        )

        topics: list[str] = []

        for topic in work.get(
            "topics",
            [],
        ):
            if not isinstance(topic, dict):
                continue

            name = _clean_text(
                topic.get("display_name")
            )

            if name:
                topics.append(name)

        papers.append(
            _make_paper(
                provider="OpenAlex",
                title=title,
                abstract=abstract,
                authors=authors,
                publication_year=_safe_int(
                    work.get("publication_year")
                ),
                doi=doi,
                citation_count=(
                    _safe_int(
                        work.get("cited_by_count")
                    )
                    or 0
                ),
                journal=journal,
                url=_canonical_url(
                    doi=doi,
                    url=url,
                ),
                source_type="scholarly_index",
                retrieval_mode="semantic",
                external_ids={
                    "openalex_id": openalex_id,
                },
                topics=topics,
                raw_metadata={
                    "openalex_id": openalex_id,
                    "relevance_score": (
                        work.get("relevance_score")
                    ),
                    "is_oa": (
                        work.get("open_access", {})
                        or {}
                    ).get("is_oa", False),
                },
            )
        )

    return {
        "provider": "OpenAlex",
        "status": "success",
        "papers": papers,
        "count": len(papers),
        "retrieval_mode": "semantic",
    }


# ============================================================================
# CROSSREF
# ============================================================================

async def search_crossref(
    client: httpx.AsyncClient,
    query: str,
    year_from: int,
    year_to: int,
    max_results: int,
) -> dict[str, Any]:
    params = {
        "query.bibliographic": query,
        "filter": (
            f"from-pub-date:"
            f"{year_from}-01-01,"
            f"until-pub-date:"
            f"{year_to}-12-31"
        ),
        "rows": max_results,
        "select": (
            "DOI,title,author,published,"
            "published-print,published-online,"
            "container-title,publisher,"
            "URL,type,is-referenced-by-count"
        ),
        "mailto": CROSSREF_EMAIL,
    }

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    data = await _get_json(
        client,
        CROSSREF_URL,
        params=params,
        headers=headers,
    )

    message = data.get(
        "message",
        {},
    )

    papers: list[dict[str, Any]] = []

    for item in message.get(
        "items",
        [],
    ):
        if not isinstance(item, dict):
            continue

        title_list = item.get(
            "title",
            [],
        )

        title = _clean_text(
            title_list[0]
            if isinstance(title_list, list)
            and title_list
            else ""
        )

        authors: list[str] = []

        for author in item.get(
            "author",
            [],
        ):
            if not isinstance(author, dict):
                continue

            given = _clean_text(
                author.get("given")
            )

            family = _clean_text(
                author.get("family")
            )

            name = " ".join(
                part
                for part in (
                    given,
                    family,
                )
                if part
            )

            if name:
                authors.append(name)

        published = (
            item.get("published")
            or item.get("published-online")
            or item.get("published-print")
            or {}
        )

        date_parts = (
            published.get("date-parts", [])
            if isinstance(published, dict)
            else []
        )

        publication_year = None

        if date_parts:
            try:
                publication_year = int(
                    date_parts[0][0]
                )
            except (
                IndexError,
                TypeError,
                ValueError,
            ):
                publication_year = None

        doi = _normalize_doi(
            item.get("DOI")
        )

        journal_list = item.get(
            "container-title",
            [],
        )

        journal = _clean_text(
            journal_list[0]
            if isinstance(journal_list, list)
            and journal_list
            else ""
        )

        papers.append(
            _make_paper(
                provider="Crossref",
                title=title,
                abstract="",
                authors=authors,
                publication_year=publication_year,
                doi=doi,
                citation_count=(
                    _safe_int(
                        item.get(
                            "is-referenced-by-count"
                        )
                    )
                    or 0
                ),
                journal=journal,
                url=_canonical_url(
                    doi=doi,
                    url=_clean_text(
                        item.get("URL")
                    ),
                ),
                source_type="scholarly_registry",
                retrieval_mode="bibliographic",
                external_ids={},
                topics=[],
                raw_metadata={
                    "publisher": _clean_text(
                        item.get("publisher")
                    ),
                    "type": _clean_text(
                        item.get("type")
                    ),
                },
            )
        )

    return {
        "provider": "Crossref",
        "status": "success",
        "papers": papers,
        "count": len(papers),
        "retrieval_mode": "bibliographic",
    }


# ============================================================================
# SEMANTIC SCHOLAR
# ============================================================================

async def search_semantic_scholar(
    client: httpx.AsyncClient,
    query: str,
    year_from: int,
    year_to: int,
    max_results: int,
) -> dict[str, Any]:
    year_range = (
        f"{year_from}-{year_to}"
    )

    params = {
        "query": query,
        "limit": max_results,
        "fields": (
            "paperId,title,abstract,"
            "authors,year,venue,publicationDate,"
            "citationCount,externalIds,"
            "openAccessPdf,url"
        ),
        "year": year_range,
    }

    data = await _get_json(
        client,
        SEMANTIC_SCHOLAR_URL,
        params=params,
    )

    papers: list[dict[str, Any]] = []

    for item in data.get(
        "data",
        [],
    ):
        if not isinstance(item, dict):
            continue

        authors = []

        for author in item.get(
            "authors",
            [],
        ):
            if not isinstance(author, dict):
                continue

            name = _clean_text(
                author.get("name")
            )

            if name:
                authors.append(name)

        external_ids = (
            item.get("externalIds")
            or {}
        )

        doi = _normalize_doi(
            external_ids.get("DOI")
        )

        paper_id = _normalize_identifier(
            item.get("paperId")
        )

        open_access_pdf = (
            item.get("openAccessPdf")
            or {}
        )

        pdf_url = _clean_text(
            open_access_pdf.get("url")
            if isinstance(
                open_access_pdf,
                dict,
            )
            else ""
        )

        url = (
            pdf_url
            or _clean_text(
                item.get("url")
            )
        )

        papers.append(
            _make_paper(
                provider="Semantic Scholar",
                title=_clean_text(
                    item.get("title")
                ),
                abstract=_clean_text(
                    item.get("abstract")
                ),
                authors=authors,
                publication_year=_safe_int(
                    item.get("year")
                ),
                doi=doi,
                citation_count=(
                    _safe_int(
                        item.get(
                            "citationCount"
                        )
                    )
                    or 0
                ),
                journal=_clean_text(
                    item.get("venue")
                ),
                url=_canonical_url(
                    doi=doi,
                    url=url,
                ),
                source_type="scholarly_graph",
                retrieval_mode="keyword",
                external_ids={
                    "semantic_scholar_id": paper_id,
                    "pmid": _normalize_identifier(
                        external_ids.get("PubMed")
                    ),
                    "arxiv": _normalize_identifier(
                        external_ids.get("ArXiv")
                    ),
                    "corpus_id": _normalize_identifier(
                        external_ids.get("CorpusId")
                    ),
                },
                topics=[],
                raw_metadata={
                    "publication_date": _clean_text(
                        item.get(
                            "publicationDate"
                        )
                    ),
                    "open_access_pdf": pdf_url,
                },
            )
        )

    return {
        "provider": "Semantic Scholar",
        "status": "success",
        "papers": papers,
        "count": len(papers),
        "retrieval_mode": "keyword",
    }


# ============================================================================
# PUBMED / NCBI
# ============================================================================

async def search_pubmed(
    client: httpx.AsyncClient,
    query: str,
    year_from: int,
    year_to: int,
    max_results: int,
) -> dict[str, Any]:
    search_params = {
        "db": "pubmed",
        "term": (
            f"({query}) AND "
            f'("{year_from}"[Date - Publication] : '
            f'"{year_to}"[Date - Publication])'
        ),
        "retmax": max_results,
        "retmode": "json",
        "tool": "AURA",
        "email": CROSSREF_EMAIL,
    }

    search_data = await _get_json(
        client,
        PUBMED_ESEARCH_URL,
        params=search_params,
    )

    id_list = (
        search_data.get("esearchresult", {})
        .get("idlist", [])
    )

    if not id_list:
        return {
            "provider": "PubMed",
            "status": "success",
            "papers": [],
            "count": 0,
            "retrieval_mode": "keyword",
        }

    summary_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "json",
        "tool": "AURA",
        "email": CROSSREF_EMAIL,
    }

    summary_data = await _get_json(
        client,
        PUBMED_ESUMMARY_URL,
        params=summary_params,
    )

    result = summary_data.get(
        "result",
        {},
    )

    papers: list[dict[str, Any]] = []

    for pmid in id_list:
        record = result.get(
            str(pmid),
            {},
        )

        if not isinstance(record, dict):
            continue

        title = _clean_text(
            record.get("title")
        )

        authors: list[str] = []

        for author in record.get(
            "authors",
            [],
        ):
            if not isinstance(author, dict):
                continue

            name = _clean_text(
                author.get("name")
            )

            if name:
                authors.append(name)

        pub_date = _clean_text(
            record.get("pubdate")
        )

        publication_year = _year_from_date(
            pub_date
        )

        journal = _clean_text(
            record.get("fulljournalname")
            or record.get("source")
        )

        doi = ""

        article_ids = record.get(
            "articleids",
            [],
        )

        if isinstance(article_ids, list):
            for article_id in article_ids:
                if not isinstance(
                    article_id,
                    dict,
                ):
                    continue

                if (
                    str(
                        article_id.get(
                            "idtype"
                        )
                    ).lower()
                    == "doi"
                ):
                    doi = _normalize_doi(
                        article_id.get("value")
                    )
                    break

        pmid_normalized = _normalize_identifier(
            pmid
        )

        url = (
            f"https://pubmed.ncbi.nlm.nih.gov/"
            f"{pmid_normalized}/"
        )

        papers.append(
            _make_paper(
                provider="PubMed",
                title=title,
                abstract="",
                authors=authors,
                publication_year=publication_year,
                doi=doi,
                citation_count=0,
                journal=journal,
                url=_canonical_url(
                    doi=doi,
                    url=url,
                ),
                source_type="biomedical_index",
                retrieval_mode="keyword",
                external_ids={
                    "pmid": pmid_normalized,
                },
                topics=[],
                raw_metadata={
                    "pubmed_article_type": (
                        record.get(
                            "pubtype"
                        )
                    ),
                    "language": record.get(
                        "lang"
                    ),
                },
            )
        )

    return {
        "provider": "PubMed",
        "status": "success",
        "papers": papers,
        "count": len(papers),
        "retrieval_mode": "keyword",
    }


# ============================================================================
# ARXIV
# ============================================================================

def _arxiv_namespace_tag(
    tag: str,
) -> str:
    return (
        "{http://www.w3.org/2005/Atom}"
        f"{tag}"
    )


async def search_arxiv(
    client: httpx.AsyncClient,
    query: str,
    year_from: int,
    year_to: int,
    max_results: int,
) -> dict[str, Any]:
    params = {
        "search_query": (
            "all:" + query
        ),
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    text = await _get_text(
        client,
        ARXIV_URL,
        params=params,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/atom+xml",
        },
    )

    root = ET.fromstring(text)

    papers: list[dict[str, Any]] = []

    for entry in root.findall(
        _arxiv_namespace_tag("entry")
    ):
        title = _clean_text(
            entry.findtext(
                _arxiv_namespace_tag("title"),
                default="",
            )
        )

        abstract = _clean_text(
            entry.findtext(
                _arxiv_namespace_tag("summary"),
                default="",
            )
        )

        published = _clean_text(
            entry.findtext(
                _arxiv_namespace_tag("published"),
                default="",
            )
        )

        year = _year_from_date(
            published
        )

        if year is not None:
            if year < year_from or year > year_to:
                continue

        authors: list[str] = []

        for author in entry.findall(
            _arxiv_namespace_tag("author")
        ):
            name = _clean_text(
                author.findtext(
                    _arxiv_namespace_tag("name"),
                    default="",
                )
            )

            if name:
                authors.append(name)

        entry_id = _clean_text(
            entry.findtext(
                _arxiv_namespace_tag("id"),
                default="",
            )
        )

        arxiv_id = ""

        if entry_id:
            arxiv_id = entry_id.rstrip(
                "/"
            ).split("/")[-1]

        doi = ""

        doi_element = entry.find(
            "{http://arxiv.org/schemas/atom}"
            "doi"
        )

        if doi_element is not None:
            doi = _normalize_doi(
                doi_element.text
            )

        categories: list[str] = []

        for category in entry.findall(
            "{http://arxiv.org/schemas/atom}"
            "category"
        ):
            term = _clean_text(
                category.attrib.get(
                    "term"
                )
            )

            if term:
                categories.append(term)

        papers.append(
            _make_paper(
                provider="arXiv",
                title=title,
                abstract=abstract,
                authors=authors,
                publication_year=year,
                doi=doi,
                citation_count=0,
                journal="arXiv",
                url=_canonical_url(
                    doi=doi,
                    url=entry_id,
                ),
                source_type="preprint_repository",
                retrieval_mode="keyword",
                external_ids={
                    "arxiv": _normalize_identifier(
                        arxiv_id
                    ),
                },
                topics=categories,
                raw_metadata={
                    "published": published,
                    "updated": _clean_text(
                        entry.findtext(
                            _arxiv_namespace_tag(
                                "updated"
                            ),
                            default="",
                        )
                    ),
                },
            )
        )

    return {
        "provider": "arXiv",
        "status": "success",
        "papers": papers,
        "count": len(papers),
        "retrieval_mode": "keyword",
    }


# ============================================================================
# IEEE XPLORE
# ============================================================================

async def search_ieee_xplore(
    client: httpx.AsyncClient,
    query: str,
    year_from: int,
    year_to: int,
    max_results: int,
) -> dict[str, Any]:
    if not IEEE_XPLORE_API_KEY:
        return {
            "provider": "IEEE Xplore",
            "status": "not_configured",
            "papers": [],
            "count": 0,
            "retrieval_mode": "official_api",
            "message": (
                "IEEE_XPLORE_API_KEY is not configured."
            ),
        }

    params = {
        "apikey": IEEE_XPLORE_API_KEY,
        "querytext": query,
        "start_record": 1,
        "max_records": max_results,
        "sort_order": "desc",
        "sort_field": "publication_year",
    }

    data = await _get_json(
        client,
        IEEE_XPLORE_URL,
        params=params,
    )

    papers: list[dict[str, Any]] = []

    articles = (
        data.get("articles")
        or data.get("results")
        or []
    )

    for article in articles:
        if not isinstance(article, dict):
            continue

        title = _clean_text(
            article.get("title")
        )

        abstract = _clean_text(
            article.get("abstract")
        )

        publication_year = _safe_int(
            article.get(
                "publication_year"
            )
        )

        if publication_year:
            if (
                publication_year < year_from
                or publication_year > year_to
            ):
                continue

        authors: list[str] = []

        author_data = article.get(
            "authors"
        )

        if isinstance(
            author_data,
            dict,
        ):
            author_data = (
                author_data.get(
                    "authors"
                )
                or []
            )

        if isinstance(
            author_data,
            list,
        ):
            for author in author_data:
                if isinstance(
                    author,
                    dict,
                ):
                    name = _clean_text(
                        author.get(
                            "full_name"
                        )
                        or author.get(
                            "name"
                        )
                    )
                else:
                    name = _clean_text(
                        author
                    )

                if name:
                    authors.append(name)

        doi = _normalize_doi(
            article.get("doi")
        )

        article_number = (
            _normalize_identifier(
                article.get(
                    "article_number"
                )
                or article.get(
                    "document_id"
                )
            )
        )

        url = _clean_text(
            article.get(
                "html_url"
            )
            or article.get(
                "pdf_url"
            )
            or article.get(
                "document_url"
            )
        )

        papers.append(
            _make_paper(
                provider="IEEE Xplore",
                title=title,
                abstract=abstract,
                authors=authors,
                publication_year=publication_year,
                doi=doi,
                citation_count=(
                    _safe_int(
                        article.get(
                            "citing_paper_count"
                        )
                    )
                    or 0
                ),
                journal=_clean_text(
                    article.get(
                        "publication_title"
                    )
                ),
                url=_canonical_url(
                    doi=doi,
                    url=url,
                ),
                source_type="technical_index",
                retrieval_mode="official_api",
                external_ids={
                    "ieee_article_number": (
                        article_number
                    ),
                    "ieee_document_id": (
                        _normalize_identifier(
                            article.get(
                                "document_id"
                            )
                        )
                    ),
                },
                topics=[],
                raw_metadata={
                    "publisher": "IEEE",
                    "content_type": _clean_text(
                        article.get(
                            "content_type"
                        )
                    ),
                },
            )
        )

    return {
        "provider": "IEEE Xplore",
        "status": "success",
        "papers": papers,
        "count": len(papers),
        "retrieval_mode": "official_api",
    }


# ============================================================================
# PAPER MODEL
# ============================================================================

def _make_paper(
    *,
    provider: str,
    title: str,
    abstract: str,
    authors: list[str],
    publication_year: int | None,
    doi: str,
    citation_count: int,
    journal: str,
    url: str,
    source_type: str,
    retrieval_mode: str,
    external_ids: dict[str, Any],
    topics: list[str],
    raw_metadata: dict[str, Any],
) -> dict[str, Any]:
    doi = _normalize_doi(doi)

    cleaned_authors = [
        _clean_text(author)
        for author in authors
        if _clean_text(author)
    ]

    cleaned_topics = [
        _clean_text(topic)
        for topic in topics
        if _clean_text(topic)
    ]

    return {
        "title": _clean_text(title),
        "abstract": _clean_text(abstract),
        "authors": cleaned_authors,
        "publication_year": publication_year,
        "doi": doi,
        "citation_count": max(
            0,
            citation_count,
        ),
        "journal": _clean_text(journal),
        "url": _clean_text(url),
        "provider": provider,
        "providers": [provider],
        "source_type": source_type,
        "retrieval_mode": retrieval_mode,
        "external_ids": external_ids,
        "topics": cleaned_topics,
        "raw_metadata": raw_metadata,
        "evidence": {
            "metadata_verified": True,
            "claim_verified": False,
            "verification_status": (
                "metadata_verified"
            ),
            "verification_note": (
                "Record retrieved from an "
                "identified scholarly or "
                "technical source. Scientific "
                "claims are not automatically "
                "verified by metadata retrieval."
            ),
        },
    }


# ============================================================================
# SOURCE QUALITY
# ============================================================================

def source_quality_score(
    paper: dict[str, Any],
) -> float:
    provider = str(
        paper.get("provider", "")
    ).lower()

    source_type = str(
        paper.get("source_type", "")
    ).lower()

    if "openalex" in provider:
        score = 0.92

    elif "semantic scholar" in provider:
        score = 0.92

    elif "crossref" in provider:
        score = 0.88

    elif "pubmed" in provider:
        score = 0.95

    elif "ieee" in provider:
        score = 0.98

    elif "arxiv" in provider:
        score = 0.82

    else:
        score = 0.70

    if source_type == "technical_index":
        score = max(
            score,
            0.95,
        )

    if paper.get("doi"):
        score += 0.02

    if paper.get("abstract"):
        score += 0.01

    return round(
        min(1.0, score),
        4,
    )


# ============================================================================
# RECENCY
# ============================================================================

def recency_score(
    publication_year: int | None,
    year_to: int,
) -> float:
    if not publication_year:
        return 0.0

    age = max(
        0,
        year_to - publication_year,
    )

    return round(
        math.exp(-0.35 * age),
        4,
    )


# ============================================================================
# RANKING
# ============================================================================

def _rank_paper(
    paper: dict[str, Any],
    query: str,
    year_to: int,
) -> dict[str, Any]:
    title = paper.get(
        "title",
        "",
    )

    abstract = paper.get(
        "abstract",
        "",
    )

    relevance = _keyword_relevance(
        query,
        title,
        abstract,
    )

    citations = (
        _safe_int(
            paper.get(
                "citation_count"
            )
        )
        or 0
    )

    citation_score = (
        min(
            1.0,
            math.log1p(citations)
            / math.log1p(1000),
        )
    )

    recency = recency_score(
        paper.get(
            "publication_year"
        ),
        year_to,
    )

    quality = source_quality_score(
        paper
    )

    final_score = (
        relevance * 0.50
        + citation_score * 0.20
        + recency * 0.15
        + quality * 0.15
    )

    paper["ranking"] = {
        "relevance_score": round(
            relevance,
            4,
        ),
        "citation_score": round(
            citation_score,
            4,
        ),
        "recency_score": round(
            recency,
            4,
        ),
        "source_quality_score": round(
            quality,
            4,
        ),
        "source_quality_percent": round(
            quality * 100,
            1,
        ),
        "final_score": round(
            final_score,
            4,
        ),
    }

    return paper


# ============================================================================
# DEDUPLICATION
# ============================================================================

def _paper_identity_keys(
    paper: dict[str, Any],
) -> list[str]:
    keys: list[str] = []

    doi = _normalize_doi(
        paper.get("doi")
    )

    if doi:
        keys.append(
            f"doi:{doi}"
        )

    external_ids = (
        paper.get("external_ids")
        or {}
    )

    for key in (
        "openalex_id",
        "semantic_scholar_id",
        "pmid",
        "arxiv",
        "ieee_article_number",
        "ieee_document_id",
    ):
        value = _normalize_identifier(
            external_ids.get(key)
        )

        if value:
            keys.append(
                f"{key}:{value}"
            )

    normalized_title = _normalize_title(
        paper.get("title", "")
    )

    if normalized_title:
        keys.append(
            f"title:{normalized_title}"
        )

    return keys


def _merge_paper_records(
    primary: dict[str, Any],
    secondary: dict[str, Any],
) -> dict[str, Any]:
    merged = primary.copy()

    primary_providers = list(
        primary.get(
            "providers",
            [],
        )
    )

    secondary_provider = secondary.get(
        "provider"
    )

    if secondary_provider:
        primary_providers.append(
            secondary_provider
        )

    merged["providers"] = list(
        dict.fromkeys(
            primary_providers
        )
    )

    for field in (
        "title",
        "abstract",
        "journal",
        "url",
        "doi",
    ):
        current = merged.get(field)

        if not current:
            merged[field] = secondary.get(
                field,
                current,
            )

    if len(
        secondary.get(
            "authors",
            [],
        )
    ) > len(
        merged.get(
            "authors",
            [],
        )
    ):
        merged["authors"] = secondary.get(
            "authors",
            [],
        )

    primary_citations = (
        _safe_int(
            merged.get(
                "citation_count"
            )
        )
        or 0
    )

    secondary_citations = (
        _safe_int(
            secondary.get(
                "citation_count"
            )
        )
        or 0
    )

    merged["citation_count"] = max(
        primary_citations,
        secondary_citations,
    )

    primary_year = _safe_int(
        merged.get(
            "publication_year"
        )
    )

    secondary_year = _safe_int(
        secondary.get(
            "publication_year"
        )
    )

    if primary_year is None:
        merged["publication_year"] = (
            secondary_year
        )

    external_ids = dict(
        merged.get(
            "external_ids",
            {},
        )
        or {}
    )

    external_ids.update(
        {
            key: value
            for key, value in (
                secondary.get(
                    "external_ids",
                    {},
                )
                or {}
            ).items()
            if value
        }
    )

    merged["external_ids"] = external_ids

    topics = list(
        merged.get(
            "topics",
            [],
        )
        or []
    )

    topics.extend(
        secondary.get(
            "topics",
            [],
        )
        or []
    )

    merged["topics"] = list(
        dict.fromkeys(
            topic
            for topic in topics
            if topic
        )
    )

    evidence = dict(
        merged.get(
            "evidence",
            {},
        )
        or {}
    )

    evidence["metadata_verified"] = True

    evidence["verification_status"] = (
        "multi_source_metadata_verified"
        if len(
            merged["providers"]
        ) > 1
        else "metadata_verified"
    )

    evidence["source_count"] = len(
        merged["providers"]
    )

    merged["evidence"] = evidence

    return merged


def deduplicate_papers(
    papers: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    merged: list[dict[str, Any]] = []

    identity_map: dict[str, int] = {}

    duplicates = 0

    for paper in papers:
        found_index: int | None = None

        keys = _paper_identity_keys(
            paper
        )

        for key in keys:
            if key in identity_map:
                found_index = identity_map[key]
                break

        if found_index is None:
            found_index = len(
                merged
            )

            merged.append(
                paper
            )

        else:
            duplicates += 1

            merged[found_index] = (
                _merge_paper_records(
                    merged[
                        found_index
                    ],
                    paper,
                )
            )

        for key in keys:
            identity_map[key] = (
                found_index
            )

    return merged, duplicates


# ============================================================================
# SOURCE STATUS
# ============================================================================

def _provider_status(
    result: Any,
    provider: str,
) -> dict[str, Any]:
    if isinstance(result, Exception):
        return {
            "provider": provider,
            "status": "failed",
            "count": 0,
            "error": str(result),
        }

    if not isinstance(result, dict):
        return {
            "provider": provider,
            "status": "failed",
            "count": 0,
            "error": "Invalid provider response.",
        }

    return {
        "provider": provider,
        "status": result.get(
            "status",
            "unknown",
        ),
        "count": result.get(
            "count",
            0,
        ),
        "retrieval_mode": result.get(
            "retrieval_mode"
        ),
        "message": result.get(
            "message"
        ),
    }


# ============================================================================
# YEAR DISTRIBUTION
# ============================================================================

def _year_distribution(
    papers: list[dict[str, Any]],
) -> dict[str, int]:
    counts = Counter()

    for paper in papers:
        year = paper.get(
            "publication_year"
        )

        if year:
            counts[str(year)] += 1

    return dict(
        sorted(
            counts.items(),
            key=lambda item: int(
                item[0]
            ),
        )
    )


# ============================================================================
# PROVIDER DISTRIBUTION
# ============================================================================

def _provider_distribution(
    papers: list[dict[str, Any]],
) -> dict[str, int]:
    counts = Counter()

    for paper in papers:
        providers = paper.get(
            "providers"
        ) or [
            paper.get(
                "provider",
                "Unknown",
            )
        ]

        for provider in providers:
            if provider:
                counts[str(provider)] += 1

    return dict(counts)


# ============================================================================
# MAIN DISCOVERY ENGINE
# ============================================================================

async def search_literature(
    query: str,
    year_from: int = DEFAULT_YEAR_FROM,
    year_to: int = DEFAULT_YEAR_TO,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict[str, Any]:
    """
    Multi-source AURA literature discovery.

    Returns
    -------
    dict
        Normalized papers, source coverage, ranking metadata,
        provenance and retrieval statistics.
    """

    query = _clean_text(query)

    if not query:
        return {
            "query": "",
            "papers": [],
            "stats": {
                "status": "failed",
                "message": (
                    "Literature query cannot be empty."
                ),
            },
        }

    year_from = _safe_int(
        year_from
    ) or DEFAULT_YEAR_FROM

    year_to = _safe_int(
        year_to
    ) or DEFAULT_YEAR_TO

    max_results = (
        _safe_int(
            max_results
        )
        or DEFAULT_MAX_RESULTS
    )

    if year_from > year_to:
        year_from, year_to = (
            year_to,
            year_from,
        )

    max_results = max(
        1,
        min(
            max_results,
            100,
        ),
    )

    started_at = datetime.utcnow()

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    ) as client:

        tasks = [
            search_openalex(
                client,
                query,
                year_from,
                year_to,
                max_results,
            ),
            search_openalex_semantic(
                client,
                query,
                year_from,
                year_to,
                max_results,
            ),
            search_crossref(
                client,
                query,
                year_from,
                year_to,
                max_results,
            ),
            search_semantic_scholar(
                client,
                query,
                year_from,
                year_to,
                max_results,
            ),
            search_pubmed(
                client,
                query,
                year_from,
                year_to,
                max_results,
            ),
            search_arxiv(
                client,
                query,
                year_from,
                year_to,
                max_results,
            ),
            search_ieee_xplore(
                client,
                query,
                year_from,
                year_to,
                max_results,
            ),
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    provider_names = [
        "OpenAlex",
        "OpenAlex Semantic",
        "Crossref",
        "Semantic Scholar",
        "PubMed",
        "arXiv",
        "IEEE Xplore",
    ]

    provider_status = []

    all_papers: list[
        dict[str, Any]
    ] = []

    for provider_name, result in zip(
        provider_names,
        results,
    ):
        provider_status.append(
            _provider_status(
                result,
                provider_name,
            )
        )

        if isinstance(
            result,
            Exception,
        ):
            continue

        if not isinstance(
            result,
            dict,
        ):
            continue

        papers = result.get(
            "papers",
            [],
        )

        if isinstance(
            papers,
            list,
        ):
            all_papers.extend(
                paper
                for paper in papers
                if isinstance(
                    paper,
                    dict,
                )
            )

    raw_total = len(
        all_papers
    )

    unique_papers, duplicate_count = (
        deduplicate_papers(
            all_papers
        )
    )

    for paper in unique_papers:
        _rank_paper(
            paper,
            query,
            year_to,
        )

    unique_papers.sort(
        key=lambda paper: (
            paper.get(
                "ranking",
                {},
            ).get(
                "final_score",
                0.0,
            ),
            paper.get(
                "citation_count",
                0,
            ),
        ),
        reverse=True,
    )

    selected_papers = unique_papers[
        :max_results
    ]

    provider_distribution = (
        _provider_distribution(
            selected_papers
        )
    )

    open_access_count = 0

    for paper in selected_papers:
        raw_metadata = paper.get(
            "raw_metadata",
            {},
        ) or {}

        is_oa = raw_metadata.get(
            "is_oa"
        )

        pdf_url = raw_metadata.get(
            "open_access_pdf"
        )

        if is_oa is True or pdf_url:
            open_access_count += 1

    highly_cited_count = sum(
        1
        for paper in selected_papers
        if (
            _safe_int(
                paper.get(
                    "citation_count"
                )
            )
            or 0
        ) >= 100
    )

    source_verified_metadata_count = sum(
        1
        for paper in selected_papers
        if (
            paper.get(
                "evidence",
                {},
            ).get(
                "metadata_verified",
                False,
            )
        )
    )

    multi_source_count = sum(
        1
        for paper in selected_papers
        if len(
            paper.get(
                "providers",
                [],
            )
        ) > 1
    )

    failed_sources = [
        status
        for status in provider_status
        if status.get(
            "status"
        ) == "failed"
    ]

    successful_sources = [
        status
        for status in provider_status
        if status.get(
            "status"
        ) in {
            "success",
            "not_configured",
        }
    ]

    completed_at = datetime.utcnow()

    retrieval_duration_seconds = round(
        (
            completed_at
            - started_at
        ).total_seconds(),
        3,
    )

    return {
        "query": query,
        "year_from": year_from,
        "year_to": year_to,
        "papers": selected_papers,
        "stats": {
            "status": (
                "completed"
                if selected_papers
                else "completed_no_results"
            ),
            "raw_results": raw_total,
            "unique_results": len(
                unique_papers
            ),
            "returned_results": len(
                selected_papers
            ),
            "duplicates_removed": (
                duplicate_count
            ),
            "open_access_count": (
                open_access_count
            ),
            "highly_cited_count": (
                highly_cited_count
            ),
            "metadata_verified_count": (
                source_verified_metadata_count
            ),
            "multi_source_records": (
                multi_source_count
            ),
            "provider_count": len(
                provider_status
            ),
            "successful_provider_count": len(
                successful_sources
            ),
            "failed_provider_count": len(
                failed_sources
            ),
            "retrieval_duration_seconds": (
                retrieval_duration_seconds
            ),
        },
        "provider_stats": provider_status,
        "provider_distribution": (
            provider_distribution
        ),
        "year_distribution": (
            _year_distribution(
                selected_papers
            )
        ),
        "retrieval_modes": [
            "keyword",
            "semantic",
            "bibliographic",
            "official_api",
        ],
        "source_registry": {
            "OpenAlex": {
                "enabled": True,
                "type": "scholarly_index",
                "official_api": True,
                "status": next(
                    (
                        item.get(
                            "status"
                        )
                        for item in provider_status
                        if item.get(
                            "provider"
                        ) == "OpenAlex"
                    ),
                    "unknown",
                ),
            },
            "Crossref": {
                "enabled": True,
                "type": "scholarly_registry",
                "official_api": True,
                "status": next(
                    (
                        item.get(
                            "status"
                        )
                        for item in provider_status
                        if item.get(
                            "provider"
                        ) == "Crossref"
                    ),
                    "unknown",
                ),
            },
            "Semantic Scholar": {
                "enabled": True,
                "type": "scholarly_graph",
                "official_api": True,
                "api_key_configured": bool(
                    SEMANTIC_SCHOLAR_API_KEY
                ),
                "status": next(
                    (
                        item.get(
                            "status"
                        )
                        for item in provider_status
                        if item.get(
                            "provider"
                        ) == "Semantic Scholar"
                    ),
                    "unknown",
                ),
            },
            "PubMed": {
                "enabled": True,
                "type": "biomedical_index",
                "official_api": True,
                "status": next(
                    (
                        item.get(
                            "status"
                        )
                        for item in provider_status
                        if item.get(
                            "provider"
                        ) == "PubMed"
                    ),
                    "unknown",
                ),
            },
            "arXiv": {
                "enabled": True,
                "type": "preprint_repository",
                "official_api": True,
                "status": next(
                    (
                        item.get(
                            "status"
                        )
                        for item in provider_status
                        if item.get(
                            "provider"
                        ) == "arXiv"
                    ),
                    "unknown",
                ),
            },
            "IEEE Xplore": {
                "enabled": bool(
                    IEEE_XPLORE_API_KEY
                ),
                "type": "technical_index",
                "official_api": True,
                "api_key_configured": bool(
                    IEEE_XPLORE_API_KEY
                ),
                "status": next(
                    (
                        item.get(
                            "status"
                        )
                        for item in provider_status
                        if item.get(
                            "provider"
                        ) == "IEEE Xplore"
                    ),
                    "not_configured",
                ),
            },
        },
        "ranking": {
            "weights": {
                "relevance": 0.50,
                "citation": 0.20,
                "recency": 0.15,
                "source_quality": 0.15,
            },
            "note": (
                "Ranking prioritizes query relevance, "
                "citation signal, recency and source "
                "quality. Ranking is an AURA retrieval "
                "priority score, not a scientific "
                "quality or impact-factor claim."
            ),
        },
        "evidence_layer": {
            "metadata_provenance": True,
            "claim_verification": False,
            "cross_source_deduplication": True,
            "source_status_tracking": True,
            "citation_ready_records": True,
            "google_scholar_scraping": False,
            "ieee_full_text_scraping": False,
            "verification_note": (
                "AURA verifies the provenance of retrieved "
                "metadata here. It does not treat retrieval "
                "as verification of scientific claims. "
                "Downstream analysis must inspect evidence "
                "before making research conclusions."
            ),
        },
    }


# ============================================================================
# OPTIONAL COMPATIBILITY HELPERS
# ============================================================================

async def discover_literature(
    query: str,
    year_from: int = DEFAULT_YEAR_FROM,
    year_to: int = DEFAULT_YEAR_TO,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> dict[str, Any]:
    """
    Compatibility alias for callers that use
    discover_literature instead of search_literature.
    """

    return await search_literature(
        query=query,
        year_from=year_from,
        year_to=year_to,
        max_results=max_results,
    )


__all__ = [
    "search_literature",
    "discover_literature",
    "search_openalex",
    "search_openalex_semantic",
    "search_crossref",
    "search_semantic_scholar",
    "search_pubmed",
    "search_arxiv",
    "search_ieee_xplore",
    "deduplicate_papers",
    "source_quality_score",
    "recency_score",
]