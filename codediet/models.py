from dataclasses import dataclass


@dataclass
class Finding:
    """Represents a single detection finding from any detector.

    Attributes:
        kind: The detector kind that produced this finding (e.g. "wrapper").
        file: Path to the source file where the finding was detected.
        line: 1-indexed line number of the finding.
        function: The name of the function that was flagged.
        target: The name of the function/builtin being forwarded to.
    """

    kind: str
    file: str
    line: int
    function: str
    target: str
