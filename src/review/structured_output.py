from copy import deepcopy
from typing import Any

from src.models.review import ReviewResult
from src.models.review_pipeline import ReviewPartial


def _make_strict(node: Any) -> None:
    if isinstance(node, dict):
        node.pop("default", None)
        properties = node.get("properties")
        if isinstance(properties, dict):
            node["required"] = list(properties)
            node["additionalProperties"] = False
        for value in node.values():
            _make_strict(value)
    elif isinstance(node, list):
        for value in node:
            _make_strict(value)


def build_model_response_format(model: type, name: str) -> dict[str, Any]:
    schema = deepcopy(model.model_json_schema())
    _make_strict(schema)
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": schema,
        },
    }


def build_review_response_format() -> dict[str, Any]:
    return build_model_response_format(ReviewResult, "review_result")


REVIEW_RESPONSE_FORMAT = build_review_response_format()
REVIEW_PARTIAL_RESPONSE_FORMAT = build_model_response_format(
    ReviewPartial, "review_partial"
)


def build_scoped_partial_response_format(
    unit_id: str, assigned_paths: list[str]
) -> dict[str, Any]:
    response_format = deepcopy(REVIEW_PARTIAL_RESPONSE_FORMAT)
    schema = response_format["json_schema"]["schema"]
    schema["properties"]["unit_id"]["enum"] = [unit_id]
    schema["properties"]["covered_paths"]["items"]["enum"] = list(assigned_paths)
    file_options = schema["$defs"]["ScopedFinding"]["properties"]["file"]["anyOf"]
    next(option for option in file_options if option["type"] == "string")["enum"] = list(
        assigned_paths
    )
    return response_format
