#!/usr/bin/env python3
"""
Generate Pydantic models and TypeScript interfaces from database_tables.yaml.
This version splits output files by API using the api_name field.

This script reads the database schema definitions from the YAML file and
generates corresponding Pydantic models for Python and TypeScript interfaces,
splitting them into separate files per API for better organization.

Updated for Pydantic 2.4 compatibility.
"""

import argparse
import sys
import yaml
import datetime
import re
import subprocess
from pathlib import Path
from collections import defaultdict

# Type mapping from YAML to Python/TypeScript
PYTHON_TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "array": "List",
    "object": "Dict",
}

TS_TYPE_MAP = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "array": "Array",
    "object": "Record<string, any>",
}

# Format mapping for Python
PYTHON_FORMAT_MAP = {
    "date": "date",
    "date-time": "datetime",
}

# CosmosBaseModel template - this will be in its own file
COSMOSDB_BASE_MODEL = '''# Generated from database_tables.yaml
# Base model for all database models with Cosmos DB compatibility

from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator
from datetime import date, datetime

# Module-level cache for storing the inverse field mappings
_PYTHON_TO_COSMOS_MAPS: dict[str, dict[str, str]] = {}

class CosmosBaseModel(BaseModel):
    """Base model for all schema models with Cosmos DB compatibility features.

    This model provides the following features for Cosmos DB compatibility:

    1. Field name mapping: Maps between camelCase field names (used in Cosmos DB)
       and snake_case property names (used in Python). This mapping is defined in
       the model_config.json_schema_extra dictionary with one primary mapping:
       - cosmos_to_python_map: Maps from Cosmos DB field names to Python property names

       The inverse mapping (python_to_cosmos_map) is automatically generated when needed
       and cached for efficiency.

    2. System field filtering: Automatically filters out Cosmos DB system fields
       (starting with '_') when creating models from Cosmos DB data.

    3. Serialization to Cosmos DB format: Provides a model_dump_cosmos() method
       that converts the model to a dictionary with camelCase field names for
       storage in Cosmos DB.

    4. Database metadata: Each model class includes metadata about its corresponding
       Cosmos DB container as class variables:
       - __db_name__: The database name
       - __container_name__: The container name
       - __partition_key__: The partition key path
       - __api_name__: The API this model belongs to

    Usage:
    - To create a model from Cosmos DB data:
      ```python
      # Manually (recommended for explicit mapping):
      cosmos_data = {"id": "123", "teamMemberId": "user1", "_rid": "some-rid"}

      # Map fields to Python property names
      python_data = {}
      for cosmos_key, value in cosmos_data.items():
          if not cosmos_key.startswith("_"):  # Filter system fields
              python_key = MyModel.model_config.get("json_schema_extra", {}).get(
                  "cosmos_to_python_map", {}).get(cosmos_key, cosmos_key)
              python_data[python_key] = value

      # Create the model
      my_model = MyModel(**python_data)
      ```

    - To convert a model to Cosmos DB format for storage:
      ```python
      cosmos_data = my_model.model_dump_cosmos()
      ```

    - To access database metadata:
      ```python
      db_name = MyModel.__db_name__
      container_name = MyModel.__container_name__
      partition_key = MyModel.__partition_key__
      api_name = MyModel.__api_name__
      ```
    """

    # Default class variables to be overridden by subclasses
    __db_name__ = ""
    __container_name__ = ""
    __partition_key__ = ""
    __api_name__ = ""

    @classmethod
    def get_db_name(cls) -> str:
        """Get the database name for this model."""
        return cls.__db_name__

    @classmethod
    def get_container_name(cls) -> str:
        """Get the container name for this model."""
        return cls.__container_name__

    @classmethod
    def get_partition_key(cls) -> str:
        """Get the partition key path for this model."""
        return cls.__partition_key__

    @classmethod
    def get_api_name(cls) -> str:
        """Get the API name this model belongs to."""
        return cls.__api_name__

    @classmethod
    def _get_python_to_cosmos_map(cls):
        """Get the Python to Cosmos DB field name mapping, generating it if needed.

        This method checks if the inverse mapping (python_to_cosmos_map) exists:
        1. First in the module-level cache
        2. Then in the model_config
        3. If not found, it generates the inverse of cosmos_to_python_map

        Returns:
            dict: The mapping from Python property names to Cosmos DB field names
        """
        # Check if we've already cached this mapping
        cls_name = cls.__name__
        if cls_name in _PYTHON_TO_COSMOS_MAPS:
            return _PYTHON_TO_COSMOS_MAPS[cls_name]

        # Check if mapping already exists in model_config
        python_map = cls.model_config.get("json_schema_extra", {}).get("python_to_cosmos_map")
        if python_map:
            # Cache it for future use
            _PYTHON_TO_COSMOS_MAPS[cls_name] = python_map
            return python_map

        # Get the cosmos_to_python_map
        cosmos_map = cls.model_config.get("json_schema_extra", {}).get("cosmos_to_python_map", {})
        if not cosmos_map:
            # No mapping defined, cache an empty dict
            _PYTHON_TO_COSMOS_MAPS[cls_name] = {}
            return {}

        # Generate the inverse mapping
        python_map = {python: cosmos for cosmos, python in cosmos_map.items()}

        # Cache it for future use
        _PYTHON_TO_COSMOS_MAPS[cls_name] = python_map
        return python_map

    @model_validator(mode='before')
    @classmethod
    def _pre_root_validator(cls, values):
        """Filter out Cosmos DB system fields and apply field name mapping."""
        if not isinstance(values, dict):
            return values

        # Create a copy to avoid modifying the input dict during iteration
        result = values.copy()

        # 1. Filter Cosmos DB system fields
        cosmos_fields_to_remove = []
        for key in result:
            # If field starts with '_' and it's not a model field, mark for removal
            if key.startswith('_') and not hasattr(cls, key):
                cosmos_fields_to_remove.append(key)

        # Remove all marked fields
        for key in cosmos_fields_to_remove:
            result.pop(key)

        # 2. Apply field name mappings if they exist
        cosmos_map = cls.model_config.get("json_schema_extra", {}).get("cosmos_to_python_map", {})
        if cosmos_map:
            for cosmos_name, python_name in cosmos_map.items():
                if cosmos_name in result:
                    result[python_name] = result.pop(cosmos_name)

        return result

    def model_dump_cosmos(self, **kwargs) -> dict:
        """Dump model as a dictionary using Cosmos DB field names."""
        # First get the normal model dict with Python property names
        data = self.model_dump(**kwargs)

        # Get the Python -> Cosmos mapping (dynamically generated if needed)
        python_map = self.__class__._get_python_to_cosmos_map()
        if not python_map:
            return data

        # Create a new dict with transformed keys
        result = {}
        for key, value in data.items():
            # Use cosmos name if available, otherwise keep the original key
            cosmos_key = python_map.get(key, key)
            result[cosmos_key] = value

        return result
'''

# Template for Python API-specific model files
PYTHON_API_MODELS_TEMPLATE = '''# Generated from database_tables.yaml on {timestamp}
# DO NOT EDIT THIS FILE MANUALLY - Your changes will be overwritten
# API: {api_name}

from typing import Any, Annotated, Literal, Callable, TypeVar  # noqa F401
# Using Python 3.12+ type annotation style (PEP 604)
# Optional[T] -> T | None
# Union[T, U] -> T | U
# List[T] -> list[T]
# Dict[K, V] -> dict[K, V]
from pydantic import BaseModel, Field, ConfigDict, model_validator, field_serializer
from datetime import date, datetime
from .cosmos_base import CosmosBaseModel

{models}
'''

# Template for backward compatibility database.py
PYTHON_BACKWARD_COMPAT_TEMPLATE = '''# Generated from database_tables.yaml on {timestamp}
# DEPRECATED: This file is maintained for backward compatibility only.
# Please update imports to use the new API-specific modules:
# - from definitions.generated.python.team_data_api_base_models import TeamMember
# - from definitions.generated.python.finance_api_base_models import DimAccount

import warnings

warnings.warn(
    "The 'database.py' module is deprecated. Please update your imports to use "
    "API-specific modules (e.g., 'team_data_api_base_models', 'finance_api_base_models')",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all models for backward compatibility
from .cosmos_base import CosmosBaseModel
{imports}

__all__ = [
    'CosmosBaseModel',
{all_exports}
]
'''

# Template for new __init__.py that aggregates all models
PYTHON_INIT_AGGREGATED_TEMPLATE = '''# Generated from database_tables.yaml on {timestamp}
# Aggregates all generated models for convenient import

from .cosmos_base import CosmosBaseModel
{imports}

# Export all models
__all__ = [
    'CosmosBaseModel',
{all_exports}
]
'''

# Template for Python model class
PYTHON_MODEL_CLASS_TEMPLATE = """
class {class_name}(CosmosBaseModel):
    \"\"\"
    {class_name}

    {description}
    \"\"\"
    # Database metadata as class variables
    __db_name__ = "{db_name}"
    __container_name__ = "{container_name}"
    __partition_key__ = "{partition_key}"
    __api_name__ = "{api_name}"
{fields}
"""

# TypeScript templates for split files
TS_BASE_TEMPLATE = """/**
 * Generated from database_tables.yaml on {timestamp}
 * Base utilities for Cosmos DB compatibility
 */

// Field name mapping utilities
export type FieldMappings = {{
  [key: string]: string;
}};

/**
 * Base interface for Cosmos DB mapping functionality
 *
 * This interface defines methods that help with mapping between TypeScript property
 * names and Cosmos DB field names, and filtering Cosmos DB system fields.
 */
export interface CosmosMapping<T> {{
  /**
   * Maps from Cosmos DB field names to TypeScript property names
   */
  readonly cosmosToTypeScriptMap: FieldMappings;

  /**
   * Maps from TypeScript property names to Cosmos DB field names
   */
  readonly typeScriptToCosmosMap: FieldMappings;

  /**
   * Converts a Cosmos DB object to TypeScript interface format
   *
   * @param cosmosObj - Object with Cosmos DB field names
   * @returns Object with TypeScript property names
   */
  fromCosmosDB(cosmosObj: any): T;

  /**
   * Converts a TypeScript interface to Cosmos DB format
   *
   * @param tsObj - Object with TypeScript property names
   * @returns Object with Cosmos DB field names
   */
  toCosmosDB(tsObj: T): any;
}};

/**
 * Creates a mapping utility object for a specific model type
 *
 * @param cosmosToTs - Mapping from Cosmos DB field names to TypeScript property names
 * @param tsToDb - Mapping from TypeScript property names to Cosmos DB field names
 * @returns Mapping utility object
 */
export function createCosmosMapping<T>(cosmosToTs: FieldMappings, tsToDb: FieldMappings): CosmosMapping<T> {{
  return {{
    cosmosToTypeScriptMap: cosmosToTs,
    typeScriptToCosmosMap: tsToDb,

    fromCosmosDB(cosmosObj: any): T {{
      if (!cosmosObj) return {{}} as T;

      // Create a new object to hold the result
      const result: any = {{}};

      // Process each field in the cosmos object
      for (const [key, value] of Object.entries(cosmosObj)) {{
        // Skip Cosmos DB system fields
        if (key.startsWith('_')) continue;

        // Map the field name or keep it if no mapping exists
        const tsKey = this.cosmosToTypeScriptMap[key] || key;
        result[tsKey] = value;
      }}

      return result as T;
    }},

    toCosmosDB(tsObj: T): any {{
      if (!tsObj) return {{}};

      // Create a new object to hold the result
      const result: any = {{}};

      // Process each field in the TypeScript object
      for (const [key, value] of Object.entries(tsObj)) {{
        // Map the field name or keep it if no mapping exists
        const cosmosKey = this.typeScriptToCosmosMap[key] || key;
        result[cosmosKey] = value;
      }}

      return result;
    }}
  }};
}};
"""

TS_API_MODELS_TEMPLATE = """/**
 * Generated from database_tables.yaml on {timestamp}
 * DO NOT EDIT THIS FILE MANUALLY - Your changes will be overwritten
 * API: {api_name}
 */

import {{ CosmosMapping, createCosmosMapping }} from './cosmos-base';

{enums}

{interfaces}

{mappings}
"""

# Template for TypeScript enum
TS_ENUM_TEMPLATE = """export enum {enum_name} {{
{enum_values}
}}
"""

# Template for TypeScript interface
TS_INTERFACE_TEMPLATE = """/**
 * {title}
 *
 * {description}
 */
export interface {interface_name} {{
{fields}
}}
"""

# Template for TypeScript mapping object
TS_MAPPING_TEMPLATE = """/**
 * Mapping utility for {interface_name}
 *
 * Provides methods to convert between Cosmos DB and TypeScript formats
 */
export const {mapping_var_name}: CosmosMapping<{interface_name}> = createCosmosMapping(
  // Cosmos DB field name -> TypeScript property name
  {{
{cosmos_to_ts_map}
  }},
  // TypeScript property name -> Cosmos DB field name
  {{
{ts_to_cosmos_map}
  }}
);
"""

# Template for TypeScript index.ts file
TS_INDEX_AGGREGATED_TEMPLATE = """/**
 * Generated from database_tables.yaml on {timestamp}
 * Aggregates all generated models for convenient import
 */

export * from './cosmos-base';
{exports}
"""

# Helper function to convert API name to snake_case filename
def api_name_to_snake_case(api_name):
    """Convert API name to snake_case for file naming."""
    # Remove 'API' suffix if present
    name = re.sub(r'\s+API$', '', api_name, flags=re.I)
    # Convert to lowercase and replace spaces with underscores
    name = name.lower().replace(' ', '_')
    # Remove any non-alphanumeric characters except underscores
    name = re.sub(r'[^a-z0-9_]', '', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name)
    return name.strip('_')

# Helper function to convert API name to kebab-case filename
def api_name_to_kebab_case(api_name):
    """Convert API name to kebab-case for TypeScript file naming."""
    # Remove 'API' suffix if present
    name = re.sub(r'\s+API$', '', api_name, flags=re.I)
    # Convert to lowercase and replace spaces with hyphens
    name = name.lower().replace(' ', '-')
    # Remove any non-alphanumeric characters except hyphens
    name = re.sub(r'[^a-z0-9-]', '', name)
    # Collapse multiple hyphens
    name = re.sub(r'-+', '-', name)
    return name.strip('-')

# Helper function to convert snake_case to camelCase
def to_camel_case(snake_str):
    """Convert snake_case string to camelCase."""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

# Helper function to convert snake_case to PascalCase
def to_pascal_case(snake_str):
    """Convert snake_case string to PascalCase."""
    components = snake_str.split('_')
    return ''.join(x.title() for x in components)

def get_python_type(field):
    """Convert YAML field type to Python type using Python 3.11 syntax for Pydantic 2.4."""
    # Handle enums with Literal types
    if "enum" in field:
        # If field has enum values, return Literal type
        enum_values = field["enum"]
        if enum_values:
            return f"Literal[{', '.join([repr(val) for val in enum_values])}]"

    # For object types, use dict with proper typing (Python 3.11 style)
    if field.get("type") == "object":
        if "properties" in field:
            # This is a complex object with defined properties
            # Could create nested models for complex objects, but that gets complicated
            # Using dict[str, Any] for simplicity (Python 3.11 style)
            return "dict[str, Any]"
        return "dict[str, Any]"  # Generic dict type

    base_type = PYTHON_TYPE_MAP.get(field.get("type", "string"), "Any")

    # Handle arrays with proper generic types (Python 3.11 style)
    if base_type == "List":
        if isinstance(field.get("items"), dict) and "type" in field.get("items", {}):
            item_type = field["items"]["type"]
            if item_type == "string":
                return "list[str]"  # List of strings
            elif item_type == "integer":
                return "list[int]"  # List of integers
            elif item_type == "number":
                return "list[float]"  # List of floats
            elif item_type == "boolean":
                return "list[bool]"  # List of booleans
            elif item_type == "object":
                return "list[dict[str, Any]]"  # List of objects
            else:
                return "list[Any]"  # Generic list
        elif isinstance(field.get("items"), str):
            # If items is a string, it's a reference to another type
            item_type = PYTHON_TYPE_MAP.get(field.get("items"), "Any")
            return f"list[{item_type}]"
        else:
            return "list[Any]"  # Generic list

    # Handle dates
    if "format" in field:
        if field["format"] == "date":
            return "date"
        elif field["format"] == "date-time":
            return "datetime"

    # Map other types to simple Python types
    type_mapping = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "Any": "Any"
    }

    return type_mapping.get(base_type, base_type)

def get_ts_type(field):
    """Convert YAML field type to TypeScript type."""
    base_type = TS_TYPE_MAP.get(field.get("type", "string"), "any")

    if base_type == "Array":
        if isinstance(field.get("items"), dict):
            if "type" in field.get("items", {}):
                item_type = TS_TYPE_MAP.get(field["items"]["type"], "any")
                if item_type == "Array" or item_type == "Record":
                    return f"{base_type}<any>"
                return f"{base_type}<{item_type}>"
            else:
                return f"{base_type}<{{ [key: string]: any }}>"
        elif isinstance(field.get("items"), str):
            item_type = TS_TYPE_MAP.get(field["items"], "any")
            return f"{base_type}<{item_type}>"
        return f"{base_type}<any>"

    if field.get("type") == "object":
        # Handle nested objects
        if "properties" in field:
            props = []
            for prop in field.get("properties", []):
                props.append(f"{prop.get('name')}: {get_ts_type(prop)}")
            return f"{{ {'; '.join(props)} }}"

    # Handle enums
    if "enum" in field:
        enum_values = " | ".join([f"'{val}'" for val in field["enum"]])
        return enum_values

    return base_type

def generate_python_model_for_schema(schema_name, schema_def):
    """Generate a single Python model class from a schema definition."""
    # Skip schemas without python_class_name - they don't want Python models generated
    if "python_class_name" not in schema_def:
        return None, None

    # Use python_class_name from schema
    class_name = schema_def["python_class_name"]

    # Generate fields
    fields_text = ""
    seen_field_names = set()  # Track field names to prevent duplicates

    # Track field mappings for the cosmos_to_python mapper
    field_mappings = {}  # Original Cosmos DB name -> Python property name
    has_custom_property_names = False

    for field in schema_def.get("fields", []):
        # Get original field name from schema
        original_field_name = field["name"]

        # Use python_property_name if present, otherwise fall back to name
        field_name = field.get("python_property_name", original_field_name)

        # Check if this field has a custom property name
        if field.get("python_property_name") and field["python_property_name"] != original_field_name:
            field_mappings[original_field_name] = field["python_property_name"]
            has_custom_property_names = True

        # Store the original field name in the field dictionary for serializer use later
        field["original_name"] = original_field_name

        # Skip duplicate field names
        if field_name in seen_field_names:
            print(f"Warning: Duplicate field '{field_name}' in {class_name}. Skipping duplicate.")
            continue

        seen_field_names.add(field_name)
        field_type = get_python_type(field)
        is_required = field.get("required", False)

        # Check for contradictory field definitions (validation warning)
        if is_required and "default" in field:
            print(f"⚠️  Warning in {class_name}.{field_name}: "
                  f"Field has both 'required: true' and a 'default' value. "
                  f"Fields with defaults should not be marked as required. "
                  f"Treating as field with default (not required).")

        # Ensure description strings are properly escaped
        description = field.get('description', '').replace('"', '\\"')
        title = field.get('title', field_name).replace('"', '\\"')

        # Build field definition - prioritize defaults over required flag
        has_default = "default" in field
        is_empty_list_default = field_type.startswith("list") and field.get("default") == []

        if has_default and not is_empty_list_default:
            # Field has a concrete default value (not empty list)
            default_val = field.get("default")
            if isinstance(default_val, str):
                field_def = f"    {field_name}: {field_type} = Field(default=\"{default_val}\", "
            elif isinstance(default_val, bool):
                field_def = f"    {field_name}: {field_type} = Field(default={default_val}, "
            else:
                field_def = f"    {field_name}: {field_type} = Field(default={default_val}, "
        elif is_empty_list_default:
            # Special case: array with empty list default
            field_def = f"    {field_name}: {field_type} = Field(default=[], "
        elif is_required:
            # Field is required with no default value
            field_def = f"    {field_name}: {field_type} = Field(..., "
        else:
            # Field is optional (not required, no default)
            # Use Python 3.11 style: Optional[T] -> T | None
            field_def = f"    {field_name}: {field_type} | None = Field(None, "

        field_def += f"description=\"{description}\", "
        field_def += f"title=\"{title}\""

        # Add validation parameters for min/max values
        if "minimum" in field and field.get("type") in ["integer", "number"]:
            field_def += f", ge={field.get('minimum')}"
        if "maximum" in field and field.get("type") in ["integer", "number"]:
            field_def += f", le={field.get('maximum')}"

        # Add string validation for min/max length
        if "minLength" in field and field.get("type") == "string":
            field_def += f", min_length={field.get('minLength')}"
        if "maxLength" in field and field.get("type") == "string":
            field_def += f", max_length={field.get('maxLength')}"

        # Close the Field parameter list
        field_def += ")"

        # Add enum values as comments for documentation (even though we're now using Literal types)
        if "enum" in field:
            enum_values = ", ".join([f'"{val}"' for val in field["enum"]])
            field_def += f"  # Allowed values: {enum_values}"
        fields_text += field_def + "\n"

    # Generate model validators
    validators_text = ""

    # Add Cosmos DB field name mapping if needed
    if has_custom_property_names:
        # Only store the cosmos_to_python map - the inverse will be generated when needed
        cosmos_map_str = ", ".join([f'"{cosmos}": "{python}"' for cosmos, python in field_mappings.items()])

        validators_text += f"""
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        # Store only the primary mapping - inverse will be generated automatically when needed
        json_schema_extra={{
            "cosmos_to_python_map": {{{cosmos_map_str}}}
        }}
    )
"""
    else:
        validators_text += """
    model_config = ConfigDict(
        populate_by_name=True, extra="forbid", str_strip_whitespace=True
    )
"""

    # Check if any fields have format or pattern constraints that need validators
    date_fields = []
    email_fields = []

    for field in schema_def.get("fields", []):
        if field.get("format") == "date" or field.get("format") == "date-time":
            # Only for optional date fields that may be None
            if not field.get("required", False):
                date_fields.append(field["name"])
        if field["name"].lower().endswith("email") and field.get("type") == "string":
            email_fields.append(field["name"])

    # Add validators for date fields if needed
    if date_fields:
        validators_text += f"""
    @model_validator(mode='after')
    def validate_date_fields(self) -> '{class_name}':
        \"\"\"Validate date fields that should be None or valid dates.\"\"\"
        # Validation logic here if needed
        return self
"""

    # Add field serializers for specific types
    date_serializer_fields = [f for f in schema_def.get("fields", [])
                              if f.get("format") == "date" or f.get("format") == "date-time"]
    if date_serializer_fields:
        # Get all date field names - use python_property_name for serializer references if available
        date_field_names = []
        for f in date_serializer_fields:
            if "python_property_name" in f:
                date_field_names.append(f["python_property_name"])
            else:
                date_field_names.append(f["name"])
        if date_field_names:
            # Add a date serializer that converts dates to ISO format strings
            validators_text += f"""
    @field_serializer({', '.join([f"'{name}'" for name in date_field_names])})
    def serialize_dates(self, date_value: date | datetime | None) -> str | None:
        \"\"\"Serialize date fields to ISO format strings.\"\"\"
        if date_value is None:
            return None
        if isinstance(date_value, datetime):
            return date_value.isoformat()
        return date_value.isoformat()
"""

    # Generate the model
    model_text = PYTHON_MODEL_CLASS_TEMPLATE.format(
        class_name=class_name,
        title=schema_def.get('title', class_name),
        description=schema_def.get('description', ''),
        db_name=schema_def.get('db_name', ''),
        container_name=schema_def.get('db_container_name', ''),
        partition_key=schema_def.get('partition_key', ''),
        api_name=schema_def.get('api_name', ''),
        fields=fields_text + validators_text[validators_text.find('\n') + 1:] if validators_text else ""
    )

    return class_name, model_text

def generate_python_models_split(schemas, output_dir):
    """Generate Pydantic models split by API."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Group schemas by api_name
    schemas_by_api = defaultdict(list)
    for schema_name, schema_def in schemas.items():
        api_name = schema_def.get('api_name', 'Common')
        schemas_by_api[api_name].append((schema_name, schema_def))

    # Track all model names for exports
    all_model_names = []
    api_file_imports = []

    # Write cosmos_base.py
    base_path = output_dir / "cosmos_base.py"
    with open(base_path, "w") as f:
        f.write(COSMOSDB_BASE_MODEL)

    # Generate file for each API
    for api_name, api_schemas in schemas_by_api.items():
        # Convert API name to filename
        file_base_name = api_name_to_snake_case(api_name) + "_api_base_models"

        # Generate models for this API
        models_text = ""
        api_model_names = []

        for schema_name, schema_def in api_schemas:
            class_name, model_text = generate_python_model_for_schema(schema_name, schema_def)
            if class_name is None:  # Schema was skipped (no python_class_name)
                continue
            models_text += model_text
            api_model_names.append(class_name)
            all_model_names.append(class_name)

        # Write API-specific file
        api_file_path = output_dir / f"{file_base_name}.py"
        with open(api_file_path, "w") as f:
            f.write(PYTHON_API_MODELS_TEMPLATE.format(
                timestamp=timestamp,
                api_name=api_name,
                models=models_text
            ))

        # Add import for this API file
        api_file_imports.append(f"from .{file_base_name} import {', '.join(api_model_names)}")

    # Write __init__.py with all imports
    init_path = output_dir / "__init__.py"
    with open(init_path, "w") as f:
        imports_text = "\n".join(api_file_imports)
        all_exports = "\n".join([f"    '{name}'," for name in all_model_names])
        f.write(PYTHON_INIT_AGGREGATED_TEMPLATE.format(
            timestamp=timestamp,
            imports=imports_text,
            all_exports=all_exports
        ))

    # Write backward compatibility database.py
    database_path = output_dir / "database.py"
    with open(database_path, "w") as f:
        imports_text = "\n".join(api_file_imports)
        all_exports = "\n".join([f"    '{name}'," for name in all_model_names])
        f.write(PYTHON_BACKWARD_COMPAT_TEMPLATE.format(
            timestamp=timestamp,
            imports=imports_text,
            all_exports=all_exports
        ))

def generate_typescript_interfaces_split(schemas, output_dir):
    """Generate TypeScript interfaces split by API."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Group schemas by api_name
    schemas_by_api = defaultdict(list)
    for schema_name, schema_def in schemas.items():
        api_name = schema_def.get('api_name', 'Common')
        schemas_by_api[api_name].append((schema_name, schema_def))

    # Track all exports
    all_exports = []

    # Write cosmos-base.ts
    base_path = output_dir / "cosmos-base.ts"
    with open(base_path, "w") as f:
        f.write(TS_BASE_TEMPLATE.format(timestamp=timestamp))

    # Process each API
    for api_name, api_schemas in schemas_by_api.items():
        # Convert API name to filename
        file_base_name = api_name_to_kebab_case(api_name) + "-api-base-models"

        # Generate enums, interfaces, and mappings for this API
        all_enums = ""
        all_interfaces = ""
        all_mappings = ""
        processed_enum_names = set()

        for schema_name, schema_def in api_schemas:
            # Skip schemas without typescript_class_name - they don't want TypeScript interfaces generated
            if "typescript_class_name" not in schema_def:
                continue

            # Use typescript_class_name from schema
            interface_name = schema_def["typescript_class_name"]

            # Generate enums for fields with enum values
            for field in schema_def.get("fields", []):
                if "enum" in field:
                    field_prop_name = field.get("typescript_property_name", field["name"])
                    enum_name = interface_name + to_pascal_case(field_prop_name) + "Enum"

                    if enum_name not in processed_enum_names:
                        processed_enum_names.add(enum_name)

                        enum_values_text = ""
                        for enum_val in field["enum"]:
                            enum_key = re.sub(r'[^a-zA-Z0-9]', '_', enum_val).upper()
                            enum_values_text += f"  {enum_key} = '{enum_val}',\n"

                        enum_text = TS_ENUM_TEMPLATE.format(
                            enum_name=enum_name,
                            enum_values=enum_values_text
                        )
                        all_enums += enum_text + "\n"

            # Track field mappings for this interface
            cosmos_to_ts_mappings = {}
            ts_to_cosmos_mappings = {}
            has_custom_property_names = False

            # Generate fields
            fields_text = ""
            for field in schema_def.get("fields", []):
                original_field_name = field["name"]
                field_name = field.get("typescript_property_name", original_field_name)

                # Check for custom property names
                if field.get("typescript_property_name") and field["typescript_property_name"] != original_field_name:
                    cosmos_to_ts_mappings[original_field_name] = field["typescript_property_name"]
                    ts_to_cosmos_mappings[field["typescript_property_name"]] = original_field_name
                    has_custom_property_names = True
                elif field.get("python_property_name"):
                    has_custom_property_names = True
                    if original_field_name not in cosmos_to_ts_mappings:
                        cosmos_to_ts_mappings[original_field_name] = original_field_name
                        ts_to_cosmos_mappings[original_field_name] = original_field_name

                field_type = get_ts_type(field)

                # Add comments
                fields_text += f"  /** {field.get('title', field_name)} - {field.get('description', '')} */\n"

                # Mark as optional if not required
                is_required = field.get("required", False)
                if is_required:
                    fields_text += f"  {field_name}: {field_type};\n"
                else:
                    fields_text += f"  {field_name}?: {field_type};\n"

            # Add interface
            interface_text = TS_INTERFACE_TEMPLATE.format(
                interface_name=interface_name,
                title=schema_def.get('title', interface_name),
                description=schema_def.get('description', ''),
                fields=fields_text
            )
            all_interfaces += interface_text + "\n"

            # Create mappings if needed
            if has_custom_property_names:
                mapping_var_name = f"{to_camel_case(schema_name)}Mapping"

                cosmos_to_ts_map = ""
                ts_to_cosmos_map = ""

                for db_name, ts_name in cosmos_to_ts_mappings.items():
                    cosmos_to_ts_map += f"    '{db_name}': '{ts_name}',\n"

                for ts_name, db_name in ts_to_cosmos_mappings.items():
                    ts_to_cosmos_map += f"    '{ts_name}': '{db_name}',\n"

                mapping_text = TS_MAPPING_TEMPLATE.format(
                    interface_name=interface_name,
                    mapping_var_name=mapping_var_name,
                    cosmos_to_ts_map=cosmos_to_ts_map,
                    ts_to_cosmos_map=ts_to_cosmos_map
                )
                all_mappings += mapping_text + "\n"

        # Write API-specific file
        api_file_path = output_dir / f"{file_base_name}.ts"
        with open(api_file_path, "w") as f:
            f.write(TS_API_MODELS_TEMPLATE.format(
                timestamp=timestamp,
                api_name=api_name,
                enums=all_enums,
                interfaces=all_interfaces,
                mappings=all_mappings
            ))

        # Add to exports list
        all_exports.append(f"export * from './{file_base_name}';")

    # Write index.ts
    index_path = output_dir / "index.ts"
    with open(index_path, "w") as f:
        exports_text = "\n".join(all_exports)
        f.write(TS_INDEX_AGGREGATED_TEMPLATE.format(
            timestamp=timestamp,
            exports=exports_text
        ))

def parse_args():
    """Parse command-line arguments for validation options."""
    parser = argparse.ArgumentParser(
        description="Generate Pydantic models and TypeScript interfaces from all YAML files in database_tables/ directory (split by API)"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip mypy and flake8 validation of generated code"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error code if validation fails (default: warn only)"
    )
    parser.add_argument(
        "--schema-dir",
        type=str,
        help="Custom directory containing schema YAML files (default: definitions/common/database_tables/)"
    )
    return parser.parse_args()

def ensure_dirs():
    """Create output directories if they don't exist."""
    base_dir = Path(__file__).parent.parent
    py_dir = base_dir / "definitions" / "generated" / "python"
    ts_dir = base_dir / "definitions" / "generated" / "typescript"

    py_dir.mkdir(parents=True, exist_ok=True)
    ts_dir.mkdir(parents=True, exist_ok=True)

    return base_dir, py_dir, ts_dir

def load_all_schema_files(schema_dir):
    """Load and merge all schema files from the database_tables directory.

    Args:
        schema_dir: Path to the database_tables directory

    Returns:
        dict: Merged schemas from all YAML files
    """
    all_schemas = {}
    duplicate_warnings = []

    # Check if directory exists
    if not schema_dir.exists():
        print(f"Warning: Schema directory {schema_dir} does not exist")
        return all_schemas

    # Find all YAML files in the directory
    yaml_files = sorted(schema_dir.glob("*.yaml"))

    if not yaml_files:
        print(f"Warning: No YAML files found in {schema_dir}")
        return all_schemas

    print(f"Loading schemas from {len(yaml_files)} files:")

    for yaml_file in yaml_files:
        # Skip the field sets file
        if yaml_file.name == "reused_field_sets.yaml":
            continue

        print(f"  - {yaml_file.name}")
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            # Get schemas from this file
            file_schemas = data.get("database_schemas", {})

            if not file_schemas:
                print(f"    Warning: No database_schemas found in {yaml_file.name}")
                continue

            # Check for duplicates before merging
            for schema_name, schema_def in file_schemas.items():
                if schema_name in all_schemas:
                    duplicate_warnings.append(f"    Warning: Schema '{schema_name}' already defined, overwriting with version from {yaml_file.name}")
                all_schemas[schema_name] = schema_def

            print(f"    Loaded {len(file_schemas)} schemas")

        except Exception as e:
            print(f"    Error loading {yaml_file.name}: {e}")

    # Print any duplicate warnings
    for warning in duplicate_warnings:
        print(warning)

    print(f"Total schemas loaded: {len(all_schemas)}")
    return all_schemas

def load_field_sets(schema_dir):
    """Load reusable field sets from reused_field_sets.yaml if it exists."""
    field_sets_path = schema_dir / "reused_field_sets.yaml"

    if not field_sets_path.exists():
        return {}

    try:
        with open(field_sets_path, "r") as f:
            data = yaml.safe_load(f)
            field_sets = data.get("field_sets", {})
            print(f"Loaded {len(field_sets)} field sets from reused_field_sets.yaml")
            for set_name in field_sets:
                field_count = len(field_sets[set_name].get("fields", []))
                print(f"  - {set_name}: {field_count} fields")
            return field_sets
    except Exception as e:
        print(f"Warning: Failed to load field sets: {e}")
        return {}


def merge_field_sets_into_schema(schema_def, field_sets):
    """Merge included field sets into a schema definition.

    If a schema has include_field_sets property, merge the referenced
    field sets' fields with the schema's own fields. Schema-specific fields
    take precedence in case of conflicts.
    """
    include_fields = schema_def.get("include_field_sets", [])

    if not include_fields:
        return schema_def

    # Create a copy to avoid modifying the original
    merged_schema = schema_def.copy()

    # Track field names already in the schema to avoid duplicates
    existing_field_names = {field["name"] for field in merged_schema.get("fields", [])}

    # Process each included field set
    merged_fields = []
    for field_set_name in include_fields:
        if field_set_name not in field_sets:
            print(f"    Warning: Field set '{field_set_name}' not found in reused_field_sets.yaml")
            continue

        field_set = field_sets[field_set_name]
        for field in field_set.get("fields", []):
            # Only add fields that don't already exist in the schema
            if field["name"] not in existing_field_names:
                merged_fields.append(field)
                existing_field_names.add(field["name"])

    # Prepend merged fields to schema's existing fields
    # (schema-specific fields come after to allow overrides)
    merged_schema["fields"] = merged_fields + merged_schema.get("fields", [])

    return merged_schema

def main():
    """Main function to generate models from YAML schema."""
    # Parse command-line arguments
    args = parse_args()

    base_dir, py_dir, ts_dir = ensure_dirs()

    # New approach: Load all schemas from database_tables directory
    if args.schema_dir:
        schema_dir = Path(args.schema_dir)
    else:
        schema_dir = base_dir / "definitions" / "common" / "database_tables"

    # Check for backward compatibility - if directory doesn't exist, try old location
    if not schema_dir.exists():
        print("Info: New database_tables directory not found, checking legacy location...")
        legacy_yaml_path = base_dir / "definitions" / "common" / "database_tables.yaml"
        if legacy_yaml_path.exists():
            print(f"Loading from legacy location: {legacy_yaml_path}")
            with open(legacy_yaml_path, "r") as f:
                data = yaml.safe_load(f)
            schemas = data.get("database_schemas", {})
        else:
            print("Error: No schema files found in either new or legacy locations")
            schemas = {}
    else:
        # Load field sets first
        field_sets = load_field_sets(schema_dir)

        # Load all schemas from the directory
        all_schemas = load_all_schema_files(schema_dir)

        # Merge field sets into schemas that include them
        schemas = {}
        for schema_name, schema_def in all_schemas.items():
            merged_schema = merge_field_sets_into_schema(schema_def, field_sets)
            schemas[schema_name] = merged_schema

    # Generate split Python models
    generate_python_models_split(schemas, py_dir)
    print(f"Generated split Python models in {py_dir}")

    # Format Python models with Black
    try:
        # Format all Python files
        for py_file in py_dir.glob("*.py"):
            subprocess.run(["black", str(py_file)], check=True, capture_output=True)
        print(f"Formatted all Python files with Black")
    except (ImportError, subprocess.SubprocessError) as e:
        print(f"Warning: Failed to format: {str(e)}")

    # Generate split TypeScript interfaces
    generate_typescript_interfaces_split(schemas, ts_dir)
    print(f"Generated split TypeScript interfaces in {ts_dir}")

    print("\n" + "="*60)
    print("✨ Generation Complete!")
    print("="*60)
    print("\nGenerated files split by API:")
    print("- Python models: *_api_base_models.py")
    print("- TypeScript models: *-api-base-models.ts")
    print("- Backward compatibility maintained via database.py")
    print("\nTo use these models in other repositories:")
    print("1. Python: Import from API-specific files or use __init__.py aggregation")
    print("2. TypeScript: Import from API-specific files or use index.ts aggregation")

if __name__ == "__main__":
    main()