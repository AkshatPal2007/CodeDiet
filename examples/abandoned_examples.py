"""Example file for Abandoned Implementation Detection.

These functions SHOULD be flagged by `codediet doctor`.
Each versioned function has a corresponding "original" in the same file.
"""


# ---------------------------------------------------------------------------
# Classic versioning — explicit _v2 / _v3
# ---------------------------------------------------------------------------

def search(query):
    """The original search function."""
    results = []
    for item in ["apple", "banana", "cherry"]:
        if query in item:
            results.append(item)
    return results


def search_v2(query):
    """Rewritten after AI suggested a 'better' approach."""
    return [item for item in ["apple", "banana", "cherry"] if query in item]


# ---------------------------------------------------------------------------
# _new suffix — post-refactor copy left behind
# ---------------------------------------------------------------------------

def parse_config(path):
    with open(path) as f:
        return f.read().split("\n")


def parse_config_new(path):
    import json
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# _final suffix — "this is definitely the last version" (until _final_v2)
# ---------------------------------------------------------------------------

def validate_email(address):
    return "@" in address


def validate_email_final(address):
    import re
    pattern = r"^[^@]+@[^@]+\.[^@]+$"
    return bool(re.match(pattern, address))


# ---------------------------------------------------------------------------
# _old suffix — kept for reference, never cleaned up
# ---------------------------------------------------------------------------

def format_date(dt):
    return dt.strftime("%Y-%m-%d")


def format_date_old(dt):
    return f"{dt.year}/{dt.month}/{dt.day}"


# ---------------------------------------------------------------------------
# _deprecated suffix — explicitly marked, but still present
# ---------------------------------------------------------------------------

def send_notification(user, msg):
    print(f"Sending to {user}: {msg}")


def send_notification_deprecated(user, msg):
    # Old SMTP-based implementation
    pass


# ---------------------------------------------------------------------------
# These should NOT be flagged — no matching base name exists in this file
# ---------------------------------------------------------------------------

def process_orders_legacy():
    """'process_orders' doesn't exist in this file — should NOT be flagged."""
    pass


def handler_v2(request):
    """'handler' doesn't exist in this file — should NOT be flagged."""
    return None
