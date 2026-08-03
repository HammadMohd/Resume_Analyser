"""Embedding search — semantic similarity using dense vectors.

Embeddings convert text into dense vectors (lists of numbers) that
capture semantic meaning. Similar meanings produce similar vectors.

Why embeddings?
- Captures synonyms ("ETL" ≈ "Data Pipeline")
- Understands context ("Python the language" vs "python the snake")
- Enables semantic matching beyond exact keywords

How it works:
1. Encode text → vector (e.g., [0.12, -0.45, 0.78, ...])
2. Compare vectors using cosine similarity
3. Score 1.0 = identical meaning, 0.0 = unrelated

Limitations:
- Slower than BM25 (requires model inference)
- Requires pre-trained model
- May not capture domain-specific jargon perfectly
"""

import math
import re

from backend.schemas.search import EmbeddingResult
from backend.utils.logging import get_logger

logger = get_logger(__name__)

# Try to import sentence-transformers (optional)
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.info("sentence-transformers not available, using lightweight embeddings")


class EmbeddingSearch:
    """Semantic search using dense embeddings.

    Supports two modes:
    1. Full mode: Uses sentence-transformers (requires installation)
    2. Lightweight mode: Uses TF-IDF-like vectorization (no dependencies)
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize embedding model.

        Args:
            model_name: Name of sentence-transformers model to use.
        """
        self.model_name = model_name
        self.model = None
        self.use_full_model = SENTENCE_TRANSFORMERS_AVAILABLE

        if self.use_full_model:
            try:
                self.model = SentenceTransformer(model_name)
                logger.info("Loaded embedding model: %s", model_name)
            except Exception as e:
                logger.warning("Failed to load model %s: %s", model_name, str(e))
                self.use_full_model = False

    def encode(self, text: str) -> list[float]:
        """Encode text into embedding vector.

        Args:
            text: Text to encode.

        Returns:
            Embedding vector.
        """
        if self.use_full_model and self.model:
            embedding = self.model.encode(text)
            return embedding.tolist()
        else:
            return self._lightweight_encode(text)

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Similarity score (-1 to 1, where 1 = identical).
        """
        if len(vec1) != len(vec2):
            # Pad shorter vector
            max_len = max(len(vec1), len(vec2))
            vec1 = vec1 + [0.0] * (max_len - len(vec1))
            vec2 = vec2 + [0.0] * (max_len - len(vec2))

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def score(self, text1: str, text2: str) -> EmbeddingResult:
        """Calculate embedding similarity between two texts.

        Args:
            text1: First text (e.g., resume).
            text2: Second text (e.g., JD).

        Returns:
            EmbeddingResult with similarity score.
        """
        vec1 = self.encode(text1)
        vec2 = self.encode(text2)

        similarity = self.cosine_similarity(vec1, vec2)

        # Normalize to 0-1 range (cosine similarity is -1 to 1)
        score = (similarity + 1) / 2

        logger.info("Embedding similarity: %.4f (normalized: %.4f)", similarity, score)

        return EmbeddingResult(
            score=score,
            resume_embedding_dim=len(vec1),
            jd_embedding_dim=len(vec2),
        )

    def _lightweight_encode(self, text: str) -> list[float]:
        """Lightweight TF-IDF-like encoding without ML dependencies.

        Creates a simple feature vector based on term frequencies.
        """
        # Tokenize
        terms = re.findall(r"\b[a-z]{2,}\b", text.lower())

        # Create vocabulary from common terms
        vocab = self._get_vocabulary()
        vocab_size = len(vocab)

        # Create TF vector
        tf = {}
        for term in terms:
            tf[term] = tf.get(term, 0) + 1

        # Create vector
        vector = [0.0] * vocab_size
        for i, vocab_term in enumerate(vocab):
            if vocab_term in tf:
                # Log-normalized TF
                vector[i] = 1 + math.log(tf[vocab_term]) if tf[vocab_term] > 0 else 0

        return vector

    def _get_vocabulary(self) -> list[str]:
        """Get vocabulary for lightweight encoding."""
        # Common technical terms and skills
        return [
            "python", "java", "javascript", "typescript", "react", "angular",
            "vue", "node", "django", "flask", "fastapi", "spring", "rails",
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "git", "github", "jenkins", "ci", "cd", "devops", "agile",
            "scrum", "REST", "API", "microservices", "serverless", "lambda",
            "machine", "learning", "deep", "data", "engineer", "pipeline",
            "etl", "spark", "kafka", "hadoop", "sql", "nosql", "graphql",
            "testing", "unit", "integration", "automation", "selenium",
            "leadership", "communication", "teamwork", "problem", "solving",
            "experience", "senior", "junior", "lead", "manager", "developer",
            "engineer", "architect", "design", "develop", "implement", "build",
            "create", "manage", "lead", "collaborate", "deliver", "improve",
        ]

    def score_skills(self, resume_skills: list[str], jd_skills: list[str]) -> float:
        """Calculate embedding similarity for skill lists.

        Args:
            resume_skills: Skills from resume.
            jd_skills: Skills from job description.

        Returns:
            Skill similarity score (0-1).
        """
        if not jd_skills or not resume_skills:
            return 0.0

        resume_text = ", ".join(resume_skills)
        jd_text = ", ".join(jd_skills)

        result = self.score(resume_text, jd_text)
        return result.score
