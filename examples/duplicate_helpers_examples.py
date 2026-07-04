"""Example file for Duplicate Helper Detection.

These functions SHOULD be detected as clusters by `codediet doctor`.
Each cluster shares a semantic root, same parameter count, and same
AST fingerprint (same top-level statement structure).
"""


# ---------------------------------------------------------------------------
# Cluster 1: root = "float", 1 param, all pure return-call bodies
# ---------------------------------------------------------------------------

def safe_float(x):
    return float(x)


def parse_float(x):
    return float(x)


def ensure_float(x):
    return float(x)


# ---------------------------------------------------------------------------
# Cluster 2: root = "json", 1 param, all pure return-call bodies
# ---------------------------------------------------------------------------

def to_json(obj):
    import json
    return json.dumps(obj)


def as_json(obj):
    import json
    return json.dumps(obj)


# ---------------------------------------------------------------------------
# Cluster 3: root = "items", 1 param (method — self excluded), same body
# ---------------------------------------------------------------------------

class Repository:
    def get_items(self):
        return list(self._store)

    def build_items(self):
        return list(self._store)


# ---------------------------------------------------------------------------
# These should NOT be flagged
# ---------------------------------------------------------------------------

def load_config(path):
    """Complex function — body exceeds _MAX_BODY_STMTS."""
    with open(path) as f:
        content = f.read()
    lines = content.split("\n")
    result = {}
    for line in lines:
        if "=" in line:
            k, v = line.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def process_data(data):
    """No recognised affix — no root → not in any cluster."""
    return [x * 2 for x in data]


def validate_data(data):
    """'data' root — but no matching 'safe_data' or 'parse_data' exists here."""
    return bool(data)
