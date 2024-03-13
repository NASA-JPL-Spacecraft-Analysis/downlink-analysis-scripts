"""Interacting with Merlin data
"""

from typing import Dict
import json
import abc


class ValueSchema:
    """Merlin resource value schema"""

    # Track schema classes keyed by data type (registered by decorator)
    __schema_types = {}

    @classmethod
    def register(cls, schema_class: "ValueSchema"):
        """Register schema class for a data type
        """
        if issubclass(schema_class, cls):
            cls.__schema_types[schema_class.get_type_string()] = schema_class
        return schema_class

    @classmethod
    def parse_unknown_schema(cls, schema: Dict) -> "ValueSchema":
        """Instantiate from a schema Dict object of arbitrary type

        Finds the schema class for the schema data type. If none is registered, throw an error.

        TODO Consider implementing special handling here for initial/rate parameters into just the "initial" type
        """
        try:
            return cls.__schema_types[schema["type"]].from_schema(schema)
        except KeyError:
            if not isinstance(schema, dict) or ("type" not in schema.keys()):
                raise ValueError(f"Bad value schema: {json.dumps(schema)}")
            elif schema["type"] not in cls.__schema_types.keys():
                raise ValueError(
                    f"Unknown schema type: {schema['type']} on schema: {json.dumps(schema)}")
            else:
                raise

    @classmethod
    @abc.abstractmethod
    def from_schema(cls, schema: Dict) -> "ValueSchema":
        pass

    @staticmethod
    @abc.abstractmethod
    def get_type_string() -> str:
        """Return the JSON type string for this schema type"""
        pass

    @classmethod
    def unknown_to_schema(cls, schema: "ValueSchema") -> Dict:
        try:
            return cls.__schema_types[schema.get_type_string()].to_schema(schema)
        except KeyError:
            raise ValueError(
                f"Unknown schema type: {schema.get_type_string()}")

    def to_schema(self) -> Dict:
        return {"type": self.get_type_string()}


@ValueSchema.register
class SeriesSchema(ValueSchema):
    """Value schema SERIES type"""

    @staticmethod
    def get_type_string() -> str:
        return "series"

    def __init__(self, items: ValueSchema) -> None:
        self.items = items

    @classmethod
    def from_schema(cls, schema: Dict) -> "ValueSchema":
        return cls(ValueSchema.parse_unknown_schema(schema["items"]))

    def to_schema(self) -> Dict:
        return {
            "type": "series",
            "items": self.items.to_schema()
        }


@ValueSchema.register
class StructSchema(ValueSchema):
    """Value schema STRUCT type"""

    @staticmethod
    def get_type_string() -> str:
        return "struct"

    def __init__(self, items: Dict[str, ValueSchema]) -> None:
        self.items = items

    @classmethod
    def from_schema(cls, schema: Dict) -> "ValueSchema":
        items = {n: ValueSchema.parse_unknown_schema(
            i) for n, i in schema["items"].items()}
        return cls(items)

    def to_schema(self) -> Dict:
        return {
            "type": "struct",
            "items": {n: i.to_schema() for n, i in self.items.items()}
        }


@ValueSchema.register
class BooleanSchema(ValueSchema):
    """Value schema BOOLEAN type"""

    @staticmethod
    def get_type_string() -> str:
        return "boolean"

    @classmethod
    def from_schema(cls, _: Dict):
        return cls()


@ValueSchema.register
class DurationSchema(ValueSchema):
    """Value schema DURATION type"""

    @staticmethod
    def get_type_string() -> str:
        return "duration"

    @classmethod
    def from_schema(cls, _: Dict):
        return cls()


@ValueSchema.register
class IntSchema(ValueSchema):
    """Value schema INT type"""

    @staticmethod
    def get_type_string() -> str:
        return "int"

    @classmethod
    def from_schema(cls, _: Dict):
        return cls()


@ValueSchema.register
class PathSchema(ValueSchema):
    """Value schema PATH type"""

    @staticmethod
    def get_type_string() -> str:
        return "path"

    @classmethod
    def from_schema(cls, _: Dict):
        return cls()


@ValueSchema.register
class RealSchema(ValueSchema):
    """Value schema REAL type"""

    @staticmethod
    def get_type_string() -> str:
        return "real"

    @classmethod
    def from_schema(cls, _: Dict):
        return cls()


@ValueSchema.register
class StringSchema(ValueSchema):
    """Value schema STRING type"""

    @staticmethod
    def get_type_string() -> str:
        return "string"

    @classmethod
    def from_schema(cls, _: Dict):
        return cls()


@ValueSchema.register
class VariantSchema(ValueSchema):
    """Value schema VARIANT type"""

    @staticmethod
    def get_type_string() -> str:
        return "variant"

    def __init__(self, variants: Dict[str, str]) -> None:
        self.variants = variants

    @classmethod
    def from_schema(cls, schema: Dict) -> "ValueSchema":
        return cls(schema["variants"])

    def to_schema(self) -> Dict:
        return {
            "type": "variant",
            "variants": self.variants
        }
