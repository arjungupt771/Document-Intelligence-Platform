from abc import ABC, abstractmethod


class DriftDetector(ABC):
    """Marker base -- concrete detectors in detectors.py each expose their own detect() signature
    (the inputs differ per dimension: a numeric field needs values, embedding needs a centroid, etc.),
    so this stays a documentation-only interface rather than one shared abstract method."""


class BaselineNotEstablishedError(Exception):
    def __init__(self, document_type: str):
        super().__init__(f"No active baseline snapshot exists for document type '{document_type}'.")