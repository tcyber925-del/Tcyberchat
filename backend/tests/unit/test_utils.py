"""
Unit tests for utility functions and helpers
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

def test_path_operations():
    """Test basic path operations and file handling"""
    # Test path creation
    test_dir = Path("test_dir")
    assert not test_dir.exists()

    # Test path joining (handle both Unix and Windows separators)
    full_path = test_dir / "subfolder" / "file.txt"
    expected_path = str(full_path).replace("\\", "/")  # Normalize for cross-platform
    assert expected_path == "test_dir/subfolder/file.txt"

def test_environment_variables():
    """Test environment variable handling"""
    # Test default values
    test_var = os.getenv("NON_EXISTENT_VAR", "default_value")
    assert test_var == "default_value"

    # Test existing variables
    python_path = os.getenv("PATH")
    assert python_path is not None
    assert len(python_path) > 0

def test_file_operations():
    """Test basic file operations"""
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        temp_path = f.name
        f.write("test content")

    try:
        # Test file exists
        assert os.path.exists(temp_path)

        # Test file reading
        with open(temp_path, 'r') as f:
            content = f.read()
            assert content == "test content"

    finally:
        # Cleanup
        os.unlink(temp_path)

def test_json_operations():
    """Test JSON parsing and validation"""
    import json

    # Test valid JSON
    test_data = {"key": "value", "number": 42}
    json_str = json.dumps(test_data)
    parsed = json.loads(json_str)
    assert parsed == test_data

    # Test JSON with nested structures
    nested_data = {
        "users": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ],
        "active": True
    }
    json_str = json.dumps(nested_data)
    parsed = json.loads(json_str)
    assert parsed["users"][0]["name"] == "Alice"
    assert parsed["active"] is True

def test_string_operations():
    """Test string manipulation utilities"""
    # Test string splitting
    text = "This is a test sentence."
    words = text.split()
    assert len(words) == 5
    assert words[0] == "This"

    # Test string formatting
    template = "Hello, {}!"
    result = template.format("World")
    assert result == "Hello, World!"

    # Test substring operations
    text = "The quick brown fox"
    assert text.startswith("The")
    assert text.endswith("fox")
    assert "brown" in text

def test_list_operations():
    """Test list manipulation and filtering"""
    # Test list comprehension
    numbers = [1, 2, 3, 4, 5]
    squares = [x**2 for x in numbers]
    assert squares == [1, 4, 9, 16, 25]

    # Test filtering
    even_numbers = [x for x in numbers if x % 2 == 0]
    assert even_numbers == [2, 4]

    # Test list methods
    test_list = [3, 1, 4, 1, 5]
    test_list.sort()
    assert test_list == [1, 1, 3, 4, 5]

    test_list.append(2)
    assert len(test_list) == 6

def test_dict_operations():
    """Test dictionary operations and manipulation"""
    # Test dictionary creation and access
    person = {"name": "Alice", "age": 30, "city": "New York"}
    assert person["name"] == "Alice"
    assert person.get("age") == 30
    assert person.get("country", "USA") == "USA"

    # Test dictionary methods
    keys = list(person.keys())
    values = list(person.values())
    assert "name" in keys
    assert 30 in values

    # Test dictionary comprehension
    squared_dict = {x: x**2 for x in range(1, 4)}
    assert squared_dict == {1: 1, 2: 4, 3: 9}

def test_exception_handling():
    """Test exception handling patterns"""
    # Test try-except blocks
    try:
        result = 10 / 2
        assert result == 5.0
    except ZeroDivisionError:
        assert False, "Should not raise ZeroDivisionError"

    # Test exception raising
    try:
        result = 10 / 0
        assert False, "Should have raised ZeroDivisionError"
    except ZeroDivisionError:
        pass  # Expected

def test_type_checking():
    """Test basic type checking and validation"""
    # Test isinstance
    assert isinstance("hello", str)
    assert isinstance(42, int)
    assert isinstance([1, 2, 3], list)
    assert isinstance({"key": "value"}, dict)

    # Test type conversion
    assert int("42") == 42
    assert str(42) == "42"
    assert float("3.14") == 3.14
    assert bool(1) is True
    assert bool(0) is False

if __name__ == "__main__":
    # Run all tests
    test_path_operations()
    test_environment_variables()
    test_file_operations()
    test_json_operations()
    test_string_operations()
    test_list_operations()
    test_dict_operations()
    test_exception_handling()
    test_type_checking()

    print("All utility tests passed!")