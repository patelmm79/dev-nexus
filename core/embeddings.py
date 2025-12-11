"""
Embedding Generation Module

Generates vector embeddings for patterns using OpenAI's text-embedding models.
Supports batch processing and caching for efficiency.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text using OpenAI"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ):
        """
        Initialize embedding generator

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Embedding model to use
            dimensions: Embedding dimensions (1536 for text-embedding-3-small)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning(
                "OPENAI_API_KEY not set. Embedding generation will be unavailable."
            )
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)

        self.model = model
        self.dimensions = dimensions
        self.enabled = self.client is not None

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for single text

        Args:
            text: Input text

        Returns:
            Embedding vector or None if disabled
        """
        if not self.enabled:
            logger.debug("Embedding generation disabled (no API key)")
            return None

        try:
            # Truncate text if too long (OpenAI has 8191 token limit)
            if len(text) > 8000:
                logger.warning(f"Truncating text from {len(text)} to 8000 characters")
                text = text[:8000]

            response = self.client.embeddings.create(
                model=self.model, input=text, dimensions=self.dimensions
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def generate_embeddings_batch(
        self, texts: List[str], batch_size: int = 100
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts per batch (max 2048 for OpenAI)

        Returns:
            List of embedding vectors (None for failures)
        """
        if not self.enabled:
            logger.debug("Embedding generation disabled (no API key)")
            return [None] * len(texts)

        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            try:
                # Truncate long texts
                truncated_batch = [
                    text[:8000] if len(text) > 8000 else text for text in batch
                ]

                response = self.client.embeddings.create(
                    model=self.model,
                    input=truncated_batch,
                    dimensions=self.dimensions,
                )

                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                logger.info(f"Generated {len(batch_embeddings)} embeddings in batch")

            except Exception as e:
                logger.error(f"Failed to generate batch embeddings: {e}")
                # Add None for failed embeddings
                embeddings.extend([None] * len(batch))

        return embeddings

    def generate_pattern_embedding(self, pattern: Dict[str, Any]) -> Optional[List[float]]:
        """
        Generate embedding for a pattern

        Combines pattern name, description, and context into a single text

        Args:
            pattern: Pattern dictionary with name, description, context

        Returns:
            Embedding vector or None
        """
        # Combine pattern fields for embedding
        text_parts = []

        if "name" in pattern and pattern["name"]:
            text_parts.append(f"Pattern: {pattern['name']}")

        if "description" in pattern and pattern["description"]:
            text_parts.append(f"Description: {pattern['description']}")

        if "context" in pattern and pattern["context"]:
            text_parts.append(f"Context: {pattern['context']}")

        combined_text = "\n".join(text_parts)

        if not combined_text:
            logger.warning("Pattern has no text fields for embedding")
            return None

        return self.generate_embedding(combined_text)

    def calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1, higher is more similar)
        """
        try:
            import numpy as np

            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)

            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, float(similarity)))

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0


# Singleton instance
_embedding_generator: Optional[EmbeddingGenerator] = None


def get_embedding_generator() -> EmbeddingGenerator:
    """Get embedding generator singleton"""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = EmbeddingGenerator()
    return _embedding_generator


async def generate_and_store_embeddings(
    db_manager,
    batch_size: int = 50,
    max_patterns: int = 1000,
) -> Dict[str, Any]:
    """
    Generate embeddings for patterns that don't have them

    Args:
        db_manager: DatabaseManager instance
        batch_size: Number of patterns to process at once
        max_patterns: Maximum patterns to process in one run

    Returns:
        Statistics about embedding generation
    """
    generator = get_embedding_generator()

    if not generator.enabled:
        return {
            "success": False,
            "message": "Embedding generator not enabled (missing OPENAI_API_KEY)",
            "processed": 0,
        }

    # Get patterns without embeddings
    patterns = await db_manager.get_patterns_without_embeddings(limit=max_patterns)

    if not patterns:
        return {
            "success": True,
            "message": "All patterns have embeddings",
            "processed": 0,
        }

    logger.info(f"Generating embeddings for {len(patterns)} patterns")

    # Generate embeddings in batches
    processed = 0
    failed = 0

    for i in range(0, len(patterns), batch_size):
        batch = patterns[i : i + batch_size]

        # Prepare texts for batch embedding
        texts = [
            f"Pattern: {p['name']}\nDescription: {p['description']}\nContext: {p['context']}"
            for p in batch
        ]

        # Generate embeddings
        embeddings = generator.generate_embeddings_batch(texts, batch_size=batch_size)

        # Store embeddings
        for pattern, embedding in zip(batch, embeddings):
            if embedding:
                try:
                    await db_manager.update_pattern_embedding(
                        pattern["id"], embedding
                    )
                    processed += 1
                except Exception as e:
                    logger.error(
                        f"Failed to store embedding for pattern {pattern['id']}: {e}"
                    )
                    failed += 1
            else:
                failed += 1

        logger.info(f"Processed batch: {processed} success, {failed} failed")

    return {
        "success": True,
        "message": f"Generated embeddings for {processed} patterns",
        "processed": processed,
        "failed": failed,
        "total": len(patterns),
    }
