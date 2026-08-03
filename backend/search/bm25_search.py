"""BM25 search — keyword-based document ranking.

BM25 (Best Matching 25) is a probabilistic information retrieval
algorithm that scores documents based on term frequency and
inverse document frequency.

Key concepts:
- TF (Term Frequency): How often a term appears in a document
- IDF (Inverse Document Frequency): How rare a term is across documents
- BM25 combines TF and IDF with length normalization

Why BM25?
- Fast, no model inference required
- Excellent for exact keyword matching
- Industry standard for search engines
- Works well for skill matching ("Python" = "Python")

Limitations:
- Cannot understand synonyms ("ETL" ≠ "Data Pipeline")
- Doesn't capture semantic meaning
"""

import math
import re

from backend.schemas.search import BM25Result
from backend.utils.logging import get_logger

logger = get_logger(__name__)


class BM25Search:
    """BM25 keyword search engine.

    Attributes:
        k1: Term frequency saturation parameter (default 1.5)
        b: Length normalization parameter (default 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        """Initialize BM25 parameters.

        Args:
            k1: Controls term frequency saturation. Higher = more weight on TF.
            b: Controls length normalization. 0 = no normalization, 1 = full.
        """
        self.k1 = k1
        self.b = b

    def score(self, query: str, document: str) -> BM25Result:
        """Calculate BM25 score between query and document.

        Args:
            query: The search query (e.g., JD text).
            document: The document to score (e.g., resume text).

        Returns:
            BM25Result with score and matched terms.
        """
        query_terms = self._tokenize(query)
        doc_terms = self._tokenize(document)
        doc_len = len(doc_terms)

        if not query_terms or not doc_terms:
            return BM25Result(score=0.0)

        # Calculate average document length (using this single doc)
        avg_doc_len = doc_len

        # Calculate IDF for each query term (simplified: using single doc)
        # In production, IDF would be calculated across a corpus
        idf = self._calculate_idf(query_terms, doc_len)

        # Calculate TF for each term in document
        tf = self._calculate_tf(doc_terms)

        # Calculate BM25 score
        score = 0.0
        matched_terms = []
        term_scores = {}

        for term in query_terms:
            if term in tf:
                term_tf = tf[term]
                term_idf = idf.get(term, 0)

                # BM25 formula
                numerator = term_tf * (self.k1 + 1)
                denominator = term_tf + self.k1 * (
                    1 - self.b + self.b * (doc_len / avg_doc_len)
                )
                term_score = term_idf * (numerator / denominator)

                score += term_score
                matched_terms.append(term)
                term_scores[term] = round(term_score, 4)

        # Normalize score to 0-1 range
        max_possible_score = sum(idf.values()) if idf else 1
        normalized_score = min(1.0, score / max_possible_score) if max_possible_score > 0 else 0

        logger.info("BM25 score: %.4f (%d matched terms)", normalized_score, len(matched_terms))

        return BM25Result(
            score=normalized_score,
            matched_terms=matched_terms,
            term_scores=term_scores,
        )

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase terms."""
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r"[^a-zA-Z0-9\s+#]", " ", text.lower())
        # Split on whitespace
        terms = text.split()
        # Remove very short terms
        return [t for t in terms if len(t) > 1]

    def _calculate_tf(self, terms: list[str]) -> dict[str, float]:
        """Calculate term frequency for each term."""
        tf: dict[str, float] = {}
        for term in terms:
            tf[term] = tf.get(term, 0) + 1
        return tf

    def _calculate_idf(self, query_terms: list[str], doc_len: int) -> dict[str, float]:
        """Calculate IDF for query terms.

        Simplified IDF using single document.
        In production, this would use a corpus of documents.
        """
        idf = {}
        for term in set(query_terms):
            # Simplified: IDF = log(N / df) where N=1 (single doc)
            # If term appears in document, df=1, so IDF = log(1) = 0
            # We use a small constant to avoid zero
            idf[term] = 1.0  # Simplified for single-document matching
        return idf

    def score_skills(self, resume_skills: list[str], jd_skills: list[str]) -> float:
        """Calculate BM25 score specifically for skill matching.

        Args:
            resume_skills: Skills from resume.
            jd_skills: Skills from job description.

        Returns:
            Skill match score (0-1).
        """
        if not jd_skills:
            return 0.0

        # Convert skills to text for BM25
        resume_text = " ".join(resume_skills)
        jd_text = " ".join(jd_skills)

        result = self.score(jd_text, resume_text)
        return result.score
