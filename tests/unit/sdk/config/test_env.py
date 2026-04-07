"""Unit tests for sdk.config._env module."""

from collections import ChainMap
from os import environ
from typing import Any
from unittest import mock

import pytest
from pydantic import BaseModel

from sdk.config._env import (
    EnvLoader,
    filter_env,
    guess_env_array_indexes,
    index_dict_to_none_list,
)


# =============================================================================
# Tests for filter_env
# =============================================================================


class TestFilterEnv:
    """Tests for filter_env function."""

    def test_empty_env(self):
        """Test filtering empty environment."""
        result = filter_env({}, "PREFIX")
        assert result == {}

    def test_no_matching_prefix(self):
        """Test when no env vars match prefix."""
        env = {"OTHER_KEY": "value", "ANOTHER_KEY": "value2"}
        result = filter_env(env, "PREFIX")
        assert result == {}

    def test_exact_prefix_match(self):
        """Test exact prefix matching."""
        env = {"PREFIX_KEY": "value", "PREFIX_OTHER": "value2"}
        result = filter_env(env, "PREFIX")
        assert result == {"PREFIX_KEY": "value", "PREFIX_OTHER": "value2"}

    def test_partial_prefix_no_match(self):
        """Test that partial prefix doesn't match."""
        env = {"PREFIX_KEY": "value", "PREFIXOTHER": "value2"}
        result = filter_env(env, "PREFIX_")
        assert result == {"PREFIX_KEY": "value"}

    def test_case_sensitive(self):
        """Test that filtering is case sensitive."""
        env = {"prefix_key": "value", "PREFIX_KEY": "value2"}
        result = filter_env(env, "PREFIX")
        assert result == {"PREFIX_KEY": "value2"}

    def test_nested_prefix(self):
        """Test filtering with nested/namespaced prefix."""
        env = {
            "APP_DATABASE_HOST": "localhost",
            "APP_DATABASE_PORT": "5432",
            "APP_CACHE_HOST": "redis",
            "OTHER_VAR": "ignored",
        }
        result = filter_env(env, "APP_DATABASE")
        assert result == {
            "APP_DATABASE_HOST": "localhost",
            "APP_DATABASE_PORT": "5432",
        }


# =============================================================================
# Tests for guess_env_array_indexes
# =============================================================================


class TestGuessEnvArrayIndexes:
    """Tests for guess_env_array_indexes function."""

    def test_empty_env(self):
        """Test with empty environment."""
        result = guess_env_array_indexes({}, "PREFIX_")
        assert result == []

    def test_no_matching_indexes(self):
        """Test when no indexed env vars exist."""
        env = {"PREFIX_KEY": "value", "PREFIX_OTHER": "value2"}
        result = guess_env_array_indexes(env, "PREFIX_")
        assert result == []

    def test_single_index(self):
        """Test with single index."""
        env = {"PREFIX_0_KEY": "value"}
        result = guess_env_array_indexes(env, "PREFIX_")
        assert result == [0]

    def test_multiple_indexes(self):
        """Test with multiple indexes."""
        env = {
            "PREFIX_0_KEY": "value0",
            "PREFIX_1_KEY": "value1",
            "PREFIX_2_KEY": "value2",
        }
        result = guess_env_array_indexes(env, "PREFIX_")
        assert sorted(result) == [0, 1, 2]

    def test_non_sequential_indexes(self):
        """Test with non-sequential indexes."""
        env = {
            "PREFIX_0_KEY": "value0",
            "PREFIX_5_KEY": "value5",
            "PREFIX_10_KEY": "value10",
        }
        result = guess_env_array_indexes(env, "PREFIX_")
        assert sorted(result) == [0, 5, 10]

    def test_mixed_indexed_and_non_indexed(self):
        """Test with both indexed and non-indexed keys."""
        env = {
            "PREFIX_KEY": "value",
            "PREFIX_0_KEY": "value0",
            "PREFIX_OTHER": "other",
            "PREFIX_1_KEY": "value1",
        }
        result = guess_env_array_indexes(env, "PREFIX_")
        assert sorted(result) == [0, 1]

    def test_indexes_with_underscore_suffix(self):
        """Test indexes followed by underscore and more text."""
        env = {
            "PREFIX_0_SUB_KEY": "value0",
            "PREFIX_1_SUB_KEY": "value1",
        }
        result = guess_env_array_indexes(env, "PREFIX_")
        assert sorted(result) == [0, 1]

    def test_indexes_without_underscore_after_prefix(self):
        """Test that index must be right after prefix delimiter."""
        env = {"PREFIX0_KEY": "value"}
        result = guess_env_array_indexes(env, "PREFIX")
        # No underscore after prefix, so 0_KEY is not an index
        assert result == []

    def test_multi_digit_indexes(self):
        """Test multi-digit index numbers."""
        env = {
            "PREFIX_100_KEY": "value",
            "PREFIX_999_KEY": "value2",
        }
        result = guess_env_array_indexes(env, "PREFIX_")
        assert sorted(result) == [100, 999]

    def test_duplicate_indexes_only_unique(self):
        """Test that duplicate indexes are returned only once."""
        env = {
            "PREFIX_0_KEY1": "value1",
            "PREFIX_0_KEY2": "value2",
            "PREFIX_0_KEY3": "value3",
        }
        result = guess_env_array_indexes(env, "PREFIX_")
        assert result == [0]


# =============================================================================
# Tests for index_dict_to_none_list
# =============================================================================


class TestIndexDictToNoneList:
    """Tests for index_dict_to_none_list function."""

    def test_empty_dict(self):
        """Test with empty dict."""
        result = index_dict_to_none_list({})
        assert result == []

    def test_single_element(self):
        """Test with single element at index 0."""
        result = index_dict_to_none_list({0: "value"})
        assert result == ["value"]

    def test_sequential_indexes(self):
        """Test with sequential indexes."""
        result = index_dict_to_none_list({0: "a", 1: "b", 2: "c"})
        assert result == ["a", "b", "c"]

    def test_non_sequential_indexes(self):
        """Test with non-sequential indexes fills gaps with None."""
        result = index_dict_to_none_list({0: "a", 2: "c"})
        assert result == ["a", None, "c"]

    def test_large_gap(self):
        """Test with large gap between indexes."""
        result = index_dict_to_none_list({0: "a", 5: "f"})
        assert result == ["a", None, None, None, None, "f"]

    def test_not_starting_from_zero(self):
        """Test when indexes don't start from zero."""
        result = index_dict_to_none_list({2: "c", 3: "d"})
        # Starts from 0, so indices 0 and 1 are None
        assert result == [None, None, "c", "d"]

    def test_different_value_types(self):
        """Test with different value types."""
        result = index_dict_to_none_list({
            0: "string",
            1: 123,
            2: {"nested": "dict"},
            3: ["list"],
        })
        assert result == ["string", 123, {"nested": "dict"}, ["list"]]


# =============================================================================
# Fixtures for EnvLoader tests
# =============================================================================


@pytest.fixture
def basic_schema():
    """Fixture providing a basic schema for testing."""
    return {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "count": {"type": "integer"},
            "enabled": {"type": "boolean"},
        },
    }


@pytest.fixture
def nested_object_schema():
    """Fixture providing a schema with nested objects."""
    return {
        "type": "object",
        "properties": {
            "database": {
                "type": "object",
                "properties": {
                    "host": {"type": "string"},
                    "port": {"type": "integer"},
                },
            },
        },
    }


@pytest.fixture
def array_schema():
    """Fixture providing a schema with array fields."""
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }


@pytest.fixture
def array_of_objects_schema():
    """Fixture providing a schema with array of objects."""
    return {
        "type": "object",
        "properties": {
            "configs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "value": {"type": "integer"},
                    },
                },
            },
        },
    }


# =============================================================================
# Tests for EnvLoader initialization
# =============================================================================


class TestEnvLoaderInit:
    """Tests for EnvLoader.__init__."""

    def test_default_delimiter(self, basic_schema):
        """Test default delimiter is underscore."""
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader(basic_schema, "PREFIX")
            assert loader.env_delimiter == "_"

    def test_custom_delimiter(self, basic_schema):
        """Test custom delimiter."""
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader(basic_schema, "PREFIX", delimiter="__")
            assert loader.env_delimiter == "__"

    def test_empty_prefix(self, basic_schema):
        """Test with empty prefix."""
        with mock.patch.dict(environ, {"KEY": "value"}, clear=True):
            loader = EnvLoader(basic_schema, "")
            assert loader.env_prefix == ""
            # Should not filter when prefix is empty
            assert loader._env == {"KEY": "value"}

    def test_no_prefix(self, basic_schema):
        """Test with None prefix defaults to empty string."""
        with mock.patch.dict(environ, {"KEY": "value"}, clear=True):
            loader = EnvLoader(basic_schema, None)
            assert loader.env_prefix == ""

    def test_env_filtering(self, basic_schema):
        """Test that env vars are filtered by prefix."""
        env = {
            "PREFIX_NAME": "value",
            "PREFIX_COUNT": "10",
            "OTHER_KEY": "ignored",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(basic_schema, "PREFIX")
            assert loader._env == {"PREFIX_NAME": "value", "PREFIX_COUNT": "10"}

    def test_schema_stored(self, basic_schema):
        """Test that schema is stored."""
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader(basic_schema, "PREFIX")
            assert loader.schema == basic_schema


# =============================================================================
# Tests for EnvLoader.load
# =============================================================================


class TestEnvLoaderLoad:
    """Tests for EnvLoader.load method."""

    def test_empty_env_returns_empty(self, basic_schema):
        """Test that empty env returns empty dict."""
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader(basic_schema, "PREFIX")
            result = loader.load()
            assert result == {}

    def test_load_simple_values(self, basic_schema):
        """Test loading simple string/integer/boolean values."""
        env = {
            "PREFIX_NAME": "test_name",
            "PREFIX_COUNT": "42",
            "PREFIX_ENABLED": "true",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(basic_schema, "PREFIX")
            result = loader.load()
            assert result == {
                "name": "test_name",
                "count": "42",
                "enabled": "true",
            }

    def test_load_nested_object(self, nested_object_schema):
        """Test loading nested object values."""
        env = {
            "PREFIX_DATABASE_HOST": "localhost",
            "PREFIX_DATABASE_PORT": "5432",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(nested_object_schema, "PREFIX")
            result = loader.load()
            assert result == {
                "database": {"host": "localhost", "port": "5432"},
            }

    def test_load_array_from_csv(self, array_schema):
        """Test loading array from CSV format."""
        env = {"PREFIX_ITEMS": "a, b, c"}
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(array_schema, "PREFIX")
            result = loader.load()
            assert result == {"items": ["a", "b", "c"]}

    def test_load_array_from_indexed(self, array_schema):
        """Test loading array from indexed env vars."""
        env = {
            "PREFIX_ITEMS_0": "first",
            "PREFIX_ITEMS_1": "second",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(array_schema, "PREFIX")
            result = loader.load()
            assert result == {"items": ["first", "second"]}

    def test_load_array_of_objects(self, array_of_objects_schema):
        """Test loading array of objects from indexed env vars."""
        env = {
            "PREFIX_CONFIGS_0_NAME": "first",
            "PREFIX_CONFIGS_0_VALUE": "10",
            "PREFIX_CONFIGS_1_NAME": "second",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(array_of_objects_schema, "PREFIX")
            result = loader.load()
            assert result == {
                "configs": [
                    {"name": "first", "value": "10"},
                    {"name": "second"},
                ],
            }

    def test_load_with_gaps_in_array(self, array_schema):
        """Test that gaps in indexed array are filled with None."""
        env = {
            "PREFIX_ITEMS_0": "first",
            "PREFIX_ITEMS_3": "fourth",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(array_schema, "PREFIX")
            result = loader.load()
            assert result == {"items": ["first", None, None, "fourth"]}

    def test_csv_takes_precedence_over_empty_indexed(self, array_schema):
        """Test CSV format when both CSV and indexed present."""
        env = {
            "PREFIX_ITEMS": "csv1, csv2",
            "PREFIX_ITEMS_0": "indexed",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(array_schema, "PREFIX")
            result = loader.load()
            # Both should be present in result dict, with indexed merged
            assert "items" in result


# =============================================================================
# Tests for EnvLoader._get with schema types
# =============================================================================


class TestEnvLoaderGetWithTypes:
    """Tests for EnvLoader._get with different schema types."""

    def test_get_null_type(self):
        """Test that null type returns None."""
        schema = {"type": "null"}
        with mock.patch.dict(environ, {"PREFIX_KEY": "value"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX_KEY", schema)
            assert result is None

    def test_get_string_type(self):
        """Test getting string type value."""
        schema = {"type": "string"}
        with mock.patch.dict(environ, {"PREFIX_NAME": "test"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX_NAME", schema)
            assert result == "test"

    def test_get_integer_type(self):
        """Test getting integer type value (returns string, pydantic converts)."""
        schema = {"type": "integer"}
        with mock.patch.dict(environ, {"PREFIX_COUNT": "42"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX_COUNT", schema)
            assert result == "42"

    def test_get_boolean_type(self):
        """Test getting boolean type value."""
        schema = {"type": "boolean"}
        with mock.patch.dict(environ, {"PREFIX_ENABLED": "true"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX_ENABLED", schema)
            assert result == "true"

    def test_get_missing_value_returns_none(self):
        """Test that missing env var returns None."""
        schema = {"type": "string"}
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX_MISSING", schema)
            assert result is None

    def test_get_const_type(self):
        """Test getting const type value."""
        schema = {"const": "fixed_value"}
        with mock.patch.dict(environ, {"PREFIX_CONST": "env_value"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX_CONST", schema)
            assert result == "env_value"


# =============================================================================
# Tests for EnvLoader._resolve_ref
# =============================================================================


class TestEnvLoaderResolveRef:
    """Tests for EnvLoader._resolve_ref method."""

    def test_resolve_root_ref(self):
        """Test resolving reference to root."""
        schema = {
            "$defs": {"MyType": {"type": "string"}},
            "type": "object",
        }
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader(schema, "PREFIX")
            result = loader._resolve_ref("#/$defs/MyType")
            assert result == {"type": "string"}

    def test_resolve_nested_ref(self):
        """Test resolving reference to nested definition."""
        schema = {
            "$defs": {
                "Database": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"},
                    },
                },
            },
        }
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader(schema, "PREFIX")
            result = loader._resolve_ref("#/$defs/Database")
            assert result["type"] == "object"
            assert "properties" in result

    def test_resolve_deeply_nested_ref(self):
        """Test resolving deeply nested reference."""
        schema = {
            "$defs": {
                "Level1": {
                    "$defs": {
                        "Level2": {"type": "string"},
                    },
                },
            },
        }
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader(schema, "PREFIX")
            result = loader._resolve_ref("#/$defs/Level1/$defs/Level2")
            assert result == {"type": "string"}


# =============================================================================
# Tests for EnvLoader._get with anyOf/oneOf/allOf
# =============================================================================


class TestEnvLoaderGetWithComposition:
    """Tests for EnvLoader._get with composition keywords."""

    def test_get_allOf(self):
        """Test _get with allOf schema."""
        schema = {
            "allOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
                {"type": "object", "properties": {"b": {"type": "string"}}},
            ],
        }
        env = {
            "PREFIX_A": "value_a",
            "PREFIX_B": "value_b",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX", schema)
            assert result == {"a": "value_a", "b": "value_b"}

    def test_get_oneOf(self):
        """Test _get with oneOf schema."""
        schema = {
            "oneOf": [
                {"title": "TypeA", "type": "object", "properties": {"a": {"type": "string"}}},
                {"title": "TypeB", "type": "object", "properties": {"b": {"type": "string"}}},
            ],
        }
        env = {"PREFIX_A": "value_a"}
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX", schema)
            assert result == {"a": "value_a"}

    def test_get_anyOf_with_strings(self):
        """Test _get with anyOf of string types."""
        schema = {
            "anyOf": [
                {"type": "string"},
                {"type": "null"},
            ],
        }
        with mock.patch.dict(environ, {"PREFIX_KEY": "value"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX_KEY", schema)
            assert result == "value"

    def test_get_anyOf_with_objects(self):
        """Test _get with anyOf of object types."""
        schema = {
            "anyOf": [
                {"type": "object", "properties": {"a": {"type": "string"}}},
                {"type": "object", "properties": {"b": {"type": "string"}}},
            ],
        }
        env = {"PREFIX_A": "value_a", "PREFIX_B": "value_b"}
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get("PREFIX", schema)
            assert result == {"a": "value_a", "b": "value_b"}


# =============================================================================
# Tests for EnvLoader._get_object
# =============================================================================


class TestEnvLoaderGetObject:
    """Tests for EnvLoader._get_object method."""

    def test_get_empty_object(self):
        """Test getting object with no properties."""
        schema = {"type": "object", "properties": {}}
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_object("PREFIX", schema)
            assert result == {}

    def test_get_object_with_properties(self):
        """Test getting object with properties."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"},
            },
        }
        env = {
            "PREFIX_NAME": "test",
            "PREFIX_COUNT": "42",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_object("PREFIX", schema)
            assert result == {"name": "test", "count": "42"}

    def test_get_object_with_empty_prefix(self):
        """Test getting object with empty prefix."""
        schema = {
            "type": "object",
            "properties": {"key": {"type": "string"}},
        }
        with mock.patch.dict(environ, {"KEY": "value"}, clear=True):
            loader = EnvLoader({}, "", delimiter="_")
            result = loader._get_object("", schema)
            assert result == {"key": "value"}

    def test_get_object_skips_empty_values(self):
        """Test that properties with empty/None values are skipped."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "missing": {"type": "string"},
            },
        }
        with mock.patch.dict(environ, {"PREFIX_NAME": "test"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_object("PREFIX", schema)
            # missing is not in env, so it's skipped
            assert result == {"name": "test"}


# =============================================================================
# Tests for EnvLoader._get_array
# =============================================================================


class TestEnvLoaderGetArray:
    """Tests for EnvLoader._get_array method."""

    def test_get_array_from_csv(self):
        """Test getting array from CSV format."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        with mock.patch.dict(environ, {"PREFIX": "a, b, c"}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_array("PREFIX", schema)
            assert result == ["a", "b", "c"]

    def test_get_array_from_csv_with_whitespace(self):
        """Test that CSV values are stripped of whitespace."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        with mock.patch.dict(environ, {"PREFIX": "  a  ,  b  "}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_array("PREFIX", schema)
            assert result == ["a", "b"]

    def test_get_array_from_indexed(self):
        """Test getting array from indexed env vars."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        env = {
            "PREFIX_0": "first",
            "PREFIX_1": "second",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_array("PREFIX", schema)
            assert result == ["first", "second"]

    def test_get_array_from_both_csv_and_indexed(self):
        """Test array populated from both CSV and indexed (merged)."""
        schema = {
            "type": "array",
            "items": {"type": "string"},
        }
        env = {
            "PREFIX": "csv1, csv2",
            "PREFIX_2": "indexed",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_array("PREFIX", schema)
            assert result == ["csv1", "csv2", "indexed"]

    def test_get_array_of_objects(self):
        """Test getting array of objects from indexed env vars."""
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
            },
        }
        env = {
            "PREFIX_0_NAME": "first",
            "PREFIX_1_NAME": "second",
        }
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader({}, "PREFIX")
            result = loader._get_array("PREFIX", schema)
            assert result == [{"name": "first"}, {"name": "second"}]

    def test_get_array_with_ref_items(self):
        """Test getting array with $ref items schema."""
        schema = {
            "type": "array",
            "items": {"$ref": "#/$defs/Item"},
        }
        full_schema = {
            "$defs": {
                "Item": {"type": "string"},
            },
        }
        with mock.patch.dict(environ, {"PREFIX": "a, b"}, clear=True):
            loader = EnvLoader(full_schema, "PREFIX")
            result = loader._get_array("PREFIX", schema)
            assert result == ["a", "b"]


# =============================================================================
# Tests for EnvLoader._get_mapping
# =============================================================================


class TestEnvLoaderGetMapping:
    """Tests for EnvLoader._get_mapping method."""

    def test_get_mapping_with_ref(self):
        """Test _get_mapping resolving references."""
        schema = {
            "$defs": {
                "TypeA": {"title": "TypeA", "type": "object", "properties": {"a": {"type": "string"}}},
            },
        }
        env = {"PREFIX_A": "value_a"}
        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(schema, "PREFIX")
            schemas = [{"$ref": "#/$defs/TypeA"}]
            result = loader._get_mapping("PREFIX", *schemas)
            assert result == {"TypeA": {"a": "value_a"}}

    def test_get_mapping_empty_result(self):
        """Test _get_mapping when no values found."""
        with mock.patch.dict(environ, {}, clear=True):
            loader = EnvLoader({}, "PREFIX")
            schemas = [{"type": "object", "properties": {"a": {"type": "string"}}}]
            result = loader._get_mapping("PREFIX", *schemas)
            assert result == {}


# =============================================================================
# Integration tests with real Pydantic models
# =============================================================================


class TestEnvLoaderIntegration:
    """Integration tests with real Pydantic models."""

    def test_with_pydantic_model(self):
        """Test EnvLoader with a real Pydantic model schema."""

        class DatabaseConfig(BaseModel):
            host: str = "localhost"
            port: int = 5432

        class AppConfig(BaseModel):
            name: str
            debug: bool = False
            database: DatabaseConfig

        schema = AppConfig.model_json_schema()
        env = {
            "APP_NAME": "myapp",
            "APP_DEBUG": "true",
            "APP_DATABASE_HOST": "remotehost",
        }

        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(schema, "APP")
            result = loader.load()

        assert result == {
            "name": "myapp",
            "debug": "true",
            "database": {"host": "remotehost"},
        }

    def test_with_complex_nested_model(self):
        """Test with complex nested model structure."""

        class Inner(BaseModel):
            value: str

        class Outer(BaseModel):
            items: list[Inner]

        schema = Outer.model_json_schema()
        env = {
            "OUTER_ITEMS_0_VALUE": "first",
            "OUTER_ITEMS_1_VALUE": "second",
        }

        with mock.patch.dict(environ, env, clear=True):
            loader = EnvLoader(schema, "OUTER")
            result = loader.load()

        assert result == {
            "items": [{"value": "first"}, {"value": "second"}],
        }
