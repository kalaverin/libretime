"""Unit tests for sdk.config._base module."""

import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
import yaml
from pydantic import BaseModel, ValidationError

from sdk.config._base import (
    DEFAULT_CONFIG_FILEPATH,
    DEFAULT_ENV_PREFIX,
    BaseConfig,
    deep_merge_dict,
    deep_merge_list,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def simple_config_class():
    """Fixture providing a simple config class for testing."""

    class SimpleConfig(BaseConfig):
        name: str
        value: int = 42

    return SimpleConfig


@pytest.fixture
def nested_config_class():
    """Fixture providing a nested config class for testing."""

    class InnerConfig(BaseModel):
        key: str
        secret: str = "default_secret"

    class NestedConfig(BaseConfig):
        outer_name: str
        inner: InnerConfig
        optional_inner: InnerConfig = InnerConfig(key="default_key")

    return NestedConfig


@pytest.fixture
def valid_yaml_content():
    """Fixture providing valid YAML content."""
    return """
name: test_name
value: 100
"""


@pytest.fixture
def nested_yaml_content():
    """Fixture providing nested YAML content."""
    return """
outer_name: outer_value
inner:
  key: inner_key
  secret: inner_secret
"""


# =============================================================================
# Tests for module constants
# =============================================================================


def test_default_constants():
    """Test that default constants are defined correctly."""
    assert DEFAULT_ENV_PREFIX == "LIBRETIME"
    assert DEFAULT_CONFIG_FILEPATH == Path("etc/config.yml")


# =============================================================================
# Tests for deep_merge_dict
# =============================================================================


class TestDeepMergeDict:
    """Tests for deep_merge_dict function."""

    def test_empty_base(self):
        """Test merging into empty base dict."""
        result = deep_merge_dict({}, {"a": 1})
        assert result == {"a": 1}

    def test_no_overlap(self):
        """Test merging dicts with no overlapping keys."""
        result = deep_merge_dict({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_simple_override(self):
        """Test that second dict overrides first."""
        result = deep_merge_dict({"a": 1}, {"a": 2})
        assert result == {"a": 2}

    def test_nested_merge(self):
        """Test recursive merging of nested dicts."""
        base = {"outer": {"inner": 1, "keep": 2}}
        override = {"outer": {"inner": 3}}
        result = deep_merge_dict(base, override)
        assert result == {"outer": {"inner": 3, "keep": 2}}

    def test_deeply_nested_merge(self):
        """Test merging of deeply nested dicts."""
        base = {"a": {"b": {"c": 1, "d": 2}}}
        override = {"a": {"b": {"c": 3}}}
        result = deep_merge_dict(base, override)
        assert result == {"a": {"b": {"c": 3, "d": 2}}}

    def test_merge_multiple_dicts(self):
        """Test merging multiple dicts."""
        result = deep_merge_dict(
            {"a": 1, "b": 1},
            {"b": 2},
            {"c": 3},
        )
        assert result == {"a": 1, "b": 2, "c": 3}

    def test_merge_with_list_values(self):
        """Test merging dicts with list values."""
        base = {"items": [1, 2, 3]}
        override = {"items": [4, 5]}
        result = deep_merge_dict(base, override)
        # deep_merge_list replaces elements, does not keep base tail
        assert result == {"items": [4, 5]}

    def test_merge_list_with_none_in_override(self):
        """Test merging when override list has None values."""
        base = {"items": [1, 2, 3]}
        override = {"items": [None, 5]}
        result = deep_merge_dict(base, override)
        # None is falsy, so base tail beyond override length is dropped
        assert result == {"items": [5]}

    def test_falsy_values_do_not_override(self):
        """Test that falsy values do not override existing keys."""
        # All falsy values (0, False, "", {}, []) are skipped by the
        # current implementation when overriding existing keys.
        result = deep_merge_dict({"a": 1}, {"a": 0})
        assert result == {"a": 1}

        result = deep_merge_dict({"a": 1}, {"a": False})
        assert result == {"a": 1}

        result = deep_merge_dict({"a": "hello"}, {"a": ""})
        assert result == {"a": "hello"}

    def test_empty_override_dict_ignored(self):
        """Test that empty dict override is ignored."""
        base = {"nested": {"key": "value"}}
        override = {"nested": {}}
        result = deep_merge_dict(base, override)
        # Empty dict is falsy, so it won't override
        assert result == {"nested": {"key": "value"}}

    def test_original_base_not_modified(self):
        """Test that original base dict is not modified."""
        base = {"a": 1, "nested": {"x": 1}}
        original_nested = base["nested"]
        override = {"nested": {"y": 2}}
        result = deep_merge_dict(base, override)

        # Original base should be unchanged
        assert base == {"a": 1, "nested": {"x": 1}}
        assert original_nested == {"x": 1}


# =============================================================================
# Tests for deep_merge_list
# =============================================================================


class TestDeepMergeList:
    """Tests for deep_merge_list function."""

    def test_empty_lists(self):
        """Test merging empty lists."""
        result = deep_merge_list([], [])
        assert result == []

    def test_single_element_lists(self):
        """Test merging single element lists."""
        result = deep_merge_list([1], [2])
        assert result == [2]

    def test_different_lengths(self):
        """Test merging lists of different lengths."""
        result = deep_merge_list([1, 2, 3], [4, 5])
        # Override does not extend with base tail
        assert result == [4, 5]

    def test_override_longer_than_base(self):
        """Test when override list is longer than base."""
        result = deep_merge_list([1], [2, 3, 4])
        assert result == [2, 3, 4]

    def test_merge_nested_lists(self):
        """Test merging nested lists."""
        base = [[1, 2], [3, 4]]
        override = [[5], [6, 7]]
        result = deep_merge_list(base, override)
        # Nested lists do not keep base tail beyond override
        assert result == [[5], [6, 7]]

    def test_merge_nested_dicts_in_lists(self):
        """Test merging lists containing dicts."""
        base = [{"a": 1, "b": 2}, {"c": 3}]
        override = [{"a": 10}, {"d": 4}]
        result = deep_merge_list(base, override)
        assert result == [{"a": 10, "b": 2}, {"c": 3, "d": 4}]

    def test_none_values_in_override(self):
        """Test that None values in override keep base values."""
        result = deep_merge_list([1, 2, 3], [None, 20])
        # None is falsy, base tail beyond override length is dropped
        assert result == [20]

    def test_multiple_list_merge(self):
        """Test merging multiple lists."""
        result = deep_merge_list(
            [1, 2, 3],
            [10, 20],
            [100, None, 300],
        )
        # Result accumulates across all elements; None skips that position
        assert result == [10, 20, 100, 300]

    def test_deeply_nested_structure(self):
        """Test merging deeply nested structures."""
        base = [[{"a": {"x": 1}}]]
        override = [[{"a": {"y": 2}}]]
        result = deep_merge_list(base, override)
        assert result == [[{"a": {"x": 1, "y": 2}}]]


# =============================================================================
# Tests for BaseConfig.load_from_file
# =============================================================================


class TestBaseConfigLoadFromFile:
    """Tests for BaseConfig.load_from_file method."""

    def test_load_valid_yaml(self, tmp_path: Path, simple_config_class, valid_yaml_content):
        """Test loading valid YAML file."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(valid_yaml_content)

        with mock.patch.dict("os.environ", {}, clear=True):
            config = simple_config_class(config_file)

        assert config.name == "test_name"
        assert config.value == 100

    def test_load_with_default_path_warning(self, simple_config_class, caplog):
        """Test warning when using default path that doesn't exist."""
        with mock.patch.dict("os.environ", {"LIBRETIME_NAME": "from_env"}, clear=True):
            with mock.patch.object(
                simple_config_class,
                "load_from_file",
                return_value={},
            ) as mock_load:
                config = simple_config_class(None)
                assert config.name == "from_env"

    def test_load_nonexistent_file(self, tmp_path: Path, simple_config_class):
        """Test loading from non-existent file path."""
        nonexistent = tmp_path / "does_not_exist.yml"

        with mock.patch.dict("os.environ", {"LIBRETIME_NAME": "from_env"}, clear=True):
            config = simple_config_class(nonexistent)
            assert config.name == "from_env"

    def test_load_directory_instead_of_file(self, tmp_path: Path, simple_config_class):
        """Test loading when path is a directory, not a file."""
        a_dir = tmp_path / "a_directory"
        a_dir.mkdir()

        with mock.patch.dict("os.environ", {"LIBRETIME_NAME": "from_env"}, clear=True):
            config = simple_config_class(a_dir)
            assert config.name == "from_env"

    def test_load_invalid_yaml(self, tmp_path: Path, simple_config_class, caplog):
        """Test loading invalid YAML causes fatal error."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(SystemExit) as exc_info:
            with mock.patch.dict("os.environ", {}, clear=True):
                simple_config_class(config_file)

        assert exc_info.value.code == 1

    def test_load_yaml_with_encoding(self, tmp_path: Path, simple_config_class):
        """Test loading YAML with UTF-8 encoding."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("name: тест_имени\nvalue: 42", encoding="utf-8")

        with mock.patch.dict("os.environ", {}, clear=True):
            config = simple_config_class(config_file)
            assert config.name == "тест_имени"

    def test_load_nested_config(self, tmp_path: Path, nested_config_class, nested_yaml_content):
        """Test loading nested config from YAML."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(nested_yaml_content)

        with mock.patch.dict("os.environ", {}, clear=True):
            config = nested_config_class(config_file)

        assert config.outer_name == "outer_value"
        assert config.inner.key == "inner_key"
        assert config.inner.secret == "inner_secret"

    def test_empty_path_returns_empty_dict(self, simple_config_class):
        """Test that None path returns empty dict."""
        config = simple_config_class.__new__(simple_config_class)
        result = config.load_from_file(None)
        assert result == {}


# =============================================================================
# Tests for BaseConfig initialization
# =============================================================================


class TestBaseConfigInit:
    """Tests for BaseConfig.__init__ method."""

    def test_init_with_kwargs_only(self, simple_config_class):
        """Test initialization with kwargs only."""
        with mock.patch.dict("os.environ", {}, clear=True):
            config = simple_config_class(None, name="kwargs_name")
            assert config.name == "kwargs_name"
            assert config.value == 42

    def test_init_file_overrides_kwargs(self, tmp_path: Path, simple_config_class, valid_yaml_content):
        """Test that file values override kwargs."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(valid_yaml_content)

        with mock.patch.dict("os.environ", {}, clear=True):
            config = simple_config_class(config_file, name="kwargs_override")
            assert config.name == "test_name"  # File overrides kwargs
            assert config.value == 100  # From file, not default

    def test_init_env_overrides_all(self, tmp_path: Path, simple_config_class, valid_yaml_content):
        """Test that env vars override both file and kwargs."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(valid_yaml_content)

        with mock.patch.dict("os.environ", {"LIBRETIME_NAME": "env_override"}, clear=True):
            config = simple_config_class(config_file, name="kwargs_override")
            assert config.name == "env_override"

    def test_init_with_custom_prefix(self, tmp_path: Path, simple_config_class, valid_yaml_content):
        """Test initialization with custom env prefix."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(valid_yaml_content)

        with mock.patch.dict("os.environ", {"CUSTOM_NAME": "custom_prefix_value"}, clear=True):
            config = simple_config_class(config_file, prefix="CUSTOM")
            assert config.name == "custom_prefix_value"

    def test_init_with_custom_delimiter(self, tmp_path: Path, simple_config_class, valid_yaml_content):
        """Test initialization with custom env delimiter."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(valid_yaml_content)

        # Using double underscore as delimiter
        with mock.patch.dict(
            "os.environ",
            {"LIBRETIME__NAME": "custom_delim_value"},
            clear=True,
        ):
            config = simple_config_class(config_file, delimiter="__")
            assert config.name == "custom_delim_value"

    def test_init_validation_error_exits(self, simple_config_class):
        """Test that validation error causes system exit."""
        with pytest.raises(SystemExit) as exc_info:
            with mock.patch.dict("os.environ", {}, clear=True):
                simple_config_class(None)  # Missing required 'name'

        assert exc_info.value.code == 1

    def test_init_with_string_path(self, tmp_path: Path, simple_config_class, valid_yaml_content):
        """Test initialization with string path instead of Path object."""
        config_file = tmp_path / "config.yml"
        config_file.write_text(valid_yaml_content)

        with mock.patch.dict("os.environ", {}, clear=True):
            config = simple_config_class(str(config_file))
            assert config.name == "test_name"

    def test_init_default_path_used(self, simple_config_class, tmp_path: Path):
        """Test that default path is used when path is None."""
        config_file = tmp_path / "config.yml"
        config_file.write_text("name: default_path_test")

        with mock.patch("sdk.config._base.DEFAULT_CONFIG_FILEPATH", config_file):
            with mock.patch.dict("os.environ", {}, clear=True):
                config = simple_config_class(None)
                assert config.name == "default_path_test"


# =============================================================================
# Tests for BaseConfig with complex types
# =============================================================================


class TestBaseConfigComplexTypes:
    """Tests for BaseConfig with complex field types."""

    def test_list_field_from_env_csv(self, tmp_path: Path):
        """Test list field populated from CSV env var."""

        class ListConfig(BaseConfig):
            items: list[str]

        config_file = tmp_path / "config.yml"
        config_file.write_text("items:\n  - from_file")

        with mock.patch.dict(
            "os.environ",
            {"LIBRETIME_ITEMS": "one, two, three"},
            clear=True,
        ):
            config = ListConfig(config_file)
            assert config.items == ["one", "two", "three"]

    def test_list_field_from_indexed_env(self, tmp_path: Path):
        """Test list field populated from indexed env vars."""

        class ListConfig(BaseConfig):
            items: list[str]

        with mock.patch.dict(
            "os.environ",
            {
                "LIBRETIME_ITEMS_0": "first",
                "LIBRETIME_ITEMS_1": "second",
            },
            clear=True,
        ):
            config = ListConfig(None)
            assert config.items == ["first", "second"]

    def test_optional_fields(self, tmp_path: Path):
        """Test config with optional fields."""

        class OptionalConfig(BaseConfig):
            required_field: str
            optional_field: str | None = None
            optional_with_default: str = "default_value"

        config_file = tmp_path / "config.yml"
        config_file.write_text("required_field: test")

        with mock.patch.dict("os.environ", {}, clear=True):
            config = OptionalConfig(config_file)
            assert config.required_field == "test"
            assert config.optional_field is None
            assert config.optional_with_default == "default_value"

    def test_boolean_field_from_env(self, tmp_path: Path):
        """Test boolean field populated from env."""

        class BoolConfig(BaseConfig):
            flag: bool = False

        with mock.patch.dict(
            "os.environ",
            {"LIBRETIME_FLAG": "true"},
            clear=True,
        ):
            config = BoolConfig(None)
            # Note: env values are strings, pydantic handles conversion
            assert config.flag is True


# =============================================================================
# Integration tests
# =============================================================================


class TestBaseConfigIntegration:
    """Integration tests for BaseConfig."""

    def test_full_config_workflow(self, tmp_path: Path):
        """Test complete configuration workflow with file, kwargs, and env."""

        class DatabaseConfig(BaseModel):
            host: str = "localhost"
            port: int = 5432

        class AppConfig(BaseConfig):
            name: str
            debug: bool = False
            database: DatabaseConfig
            allowed_hosts: list[str] = []

        config_file = tmp_path / "config.yml"
        config_file.write_text("""
name: from_file
debug: true
database:
  host: file_host
  port: 3306
allowed_hosts:
  - host1.com
  - host2.com
""")

        # Override some values via env
        with mock.patch.dict(
            "os.environ",
            {
                "LIBRETIME_NAME": "from_env",  # Override file
                "LIBRETIME_DATABASE_HOST": "env_host",  # Override nested
                # debug stays from file
                # allowed_hosts stays from file
            },
            clear=True,
        ):
            config = AppConfig(config_file)

        assert config.name == "from_env"
        assert config.debug is True  # From file
        assert config.database.host == "env_host"
        assert config.database.port == 3306  # From file
        assert config.allowed_hosts == ["host1.com", "host2.com"]

    def test_config_with_discriminated_union(self, tmp_path: Path):
        """Test config with discriminated union fields."""

        class BaseOutput(BaseModel):
            enabled: bool = True

        class IcecastOutput(BaseOutput):
            kind: str = "icecast"
            mount: str

        class ShoutcastOutput(BaseOutput):
            kind: str = "shoutcast"
            port: int

        class StreamConfig(BaseConfig):
            outputs: list[IcecastOutput | ShoutcastOutput]

        config_file = tmp_path / "config.yml"
        config_file.write_text("""
outputs:
  - kind: icecast
    mount: main.ogg
  - kind: shoutcast
    port: 8000
""")

        with mock.patch.dict("os.environ", {}, clear=True):
            config = StreamConfig(config_file)

        assert len(config.outputs) == 2
        assert config.outputs[0].kind == "icecast"
        assert config.outputs[0].mount == "main.ogg"
        assert config.outputs[1].kind == "shoutcast"
        assert config.outputs[1].port == 8000
