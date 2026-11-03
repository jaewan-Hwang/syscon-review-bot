from copy import deepcopy

from src.review.structured_output import (
    REVIEW_PARTIAL_RESPONSE_FORMAT,
    build_review_response_format,
    build_scoped_partial_response_format,
)


def _walk_schema(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_schema(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_schema(value)


def test_review_response_format_is_strict_json_schema():
    response_format = build_review_response_format()

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "review_result"
    assert response_format["json_schema"]["strict"] is True


def test_review_schema_makes_every_object_closed_and_required():
    schema = build_review_response_format()["json_schema"]["schema"]

    object_nodes = [node for node in _walk_schema(schema) if "properties" in node]
    assert object_nodes
    for node in object_nodes:
        assert node["additionalProperties"] is False
        assert node["required"] == list(node["properties"])


def test_review_schema_removes_defaults_recursively():
    schema = build_review_response_format()["json_schema"]["schema"]

    assert all("default" not in node for node in _walk_schema(schema))


def test_scoped_partial_schema_limits_api_fields_without_mutating_shared_schema():
    original = deepcopy(REVIEW_PARTIAL_RESPONSE_FORMAT)
    shard = build_scoped_partial_response_format("shard-1", ["a.py", "b.py"])
    other = build_scoped_partial_response_format("shard-2", ["c.py"])

    for result, unit, paths in (
        (shard, "shard-1", ["a.py", "b.py"]),
        (other, "shard-2", ["c.py"]),
    ):
        schema = result["json_schema"]["schema"]
        assert schema["properties"]["unit_id"]["enum"] == [unit]
        assert schema["properties"]["covered_paths"]["items"]["enum"] == paths
        file_schema = schema["$defs"]["ScopedFinding"]["properties"]["file"]
        assert file_schema["anyOf"] == [
            {"type": "string", "enum": paths}, {"type": "null"}
        ]
        for node in _walk_schema(schema):
            if "properties" in node:
                assert node["required"] == list(node["properties"])
                assert node["additionalProperties"] is False

    assert REVIEW_PARTIAL_RESPONSE_FORMAT == original
    assert shard != other
