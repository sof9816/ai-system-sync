# obsidian-cli

> Interact with Obsidian vaults using the Obsidian CLI to read, create, search, and manage notes, tasks, properties, and more. Also supports plugin and theme development with commands to reload plugins, run JavaScript, capture errors, take screenshots, and inspect the DOM. Use when the user asks to interact with their Obsidian vault, manage notes, search vault content, perform vault operations from the command line, or develop and debug Obsidian plugins and themes.

## Metadata

- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/note-taking/obsidian-cli/SKILL.md`

## Skill Body

# Obsidian CLI

Use the `obsidian` CLI to interact with a running Obsidian instance. Requires Obsidian to be open.

## Command reference

Run `obsidian help` to see all available commands. This is always up to date. Full docs: https://help.obsidian.md/cli

## Syntax

**Parameters** take a value with `=`. Quote values with spaces:

```bash
obsidian create name="My Note" content="Hello world"
```

**Flags** are boolean switches with no value:

```bash
obsidian create name="My Note" silent overwrite
```

For multiline content use `\n` for newline and `\t` for tab.

## File targeting

Many commands accept `file` or `path` to target a file. Without either, the active file is used.

- `file=<name>` — resolves like a wikilink (name only, no path or extension needed)
- `path=<path>` — exact path from vault root, e.g. `folder/note.md`

## Vault targeting

Commands target the most recently focused vault by default. Use `vault=<name>` as the first parameter to target a specific vault:

```bash
obsidian vault="My Vault" search query="test"
```

## Common patterns

```bash
obsidian read file="My Note"
obsidian create name="New Note" content="# Hello" template="Template" silent
obsidian append file="My Note" content="New line"
obsidian search query="search term" limit=10
obsidian daily:read
obsidian daily:append content="- [ ] New task"
obsidian property:set name="status" value="done" file="My Note"
obsidian tasks daily todo
obsidian tags sort=count counts
obsidian backlinks file="My Note"
```

Use `--copy` on any command to copy output to clipboard. Use `silent` to prevent files from opening. Use `total` on list commands to get a count.

## Plugin development

### Develop/test cycle

After making code changes to a plugin or theme, follow this workflow:

1. **Reload** the plugin to pick up changes:
   ```bash
   obsidian plugin:reload id=my-plugin
   ```
2. **Check for errors** — if errors appear, fix and repeat from step 1:
   ```bash
   obsidian dev:errors
   ```
3. **Verify visually** with a screenshot or DOM inspection:
   ```bash
   obsidian dev:screenshot path=screenshot.png
   obsidian dev:dom selector=".workspace-leaf" text
   ```
4. **Check console output** for warnings or unexpected logs:
   ```bash
   obsidian dev:console level=error
   ```

### Additional developer commands

Run JavaScript in the app context:

```bash
obsidian eval code="app.vault.getFiles().length"
```

Inspect CSS values:

```bash
obsidian dev:css selector=".workspace-leaf" prop=background-color
```

Toggle mobile emulation:

```bash
obsidian dev:mobile
```

### Theme development

```bash
obsidian theme:reload
obsidian dev:css selector=".workspace-leaf" prop=background-color
```

## Note management

### Create notes

```bash
obsidian create name="My Note" content="# Hello World"
obsidian create name="My Note" template="Daily Note" silent
obsidian create name="My Note" content="Text" path="folder/note.md"
```

### Read notes

```bash
obsidian read file="My Note"
obsidian read path="folder/note.md"
obsidian read file="My Note" --copy
```

### Update notes

```bash
obsidian append file="My Note" content="New line"
obsidian prepend file="My Note" content="Header"
obsidian replace file="My Note" content="Old text" replacement="New text"
obsidian property:set name="status" value="done" file="My Note"
obsidian property:remove name="status" file="My Note"
```

### Delete notes

```bash
obsidian delete file="My Note"
obsidian delete path="folder/note.md" force
```

## Search and query

```bash
obsidian search query="search term"
obsidian search query="term" limit=10
obsidian search query="term" path="folder/"
obsidian backlinks file="My Note"
obsidian outgoing file="My Note"
```

## Daily notes

```bash
obsidian daily:read
obsidian daily:append content="- [ ] Task"
obsidian daily:prepend content="# Morning"
```

## Tasks

```bash
obsidian tasks daily todo
obsidian tasks daily done
obsidian tasks file="My Note" todo
obsidian tasks file="My Note" done
```

## Tags

```bash
obsidian tags
obsidian tags sort=count
obsidian tags counts
```

## Graph view

```bash
obsidian graph depth=2 file="My Note"
obsidian graph depth=3 limit=50
```

## See Also

- [Obsidian CLI Documentation](https://help.obsidian.md/cli)
- [Plugin Development](https://docs.obsidian.md/Plugins/Getting+started)
- [Theme Development](https://docs.obsidian.md/Themes/App+themes)
