# Database Schema Definitions (YAML)

This directory contains the **single source of truth** for the Indomonitor database schema, defined in YAML format. These definitions can be used to generate SQL schemas, Python Pydantic models, TypeScript interfaces, and API documentation.

## Files

### `reused_field_sets.yaml`
Defines reusable collections of field definitions that can be included in multiple schemas.

**Field Sets:**
- `audit_timestamps` - Standard created_at/updated_at fields
- `extended_audit_timestamps` - Audit fields with user tracking (created_by/updated_by)
- `scraper_metadata` - Common scraper execution fields (started_at, completed_at, status)
- `agent_metadata` - AI agent execution fields (includes token_usage and report)

### `news_monitoring_tables.yaml`
Complete database schema definitions for the news monitoring system.

**Schemas (6 total):**
1. `news_sites` - News website configurations and monitoring metadata
2. `site_structure_reports` - Research agent findings about site structure
3. `scraper_scripts` - Version-controlled Python scraper code (stored as text)
4. `agent_runs` - Claude Code agent execution history
5. `scrape_runs` - Scraper execution history and results
6. `news_scrapes` - Scraped news articles with content

## Schema Structure

### Field Set Definition

```yaml
field_sets:
  field_set_name:
    description: "Purpose and usage"
    fields:
      - name: "field_name"                    # Database column name
        title: "Human Readable Title"         # UI display name
        type: "string|integer|timestamp|text|json|uuid"
        sql_type: "VARCHAR(255)|INT|TIMESTAMP|TEXT|JSON|CHAR(36)"
        description: "Field purpose and usage"
        required: true|false
        default: "default_value"              # Optional
        enum: ["value1", "value2"]            # Optional
        python_property_name: "field_name"    # Python snake_case
        typescript_property_name: "fieldName" # TypeScript camelCase
```

### Database Schema Definition

```yaml
database_schemas:
  schema_key:
    title: "Human Readable Name"
    description: "Purpose and usage"
    python_class_name: "ClassName"
    typescript_class_name: "ClassName"
    db_table_name: "table_name"
    db_name: "indomonitor"
    primary_key: "id"
    
    # Include reusable field sets
    include_field_sets: ["audit_timestamps", "agent_metadata"]
    
    # Schema-specific fields
    fields:
      - name: "custom_field"
        title: "Custom Field"
        type: "string"
        sql_type: "VARCHAR(255)"
        description: "Field description"
        required: true
        python_property_name: "custom_field"
        typescript_property_name: "customField"
    
    # Indexes for performance
    indexes:
      - name: "idx_field_name"
        columns: ["field_name"]
      - name: "ft_search"
        type: "FULLTEXT"
        columns: ["title", "content"]
    
    # Unique constraints
    unique_constraints:
      - name: "unique_constraint_name"
        columns: ["field1", "field2"]
```

## Field Types

### Basic Types
- `string` → `VARCHAR(255)`
- `integer` → `INT`
- `text` → `TEXT`
- `timestamp` → `TIMESTAMP`
- `json` → `JSON`
- `uuid` → `CHAR(36)`

### Special Attributes
- `required: true|false` - Whether field is mandatory
- `default: "value"` - Default value for field
- `enum: [...]` - Enumerated allowed values
- `computed: true` - Generated/computed column
- `primary_key: true` - Marks as primary key
- `foreign_key: {...}` - Foreign key relationship

### Foreign Key Definition

```yaml
foreign_key:
  table: "referenced_table"
  column: "id"
  on_delete: "CASCADE|SET NULL|RESTRICT"
```

## Using Field Sets

Field sets are merged into schemas using the `include_field_sets` directive:

```yaml
database_schemas:
  my_table:
    include_field_sets: ["audit_timestamps", "agent_metadata"]
    fields:
      # Schema-specific fields here
```

**Merging Rules:**
1. Field set fields are added to the schema
2. Schema-specific fields override field set fields if names conflict
3. Multiple field sets can be included (order matters for conflicts)

## Field Naming Conventions

### Database/SQL (snake_case)
```yaml
name: "created_at"
sql_type: "TIMESTAMP"
```

### Python (snake_case)
```yaml
python_property_name: "created_at"
```

### TypeScript (camelCase)
```yaml
typescript_property_name: "createdAt"
```

**Benefit:** Single definition automatically translates to all target language conventions.

## Indexes and Constraints

### Regular Index
```yaml
indexes:
  - name: "idx_status"
    columns: ["status"]
```

### Fulltext Index
```yaml
indexes:
  - name: "ft_title_content"
    type: "FULLTEXT"
    columns: ["title", "content"]
```

### Unique Constraint
```yaml
unique_constraints:
  - name: "unique_url_hash"
    columns: ["url_hash"]
```

### Multi-Column Unique Constraint
```yaml
unique_constraints:
  - name: "unique_site_version"
    columns: ["site_id", "version"]
```

## Code Generation (Future)

These YAML schemas will be used to generate:

### 1. SQL Schema
```sql
CREATE TABLE news_sites (
  id INT AUTO_INCREMENT PRIMARY KEY,
  url TEXT NOT NULL,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ...
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. Python Pydantic Models
```python
class NewsSite(BaseModel):
    id: int
    url: str
    name: Optional[str] = None
    created_at: datetime
    ...
    
    class Config:
        populate_by_name = True
```

### 3. TypeScript Interfaces
```typescript
interface NewsSite {
  id: number;
  url: string;
  name?: string;
  createdAt: Date;
  ...
}
```

### 4. OpenAPI/JSON Schema
```json
{
  "NewsSite": {
    "type": "object",
    "properties": {
      "id": {"type": "integer"},
      "url": {"type": "string"},
      ...
    },
    "required": ["id", "url", "createdAt"]
  }
}
```

## Modifying Schemas

### Adding a New Field

1. **Decide if it's reusable** - If multiple tables need it, add to `reused_field_sets.yaml`
2. **Edit the schema** - Add field definition to appropriate schema in `news_monitoring_tables.yaml`
3. **Include all attributes**:
   - `name`, `title`, `type`, `sql_type`
   - `description`, `required`
   - `python_property_name`, `typescript_property_name`
   - Optional: `enum`, `default`, `foreign_key`
4. **Update indexes** - If field needs indexing for queries
5. **Generate code** - Run code generators (when available)

### Adding a New Table

1. **Create schema definition** in `news_monitoring_tables.yaml`
2. **Include appropriate field sets** (usually `audit_timestamps`)
3. **Define all fields** with complete metadata
4. **Add indexes** for query performance
5. **Document relationships** with foreign_key definitions
6. **Generate code** - Run code generators (when available)

### Creating a New Field Set

1. **Identify pattern** - Find fields repeated across multiple schemas
2. **Add to `reused_field_sets.yaml`** with descriptive name
3. **Document usage** - Note which schemas should use it
4. **Refactor existing schemas** - Replace duplicated fields with `include_field_sets`

## Benefits of YAML Schema Approach

### 1. Single Source of Truth
- One authoritative definition
- Changes propagate automatically to all generated code
- No duplication between SQL, Python, TypeScript

### 2. Consistency
- Standardized naming conventions
- Common audit fields across all tables
- Uniform foreign key definitions

### 3. Type Safety
- Explicit types and constraints
- Enum definitions prevent invalid data
- Required vs optional fields clearly marked

### 4. Maintainability
- Clear, readable structure
- Version control friendly
- Easy to review and understand

### 5. Documentation
- Descriptions embedded in definitions
- Self-documenting schemas
- Aligns with domain-driven design

### 6. Automation
- Code generation for multiple languages
- Database migration generation
- API documentation generation

## Current Schema Statistics

- **Tables:** 6
- **Field Sets:** 4
- **Total Fields (including field sets):** ~60+
- **Foreign Key Relationships:** 10
- **Indexes:** 17
- **Unique Constraints:** 2

## Example: Complete Schema with Field Set

```yaml
agent_runs:
  title: "Agent Runs"
  description: "Execution history for Claude Code agents"
  python_class_name: "AgentRun"
  typescript_class_name: "AgentRun"
  db_table_name: "agent_runs"
  db_name: "indomonitor"
  primary_key: "id"
  
  # Includes: started_at, completed_at, status, token_usage, report
  include_field_sets: ["agent_metadata"]
  
  fields:
    - name: "id"
      type: "uuid"
      sql_type: "CHAR(36)"
      description: "UUID primary key"
      required: true
      primary_key: true
      
    - name: "agent_type"
      type: "string"
      sql_type: "VARCHAR(100)"
      description: "Type of agent that was executed"
      required: true
      enum: ["Manager", "Research", "ScriptWriter", "Debug", "Monitor", "Validation"]
```

**Result:** 7 total fields (5 from field set + 2 schema-specific)

## Validation

When creating or modifying schemas, verify:

- [ ] All required attributes present (name, type, sql_type, description, required)
- [ ] Naming conventions followed (snake_case for database, camelCase for TypeScript)
- [ ] Foreign keys reference existing tables
- [ ] Enum values are meaningful and complete
- [ ] Indexes added for frequently queried fields
- [ ] Unique constraints defined where needed
- [ ] Field sets used appropriately (don't duplicate common fields)

## Future Enhancements

1. **Code Generators** - Auto-generate SQL, Python, TypeScript
2. **Migration Generator** - Create database migrations from schema changes
3. **Validation Tool** - Validate YAML syntax and schema completeness
4. **Documentation Generator** - Create database documentation website
5. **Test Fixture Generator** - Generate test data from schemas
6. **GraphQL Schema Generator** - Generate GraphQL types and resolvers
