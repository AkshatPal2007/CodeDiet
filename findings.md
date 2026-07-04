# CodeDiet Findings — .
Generated: 2026-06-21T06:17:44Z
Detector(s) run: wrapper

## Facts
(deterministic — these are structurally true as written)

### Wrapper
- `_validation/fastapi/docs_src/custom_docs_ui/tutorial001_py310.py:23` — swagger_ui_redirect -> get_swagger_ui_oauth2_redirect_html

### Wrapper
- `_validation/fastapi/docs_src/custom_docs_ui/tutorial002_py310.py:26` — swagger_ui_redirect -> get_swagger_ui_oauth2_redirect_html

### Wrapper
- `_validation/fastapi/docs_src/custom_request_and_route/tutorial002_an_py310.py:29` — sum_numbers -> sum

### Wrapper
- `_validation/fastapi/docs_src/custom_request_and_route/tutorial002_py310.py:28` — sum_numbers -> sum

### Wrapper
- `_validation/fastapi/docs_src/custom_response/tutorial004_py310.py:22` — read_items -> generate_html_response

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial004_an_py310.py:58` — verify_password -> password_hash.verify

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial004_an_py310.py:62` — get_password_hash -> password_hash.hash

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial004_py310.py:57` — verify_password -> password_hash.verify

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial004_py310.py:61` — get_password_hash -> password_hash.hash

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial005_an_py310.py:73` — verify_password -> password_hash.verify

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial005_an_py310.py:77` — get_password_hash -> password_hash.hash

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial005_py310.py:72` — verify_password -> password_hash.verify

### Wrapper
- `_validation/fastapi/docs_src/security/tutorial005_py310.py:76` — get_password_hash -> password_hash.hash

### Wrapper
- `_validation/fastapi/docs_src/settings/app02_an_py310/main.py:12` — get_settings -> Settings

### Wrapper
- `_validation/fastapi/docs_src/settings/app02_py310/main.py:11` — get_settings -> Settings

### Wrapper
- `_validation/fastapi/docs_src/settings/app03_an_py310/main.py:12` — get_settings -> config.Settings

### Wrapper
- `_validation/fastapi/docs_src/settings/app03_py310/main.py:11` — get_settings -> config.Settings

### Wrapper
- `_validation/fastapi/fastapi/routing.py:195` — __aenter__ -> self._cm.__enter__

### Wrapper
- `_validation/fastapi/fastapi/routing.py:198` — __aexit__ -> self._cm.__exit__

### Wrapper
- `_validation/fastapi/tests/test_dependency_after_yield_streaming.py:73` — get_broken_session_data -> list

### Wrapper
- `_validation/fastapi/tests/test_dependency_wrapped.py:19` — wrapper -> func

### Wrapper
- `_validation/fastapi/tests/test_inherited_custom_class.py:47` — serialize_a_uuid -> str

### Wrapper
- `_validation/fastapi/tests/test_response_model_default_factory.py:25` — response_model_has_default_factory_return_model -> ResponseModel

### Wrapper
- `_validation/fastapi/tests/test_router_events.py:20` — state -> State

### Wrapper
- `_validation/fastapi/tests/test_security_scopes.py:35` — client_fixture -> TestClient

### Wrapper
- `_validation/fastapi/tests/test_security_scopes_sub_dependency.py:73` — client_fixture -> TestClient

### Wrapper
- `_validation/fastapi/tests/test_wrapped_method_forward_reference.py:11` — method -> f

### Wrapper
- `_validation/flask/examples/tutorial/tests/conftest.py:61` — auth -> AuthActions

### Wrapper
- `_validation/flask/tests/test_basic.py:1180` — from_wsgi -> NotFound

### Wrapper
- `_validation/flask/tests/test_blueprints.py:139` — bar -> str

### Wrapper
- `_validation/flask/tests/test_blueprints.py:277` — something -> str

### Wrapper
- `_validation/flask/tests/test_blueprints.py:694` — bp_page -> template_string

### Wrapper
- `_validation/flask/tests/test_blueprints.py:698` — app_page -> template_string

### Wrapper
- `_validation/flask/tests/test_cli.py:37` — runner -> CliRunner

### Wrapper
- `_validation/flask/tests/test_json.py:41` — return_json -> flask.request.get_json

### Wrapper
- `_validation/flask/tests/test_json_tag.py:58` — to_python -> Foo

### Wrapper
- `_validation/flask/tests/test_user_error_handler.py:289` — handle_exception -> self.report_error

### Wrapper
- `examples/mixed_realistic.py:29` — file_exists -> os.path.exists

### Wrapper
- `examples/mixed_realistic.py:41` — to_json -> json.dumps

### Wrapper
- `examples/mixed_realistic.py:53` — process -> transform

### Wrapper
- `examples/obvious_wrappers.py:7` — parse_float -> float

### Wrapper
- `examples/obvious_wrappers.py:11` — parse_int -> int

### Wrapper
- `examples/obvious_wrappers.py:15` — stringify -> str

### Wrapper
- `examples/obvious_wrappers.py:19` — get_length -> len

### Wrapper
- `examples/obvious_wrappers.py:23` — sort_list -> sorted

## Review Recommendations
(heuristic signals — worth a look, not a claim about the outcome)

_None in this run._

---
## Summary
- 45 Facts
- 0 Review Recommendations
- 1232 files scanned

---
## LLM Hand-off Prompt
_Copy the block below and paste it into your own coding assistant._

```text
The following is output from CodeDiet, a read-only static analysis tool.
CodeDiet made no changes to this codebase. It performed purely structural,
deterministic static analysis — no LLMs, no embeddings, no probabilistic
inference of any kind was used to produce these findings.

Findings are split into two categories. Please treat them differently:

FACTS (structurally confirmed — true as written, by construction):
- _validation/fastapi/docs_src/custom_docs_ui/tutorial001_py310.py:23 — `swagger_ui_redirect` is a pure pass-through wrapper around `get_swagger_ui_oauth2_redirect_html`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/custom_docs_ui/tutorial002_py310.py:26 — `swagger_ui_redirect` is a pure pass-through wrapper around `get_swagger_ui_oauth2_redirect_html`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/custom_request_and_route/tutorial002_an_py310.py:29 — `sum_numbers` is a pure pass-through wrapper around `sum`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/custom_request_and_route/tutorial002_py310.py:28 — `sum_numbers` is a pure pass-through wrapper around `sum`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/custom_response/tutorial004_py310.py:22 — `read_items` is a pure pass-through wrapper around `generate_html_response`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial004_an_py310.py:58 — `verify_password` is a pure pass-through wrapper around `password_hash.verify`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial004_an_py310.py:62 — `get_password_hash` is a pure pass-through wrapper around `password_hash.hash`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial004_py310.py:57 — `verify_password` is a pure pass-through wrapper around `password_hash.verify`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial004_py310.py:61 — `get_password_hash` is a pure pass-through wrapper around `password_hash.hash`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial005_an_py310.py:73 — `verify_password` is a pure pass-through wrapper around `password_hash.verify`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial005_an_py310.py:77 — `get_password_hash` is a pure pass-through wrapper around `password_hash.hash`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial005_py310.py:72 — `verify_password` is a pure pass-through wrapper around `password_hash.verify`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/security/tutorial005_py310.py:76 — `get_password_hash` is a pure pass-through wrapper around `password_hash.hash`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/settings/app02_an_py310/main.py:12 — `get_settings` is a pure pass-through wrapper around `Settings`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/settings/app02_py310/main.py:11 — `get_settings` is a pure pass-through wrapper around `Settings`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/settings/app03_an_py310/main.py:12 — `get_settings` is a pure pass-through wrapper around `config.Settings`. Consider whether it can be inlined or removed.
- _validation/fastapi/docs_src/settings/app03_py310/main.py:11 — `get_settings` is a pure pass-through wrapper around `config.Settings`. Consider whether it can be inlined or removed.
- _validation/fastapi/fastapi/routing.py:195 — `__aenter__` is a pure pass-through wrapper around `self._cm.__enter__`. Consider whether it can be inlined or removed.
- _validation/fastapi/fastapi/routing.py:198 — `__aexit__` is a pure pass-through wrapper around `self._cm.__exit__`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_dependency_after_yield_streaming.py:73 — `get_broken_session_data` is a pure pass-through wrapper around `list`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_dependency_wrapped.py:19 — `wrapper` is a pure pass-through wrapper around `func`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_inherited_custom_class.py:47 — `serialize_a_uuid` is a pure pass-through wrapper around `str`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_response_model_default_factory.py:25 — `response_model_has_default_factory_return_model` is a pure pass-through wrapper around `ResponseModel`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_router_events.py:20 — `state` is a pure pass-through wrapper around `State`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_security_scopes.py:35 — `client_fixture` is a pure pass-through wrapper around `TestClient`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_security_scopes_sub_dependency.py:73 — `client_fixture` is a pure pass-through wrapper around `TestClient`. Consider whether it can be inlined or removed.
- _validation/fastapi/tests/test_wrapped_method_forward_reference.py:11 — `method` is a pure pass-through wrapper around `f`. Consider whether it can be inlined or removed.
- _validation/flask/examples/tutorial/tests/conftest.py:61 — `auth` is a pure pass-through wrapper around `AuthActions`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_basic.py:1180 — `from_wsgi` is a pure pass-through wrapper around `NotFound`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_blueprints.py:139 — `bar` is a pure pass-through wrapper around `str`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_blueprints.py:277 — `something` is a pure pass-through wrapper around `str`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_blueprints.py:694 — `bp_page` is a pure pass-through wrapper around `template_string`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_blueprints.py:698 — `app_page` is a pure pass-through wrapper around `template_string`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_cli.py:37 — `runner` is a pure pass-through wrapper around `CliRunner`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_json.py:41 — `return_json` is a pure pass-through wrapper around `flask.request.get_json`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_json_tag.py:58 — `to_python` is a pure pass-through wrapper around `Foo`. Consider whether it can be inlined or removed.
- _validation/flask/tests/test_user_error_handler.py:289 — `handle_exception` is a pure pass-through wrapper around `self.report_error`. Consider whether it can be inlined or removed.
- examples/mixed_realistic.py:29 — `file_exists` is a pure pass-through wrapper around `os.path.exists`. Consider whether it can be inlined or removed.
- examples/mixed_realistic.py:41 — `to_json` is a pure pass-through wrapper around `json.dumps`. Consider whether it can be inlined or removed.
- examples/mixed_realistic.py:53 — `process` is a pure pass-through wrapper around `transform`. Consider whether it can be inlined or removed.
- examples/obvious_wrappers.py:7 — `parse_float` is a pure pass-through wrapper around `float`. Consider whether it can be inlined or removed.
- examples/obvious_wrappers.py:11 — `parse_int` is a pure pass-through wrapper around `int`. Consider whether it can be inlined or removed.
- examples/obvious_wrappers.py:15 — `stringify` is a pure pass-through wrapper around `str`. Consider whether it can be inlined or removed.
- examples/obvious_wrappers.py:19 — `get_length` is a pure pass-through wrapper around `len`. Consider whether it can be inlined or removed.
- examples/obvious_wrappers.py:23 — `sort_list` is a pure pass-through wrapper around `sorted`. Consider whether it can be inlined or removed.

REVIEW RECOMMENDATIONS (heuristic signals — investigate before acting,
do not assume these are confirmed issues):
(none in this run)

For FACTS, you may propose a direct fix (for example, inlining a pure
pass-through wrapper) if it is appropriate for the context.

For REVIEW RECOMMENDATIONS, please investigate first and report back what
you find — do not modify code based on these signals alone. Confirm whether
the flagged items are genuinely redundant or problematic before proposing
any change.

Please summarize your proposed plan before making any edits.
```
