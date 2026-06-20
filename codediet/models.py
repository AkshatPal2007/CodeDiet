from dataclasses import dataclass
from enum import Enum


class FindingClass(Enum):
    """Classification of a finding's reliability level.

    FACT     — deterministic, mechanically defensible claim derived from the
               AST alone. True by construction, 100% of the time.
    REVIEW   — heuristic signal that something is worth a human looking at.
               Makes no claim about what the inspection will find.
    """

    FACT = "fact"
    REVIEW = "review"


@dataclass
class Finding:
    """Represents a single detection finding from any detector.

    Attributes:
        detector:        Name of the detector that produced this finding
                         (e.g. "wrapper", "duplicate_helper_cluster").
        classification:  FindingClass.FACT or FindingClass.REVIEW.
        file:            Path to the source file where the finding was detected.
        line:            1-indexed line number of the finding.
        message:         Human-readable description of the finding. Must
                         conform to the wording rules in CLAUDE.md §5 for the
                         relevant detector.
        evidence:        Structured, detector-specific supporting data.
                         For wrappers: {"function": ..., "target": ...}.
    """

    detector: str
    classification: FindingClass
    file: str
    line: int
    message: str
    evidence: dict
