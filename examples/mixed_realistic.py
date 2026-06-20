"""Example Python file with a realistic mix of real code and wrappers.

Simulates a utility module that an AI assistant might produce — some functions
do real work, some are pointless pass-throughs that should be flagged.
"""

import json
import os


# ---------------------------------------------------------------------------
# Stubs — stand-ins for external functions that would exist in a real codebase.
# These make the file importable/lintable without needing actual implementations.
# ---------------------------------------------------------------------------
def transform(x):  # noqa: ANN201
    return x


def check(x):  # noqa: ANN201
    return x

# Real function — does actual work
def load_config(path):
    with open(path) as f:
        return json.load(f)


# WRAPPER — just forwards to os.path.exists
def file_exists(path):
    return os.path.exists(path)


# Real function — has a guard + transformation
def safe_divide(a, b):
    if b == 0:
        return None
    return a / b


# WRAPPER — just forwards to json.dumps
def to_json(obj):
    return json.dumps(obj)


# Real function — does logging + call
def process_data(data):
    print(f"Processing {len(data)} items")
    return transform(data)


# WRAPPER — method wrapper pattern
class DataProcessor:
    def process(self, data):
        return transform(data)

    # Real method — has branching
    def validate(self, data):
        if not data:
            raise ValueError("Empty data")
        return check(data)
