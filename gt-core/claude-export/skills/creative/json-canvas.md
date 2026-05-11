# json-canvas

> Create and edit JSON Canvas files (.canvas) with nodes, edges, groups, and connections. Use when working with .canvas files, creating visual canvases, mind maps, flowcharts, or when the user mentions Canvas files in Obsidian.

## Metadata

- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/creative/json-canvas/SKILL.md`

## Skill Body

# JSON Canvas Skill

## File Structure

A canvas file (`.canvas`) contains two top-level arrays following the [JSON Canvas Spec 1.0](https://jsoncanvas.org/spec/1.0/):

```json
{
  "nodes": [],
  "edges": []
}
```

- `nodes` (optional): Array of node objects
- `edges` (optional): Array of edge objects connecting nodes

## Common Workflows

### 1. Create a New Canvas

1. Create a `.canvas` file with the base structure `{"nodes": [], "edges": []}`
2. Generate unique 16-character hex IDs for each node (e.g., `"6f0ad84f44ce9c17"`)
3. Add nodes with required fields: `id`, `type`, `x`, `y`, `width`, `height`
4. Add edges referencing valid node IDs via `fromNode` and `toNode`
5. **Validate**: Parse the JSON to confirm it is valid. Verify all `fromNode`/`toNode` values exist in the nodes array

### 2. Add a Node to an Existing Canvas

1. Read and parse the existing `.canvas` file
2. Generate a unique ID that does not collide with existing node or edge IDs
3. Choose position (`x`, `y`) that avoids overlapping existing nodes (leave 50-100px spacing)
4. Append the new node object to the `nodes` array
5. Optionally add edges connecting the new node to existing nodes
6. **Validate**: Confirm all IDs are unique and all edge references resolve to existing nodes

### 3. Connect Two Nodes

1. Identify the source and target node IDs
2. Generate a unique edge ID
3. Set `fromNode` and `toNode` to the source and target IDs
4. Optionally set `fromSide`/`toSide` (top, right, bottom, left) for anchor points
5. Optionally set `label` for descriptive text on the edge
6. Append the edge to the `edges` array
7. **Validate**: Confirm both `fromNode` and `toNode` reference existing node IDs

### 4. Edit an Existing Canvas

1. Read and parse the `.canvas` file as JSON
2. Locate the target node or edge by `id`
3. Modify the desired attributes (text, position, color, etc.)
4. Write the updated JSON back to the file
5. **Validate**: Re-check all ID uniqueness and edge reference integrity after editing

## Nodes

Nodes are objects placed on the canvas. Array order determines z-index: first node = bottom layer, last node = top layer.

### Generic Node Attributes

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
| `id` | Yes | string | Unique 16-char hex identifier |
| `type` | Yes | string | `text`, `file`, `link`, or `group` |
| `x` | Yes | integer | X position in pixels |
| `y` | Yes | integer | Y position in pixels |
| `width` | Yes | integer | Width in pixels |
| `height` | Yes | integer | Height in pixels |
| `color` | No | canvasColor | Preset `"1"`-`"6"` or hex (e.g., `"#FF0000"`) |

### Text Nodes

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
| `text` | Yes | string | Plain text with Markdown syntax |

```json
{
  "id": "6f0ad84f44ce9c17",
  "type": "text",
  "x": 0,
  "y": 0,
  "width": 400,
  "height": 200,
  "text": "# Hello World\n\nThis is **Markdown** content."
}
```

**Newline pitfall**: Use `\n` for line breaks in JSON strings. Do **not** use the literal `\\n` -- Obsidian renders that as the characters `\` and `n`.

### File Nodes

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
| `file` | Yes | string | Path to file within the system |
| `subpath` | No | string | Link to heading or block (starts with `#`) |

```json
{
  "id": "a1b2c3d4e5f67890",
  "type": "file",
  "x": 500,
  "y": 0,
  "width": 400,
  "height": 400,
  "file": "projects/notes.md"
}
```

### Link Nodes

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
| `url` | Yes | string | External URL |

```json
{
  "id": "1234567890abcdef",
  "type": "link",
  "x": 1000,
  "y": 0,
  "width": 300,
  "height": 150,
  "url": "https://example.com"
}
```

### Group Nodes

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
| `label` | No | string | Group label (top-left) |

```json
{
  "id": "fedcba0987654321",
  "type": "group",
  "x": -50,
  "y": -50,
  "width": 900,
  "height": 600,
  "label": "Project Overview"
}
```

## Edges

Edges connect nodes. Each edge has:

| Attribute | Required | Type | Description |
|-----------|----------|------|-------------|
| `id` | Yes | string | Unique 16-char hex identifier |
| `fromNode` | Yes | string | Source node ID |
| `toNode` | Yes | string | Target node ID |
| `fromSide` | No | string | `top`, `right`, `bottom`, `left` |
| `toSide` | No | string | `top`, `right`, `bottom`, `left` |
| `color` | No | canvasColor | Preset `"1"`-`"6"` or hex |
| `label` | No | string | Text displayed on the edge |

```json
{
  "id": "edge1234567890ab",
  "fromNode": "6f0ad84f44ce9c17",
  "toNode": "a1b2c3d4e5f67890",
  "fromSide": "right",
  "toSide": "left",
  "label": "references"
}
```

## Colors

Use preset numbers or custom hex colors:

| Preset | Color |
|--------|-------|
| `"1"` | Red |
| `"2"` | Orange |
| `"3"` | Yellow |
| `"4"` | Green |
| `"5"` | Cyan |
| `"6"` | Purple |

```json
{
  "color": "4"
}
```

```json
{
  "color": "#FF5733"
}
```

## Examples

### Simple Mind Map

```json
{
  "nodes": [
    {
      "id": "center0000000001",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 200,
      "height": 100,
      "text": "# Central Idea"
    },
    {
      "id": "branch1000000002",
      "type": "text",
      "x": 300,
      "y": -150,
      "width": 180,
      "height": 80,
      "text": "Branch 1"
    },
    {
      "id": "branch2000000003",
      "type": "text",
      "x": 300,
      "y": 150,
      "width": 180,
      "height": 80,
      "text": "Branch 2"
    }
  ],
  "edges": [
    {
      "id": "edge000000000004",
      "fromNode": "center0000000001",
      "toNode": "branch1000000002",
      "fromSide": "right",
      "toSide": "left"
    },
    {
      "id": "edge000000000005",
      "fromNode": "center0000000001",
      "toNode": "branch2000000003",
      "fromSide": "right",
      "toSide": "left"
    }
  ]
}
```

### Flowchart with Groups

```json
{
  "nodes": [
    {
      "id": "group00000000001",
      "type": "group",
      "x": -50,
      "y": -50,
      "width": 600,
      "height": 400,
      "label": "Process A"
    },
    {
      "id": "start00000000002",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 150,
      "height": 80,
      "text": "Start",
      "color": "4"
    },
    {
      "id": "step100000000003",
      "type": "text",
      "x": 250,
      "y": 0,
      "width": 150,
      "height": 80,
      "text": "Step 1"
    },
    {
      "id": "end0000000000004",
      "type": "text",
      "x": 500,
      "y": 0,
      "width": 150,
      "height": 80,
      "text": "End",
      "color": "1"
    }
  ],
  "edges": [
    {
      "id": "edge000000000006",
      "fromNode": "start00000000002",
      "toNode": "step100000000003",
      "fromSide": "right",
      "toSide": "left"
    },
    {
      "id": "edge000000000007",
      "fromNode": "step100000000003",
      "toNode": "end0000000000004",
      "fromSide": "right",
      "toSide": "left"
    }
  ]
}
```

## See Also

- [JSON Canvas Spec 1.0](https://jsoncanvas.org/spec/1.0/)
- [JSON Canvas GitHub](https://github.com/obsidianmd/jsoncanvas)
