from types import NoneType
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from typing_extensions import NotRequired, is_typeddict
from typing_extensions import get_origin as ext_get_origin


def check_typed_dict(value: dict[str, Any], typed_dict_cls: type) -> None:
    """
    Validates that a dictionary matches a TypedDict structure.

    Args:
        value: The dictionary to validate
        typed_dict_cls: The TypedDict class to validate against

    Raises:
        TypeError: If the value doesn't match the TypedDict structure
        KeyError: If a required key is missing
    """
    # Check if value is a dict
    if not isinstance(value, dict):
        raise TypeError(f"Expected dict, got {type(value).__name__}")

    # Get type hints and check if it's a total TypedDict
    annotations = get_type_hints(typed_dict_cls)
    is_total = getattr(typed_dict_cls, "__total__", True)

    # Get NotRequired keys
    not_required_keys = set()
    for key, type_hint in annotations.items():
        origin = ext_get_origin(type_hint)
        if origin is NotRequired:
            not_required_keys.add(key)
            # Update the annotation with the inner type
            annotations[key] = get_args(type_hint)[0]

    # Check for required keys
    for key in annotations:
        if key not in value:
            # Skip if the key is marked as NotRequired or if the TypedDict is not total
            if key in not_required_keys or not is_total:
                continue
            raise KeyError(f"Missing required key: {key}")

    # Check types for all provided keys
    for key, val in value.items():
        if key not in annotations:
            # Extra keys are not allowed in TypedDict
            raise KeyError(f"Unexpected key: {key}")

        expected_type = annotations[key]
        validate_type(val, expected_type, key_path=key)


def validate_type(value: Any, expected_type: type, key_path: str = "") -> None:
    """
    Validates that a value matches an expected type, handling complex types like Union, List, etc.

    Args:
        value: The value to validate
        expected_type: The type to validate against
        key_path: String representation of the current key path for error messages

    Raises:
        TypeError: If the value doesn't match the expected type
    """
    # Handle None value with Optional type
    if value is None:
        # Check if None is allowed (Union with NoneType)
        origin = get_origin(expected_type)
        if origin is Union and NoneType in get_args(expected_type):
            return
        raise TypeError(f"{key_path}: None is not valid for type {expected_type}")

    origin = get_origin(expected_type)
    type_args = get_args(expected_type)

    # Handle Literal types
    if origin is Literal:
        if value not in type_args:
            allowed_values = ", ".join(repr(arg) for arg in type_args)
            raise TypeError(
                f"{key_path}: Expected one of {allowed_values}, got {repr(value)}"
            )
        return

    # Handle Union types (including Optional)
    if origin is Union:
        errors = []
        for arg_type in type_args:
            try:
                validate_type(value, arg_type, key_path)
                return  # If any type validation succeeds, return
            except (TypeError, KeyError) as e:
                errors.append(str(e))
        raise TypeError(
            f"{key_path}: Value does not match any type in {expected_type}. Errors: {', '.join(errors)}"
        )

    # Handle TypedDict
    if is_typeddict(expected_type):
        if not isinstance(value, dict):
            raise TypeError(
                f"{key_path}: Expected dict for TypedDict, got {type(value).__name__}"
            )
        check_typed_dict(value, expected_type)
        return

    # Handle List type
    if origin is list:
        if not isinstance(value, list):
            raise TypeError(f"{key_path}: Expected list, got {type(value).__name__}")
        if type_args:
            element_type = type_args[0]
            for i, item in enumerate(value):
                validate_type(item, element_type, f"{key_path}[{i}]")
        return

    # Handle Dict type
    if origin is dict:
        if not isinstance(value, dict):
            raise TypeError(f"{key_path}: Expected dict, got {type(value).__name__}")
        if len(type_args) == 2:
            key_type, val_type = type_args
            for k, v in value.items():
                validate_type(k, key_type, f"key of {key_path}")
                validate_type(v, val_type, f"{key_path}[{k}]")
        return

    # Handle basic types - try using isinstance for concrete types
    if origin is None:  # Not a generic type
        if hasattr(expected_type, "__origin__"):  # Handle typing types
            raise TypeError(
                f"{key_path}: Cannot validate advanced typing construct {expected_type} at runtime"
            )

        # For basic types, use isinstance
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{key_path}: Expected {expected_type.__name__}, got {type(value).__name__}"
            )
        return

    # For other container types, check if it matches the origin
    if not isinstance(value, origin):
        raise TypeError(
            f"{key_path}: Expected {origin.__name__}, got {type(value).__name__}"
        )
