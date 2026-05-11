# obsidian-bases

> Create and edit Obsidian Bases (.base files) with views, filters, formulas, and summaries. Use when working with .base files, creating database-like views of notes, or when the user mentions Bases, table views, card views, filters, or formulas in Obsidian.

## Metadata

- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/note-taking/obsidian-bases/SKILL.md`

## Skill Body

# Obsidian Bases Skill

## Workflow

1. **Create the file**: Create a `.base` file in the vault with valid YAML content
2. **Define scope**: Add `filters` to select which notes appear (by tag, folder, property, or date)
3. **Add formulas** (optional): Define computed properties in the `formulas` section
4. **Configure views**: Add one or more views (`table`, `cards`, `list`, or `map`) with `order` specifying which properties to display
5. **Validate**: Verify the file is valid YAML with no syntax errors. Check that all referenced properties and formulas exist. Common issues: unquoted strings containing special YAML characters, mismatched quotes in formula expressions, referencing `formula.X` without defining `X` in `formulas`
6. **Test in Obsidian**: Open the `.base` file in Obsidian to confirm the view renders correctly. If it shows a YAML error, check quoting rules below

## Schema

Base files use the `.base` extension and contain valid YAML.

```yaml
# Global filters apply to ALL views in the base
filters:
  # Can be a single filter string
  # OR a recursive filter object with and/or/not
  and: []
  or: []
  not: []

# Define formula properties that can be used across all views
formulas:
  formula_name: 'expression'

# Configure display names and settings for properties
properties:
  property_name:
    displayName: "Display Name"
  formula.formula_name:
    displayName: "Formula Display Name"
  file.ext:
    displayName: "Extension"

# Define custom summary formulas
summaries:
  custom_summary_name: 'values.mean().round(3)'

# Define one or more views
views:
  - type: table | cards | list | map
    name: "View Name"
    limit: 10                    # Optional: limit results
    groupBy:                     # Optional: group results
      property: property_name
      direction: ASC | DESC
    filters:                     # View-specific filters
      and: []
    order:                       # Properties to display in order
      - file.name
      - property_name
      - formula.formula_name
    summaries:                   # Map properties to summary formulas
      property_name: Average
```

## Filter Syntax

Filters narrow down results. They can be applied globally or per-view.

### Filter Structure

```yaml
# Single filter
filters: 'status == "done"'

# AND - all conditions must be true
filters:
  and:
    - 'status == "done"'
    - 'priority > 3'

# OR - any condition can be true
filters:
  or:
    - 'file.hasTag("book")'
    - 'file.hasTag("article")'

# NOT - exclude matching items
filters:
  not:
    - 'file.hasTag("archived")'

# Nested filters
filters:
  or:
    - file.hasTag("tag")
    - and:
        - file.hasTag("book")
        - file.hasLink("Textbook")
    - not:
        - file.hasTag("book")
```

### Filter Functions

| Function | Description | Example |
|----------|-------------|---------|
| `file.hasTag("tag")` | Note has tag | `file.hasTag("project")` |
| `file.hasLink("Note")` | Note links to | `file.hasLink("Meeting Notes")` |
| `file.path` | Note path | `file.path == "projects/"` |
| `file.name` | Note name | `file.name == "README"` |
| `file.ext` | File extension | `file.ext == "md"` |
| `file.size` | File size in bytes | `file.size > 1000` |
| `file.ctime` | Creation time | `file.ctime > 2024-01-01` |
| `file.mtime` | Modification time | `file.mtime > 2024-01-01` |
| `property == "value"` | Property equals | `status == "done"` |
| `property > 5` | Property greater than | `priority > 3` |
| `property < 10` | Property less than | `count < 100` |
| `property != "value"` | Property not equals | `status != "archived"` |
| `property` | Property exists | `due_date` |
| `!property` | Property missing | `!completed` |

## Formula Syntax

Formulas define computed properties. Use single quotes to avoid YAML parsing issues.

```yaml
formulas:
  days_old: '(today - file.ctime).days'
  word_count: 'file.size / 6'
  is_recent: 'file.mtime > (today - 7d)'
```

### Formula Functions

| Function | Description | Example |
|----------|-------------|---------|
| `today` | Current date | `today` |
| `now` | Current datetime | `now` |
| `values.mean()` | Average of values | `values.mean().round(2)` |
| `values.sum()` | Sum of values | `values.sum()` |
| `values.min()` | Minimum value | `values.min()` |
| `values.max()` | Maximum value | `values.max()` |
| `values.count()` | Count of values | `values.count()` |
| `.round(n)` | Round to n decimals | `values.mean().round(2)` |
| `.days` | Convert to days | `(today - file.ctime).days` |
| `.months` | Convert to months | `(today - file.ctime).months` |

## View Types

### Table View

```yaml
views:
  - type: table
    name: "All Tasks"
    order:
      - file.name
      - status
      - priority
      - due_date
```

### Cards View

```yaml
views:
  - type: cards
    name: "Project Cards"
    order:
      - file.name
      - description
      - status
```

### List View

```yaml
views:
  - type: list
    name: "Simple List"
    order:
      - file.name
      - status
```

### Map View

```yaml
views:
  - type: map
    name: "Location Map"
    order:
      - file.name
      - location
```

## Quoting Rules

Always use single quotes for formula strings and filter expressions to avoid YAML parsing issues:

```yaml
# Good
formulas:
  my_formula: 'values.mean().round(2)'

# Bad - YAML may interpret special characters
formulas:
  my_formula: values.mean().round(2)
```

## Examples

### Task Manager

```yaml
filters:
  and:
    - file.hasTag("task")
    - 'status != "archived"'

formulas:
  days_open: '(today - file.ctime).days'

properties:
  status:
    displayName: "Status"
  priority:
    displayName: "Priority"
  days_open:
    displayName: "Days Open"

views:
  - type: table
    name: "Active Tasks"
    filters:
      and:
        - 'status != "done"'
    order:
      - priority
      - file.name
      - status
      - days_open
    groupBy:
      property: status
      direction: ASC
```

### Book Library

```yaml
filters:
  or:
    - file.hasTag("book")
    - file.hasTag("article")

properties:
  author:
    displayName: "Author"
  rating:
    displayName: "Rating"
  status:
    displayName: "Read Status"

views:
  - type: cards
    name: "Reading List"
    filters:
      and:
        - 'status == "reading"'
    order:
      - file.name
      - author
      - rating
      - status
```

## See Also

- [Obsidian Bases Documentation](https://help.obsidian.md/bases/syntax)
- [Filter Syntax Reference](https://help.obsidian.md/bases/filters)
- [Formula Reference](https://help.obsidian.md/bases/formulas)
