"""
JSON serialization utilities for the parser system.

This module provides functionality to serialize parser data structures to JSON,
handling circular references and complex objects.

# AI-Intent: Core-Domain
# Intent: These serialization utilities represent core domain services
# They handle conversion of domain entities to serializable format
# Confidence: High
"""

import dataclasses
import enum
import inspect
import json
import typing
from datetime import date, datetime
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

# Type for custom serializers
T = TypeVar("T")
SerializerFunc = Callable[[T], Any]


class CircularReferenceDetector:
    """
    Utility class to detect and handle circular references during serialization.
    """

    def __init__(self):
        """Initialize the circular reference detector."""
        self._seen_objects: Dict[int, str] = {}
        self._reference_map: Dict[str, Any] = {}
        self._current_path: List[str] = []

    def enter_object(self, obj: Any, name: str = "") -> Tuple[bool, Optional[str]]:
        """
        Check if an object has been seen before, indicating a circular reference.

        Args:
            obj: The object to check.
            name: The name of the object in the current context.

        Returns:
            A tuple (is_circular, ref_id) where:
            - is_circular: True if this is a circular reference.
            - ref_id: The reference ID for this object if it's a circular reference.
        """
        # Only track objects with stable identity (not primitives)
        if not self._is_trackable(obj):
            return False, None

        obj_id = id(obj)

        # If we've seen this object before, it's a circular reference
        if obj_id in self._seen_objects:
            return True, self._seen_objects[obj_id]

        # Generate a reference path
        path_name = name if name else f"obj_{obj_id}"
        if self._current_path:
            ref_id = f"{'.'.join(self._current_path)}.{path_name}"
        else:
            ref_id = path_name

        # Record this object
        self._seen_objects[obj_id] = ref_id
        self._reference_map[ref_id] = obj

        # Update the current path
        self._current_path.append(path_name)

        return False, ref_id

    def exit_object(self):
        """Exit the current object context."""
        if self._current_path:
            self._current_path.pop()

    def get_reference(self, ref_id: str) -> Any:
        """Get the object associated with a reference ID."""
        return self._reference_map.get(ref_id)

    @staticmethod
    def _is_trackable(obj: Any) -> bool:
        """Check if an object is trackable for circular references."""
        return (
            obj is not None
            and not isinstance(obj, (bool, int, float, str, bytes, datetime, date))
            and not isinstance(obj, (type, enum.Enum))
        )


class ParserJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for parser data structures.

    This encoder handles:
    1. Dataclasses
    2. Enums
    3. Circular references
    4. Path objects
    5. Custom registered types
    """

    def __init__(self, *args, **kwargs):
        """Initialize the encoder."""
        self._circular_detector = CircularReferenceDetector()
        self._custom_serializers: Dict[Type, SerializerFunc] = {
            Path: lambda p: str(p),
            datetime: lambda dt: dt.isoformat(),
            date: lambda d: d.isoformat(),
        }
        super().__init__(*args, **kwargs)

    def default(self, obj: Any) -> Any:
        """
        Convert a custom object to a serializable type.

        Args:
            obj: The object to serialize.

        Returns:
            A JSON-serializable representation of the object.

        Raises:
            TypeError: If the object cannot be serialized.
        """
        # Check for circular references
        is_circular, ref_id = self._circular_detector.enter_object(obj)
        try:
            if is_circular:
                return {"$ref": ref_id}

            # Handle dataclasses
            if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
                if hasattr(obj, "to_dict") and callable(obj.to_dict):
                    # Use the object's custom to_dict method
                    return obj.to_dict()
                return self._handle_dataclass(obj)

            # Handle enums
            if isinstance(obj, enum.Enum):
                return obj.value

            # Check for custom serializers
            for obj_type, serializer in self._custom_serializers.items():
                if isinstance(obj, obj_type):
                    return serializer(obj)

            # Handle types that json can't serialize natively
            if inspect.isfunction(obj) or inspect.ismethod(obj):
                return f"{obj.__module__}.{obj.__qualname__}"

            if inspect.isclass(obj):
                return f"{obj.__module__}.{obj.__qualname__}"

            if hasattr(obj, "__dict__"):
                return self._handle_object_with_dict(obj)

            # Let the parent class handle it or raise TypeError
            return super().default(obj)
        finally:
            self._circular_detector.exit_object()

    def _handle_dataclass(self, obj: Any) -> Dict[str, Any]:
        """Handle serialization of a dataclass."""
        result = {}
        for field in dataclasses.fields(obj):
            field_name = field.name
            field_value = getattr(obj, field_name)

            # Skip fields that start with underscore
            if field_name.startswith("_"):
                continue

            result[field_name] = field_value
        return result

    def _handle_object_with_dict(self, obj: Any) -> Dict[str, Any]:
        """Handle serialization of an object with __dict__."""
        # Use __dict__ but filter out private attributes
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}

    def register_serializer(
        self, obj_type: Type[T], serializer: SerializerFunc[T]
    ) -> None:
        """Register a custom serializer for a type."""
        self._custom_serializers[obj_type] = serializer


class ParsedDataSerializer:
    """
    Serializer for parsed data structures.

    This class provides utility methods to serialize and deserialize
    parser data structures, with support for custom serializers and schemas.
    """

    def __init__(self):
        """Initialize the serializer."""
        self._encoder = ParserJSONEncoder(indent=2)
        self._seen_objects: Set[int] = set()

    def register_serializer(
        self, obj_type: Type[T], serializer: SerializerFunc[T]
    ) -> None:
        """Register a custom serializer for a type."""
        self._encoder.register_serializer(obj_type, serializer)

    def serialize(self, obj: Any) -> str:
        """
        Serialize an object to JSON.

        Args:
            obj: The object to serialize.

        Returns:
            A JSON string representation of the object.

        Raises:
            SerializationException: If the object cannot be serialized.
        """
        try:
            self._seen_objects.clear()
            return json.dumps(obj, cls=type(self._encoder))
        except Exception as e:
            from .errors import ParserErrorCode, SerializationException

            raise SerializationException(
                message=f"Failed to serialize object: {str(e)}",
                code=ParserErrorCode.SERIALIZATION_ERROR,
                context={"object_type": type(obj).__name__},
            ) from e

    def serialize_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Serialize an object to a dictionary.

        Args:
            obj: The object to serialize.

        Returns:
            A dictionary representation of the object.

        Raises:
            SerializationException: If the object cannot be serialized.
        """
        try:
            self._seen_objects.clear()
            return json.loads(self.serialize(obj))
        except Exception as e:
            from .errors import ParserErrorCode, SerializationException

            raise SerializationException(
                message=f"Failed to serialize object to dict: {str(e)}",
                code=ParserErrorCode.SERIALIZATION_ERROR,
                context={"object_type": type(obj).__name__},
            ) from e

    def deserialize(self, json_str: str, obj_type: Optional[Type[T]] = None) -> Any:
        """
        Deserialize a JSON string to an object.

        Args:
            json_str: The JSON string to deserialize.
            obj_type: Optional type to deserialize to.

        Returns:
            The deserialized object.

        Raises:
            SerializationException: If the JSON string cannot be deserialized.
        """
        try:
            data = json.loads(json_str)
            if obj_type is not None:
                return self._convert_to_type(data, obj_type)
            return data
        except Exception as e:
            from .errors import ParserErrorCode, SerializationException

            raise SerializationException(
                message=f"Failed to deserialize JSON: {str(e)}",
                code=ParserErrorCode.SERIALIZATION_ERROR,
            ) from e

    def _convert_to_type(self, data: Any, obj_type: Type[T]) -> T:
        """Convert a deserialized object to the specified type."""
        if dataclasses.is_dataclass(obj_type):
            # For dataclasses, create a new instance with fields from data
            field_values = {}
            for field in dataclasses.fields(obj_type):
                if field.name in data:
                    field_values[field.name] = data[field.name]
            return obj_type(**field_values)

        # For basic types, just return the data
        return obj_type(data)


# Global serializer instance
_serializer = ParsedDataSerializer()


def serialize(obj: Any) -> str:
    """
    Serialize an object to JSON.

    Args:
        obj: The object to serialize.

    Returns:
        A JSON string representation of the object.
    """
    return _serializer.serialize(obj)


def serialize_to_dict(obj: Any) -> Dict[str, Any]:
    """
    Serialize an object to a dictionary.

    Args:
        obj: The object to serialize.

    Returns:
        A dictionary representation of the object.
    """
    return _serializer.serialize_to_dict(obj)


def deserialize(json_str: str, obj_type: Optional[Type[T]] = None) -> Any:
    """
    Deserialize a JSON string to an object.

    Args:
        json_str: The JSON string to deserialize.
        obj_type: Optional type to deserialize to.

    Returns:
        The deserialized object.
    """
    return _serializer.deserialize(json_str, obj_type)


def register_serializer(obj_type: Type[T], serializer: SerializerFunc[T]) -> None:
    """
    Register a custom serializer for a type.

    Args:
        obj_type: The type to register a serializer for.
        serializer: The serializer function.
    """
    _serializer.register_serializer(obj_type, serializer)
