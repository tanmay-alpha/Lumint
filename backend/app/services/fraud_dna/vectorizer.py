from typing import List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def build_tfidf_matrix(
    fingerprints: List[dict],
) -> Tuple[Optional[np.ndarray], Optional[TfidfVectorizer], List[str]]:
    """
    Returns (matrix, vectorizer, event_ids).
    Returns (None, None, []) if fewer than 2 fingerprints.
    """
    if len(fingerprints) < 2:
        return None, None, []

    texts = [fp.get("fingerprint_text", "") for fp in fingerprints]
    event_ids = [fp.get("event_id", "") for fp in fingerprints]

    # Filter out empty texts
    valid = [(t, eid) for t, eid in zip(texts, event_ids) if t.strip()]
    if len(valid) < 2:
        return None, None, []

    texts_clean, event_ids_clean = zip(*valid)

    vectorizer = TfidfVectorizer(
        min_df=1,
        max_features=500,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(list(texts_clean))
    return matrix, vectorizer, list(event_ids_clean)