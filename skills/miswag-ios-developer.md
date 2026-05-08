---
name: miswag-ios-developer
description: Senior iOS Development rules, guidelines, and project architecture specifically for the Miswag iOS project. Use this skill WHENEVER working on any feature, bug fix, or refactor in this repository.
---

# Miswag iOS Developer Guidelines

You are an elite Senior iOS Engineer working on the `miswag-ios` application. Follow these project-specific principles stringently.

---

## 🏗️ Project Architecture & Submodules

The app is highly modularized — 37 Git submodules plus the main `Miswag/` target.

**Key submodules:**
- `MiswagCore` — Base `MGViewController`, `performAction(_:with:)` engine
- `MiswagCoreModels` — Shared models: `ActionResult`, `GenericResult`, `InfoWrappedResult`
- `MiswagUI` — Design tokens, reusable UI components
- `CoreAPI` — Networking; always use `Network.decoder()` for JSON decoding
- `BlocksParser` — Server-driven UI: `BlockResultTranslater`, `BlocksController`, `BlocksPresenter`
- `AppRoute` — Route definitions, routing abstractions
- `Analytics` — `MGAnalytics` tracking; identity/alias in `MGAnalytics+Identity.swift`

**Rules:**
- Always be aware of which module you are working in
- Never create circular dependencies between submodules
- Before adding any library, check existing submodule dependencies to avoid duplication

---

## 📁 File Organization

**CRITICAL: Never suppress `file_length` violations with `// swiftlint:disable file_length`.**

Instead, split the file into focused extension files:
- Pattern: `TypeName+Feature.swift` in the same directory as the main file
- Examples: `HomeViewController+NavigationBar.swift`, `MGAnalytics+Identity.swift`
- Stored properties and `deinit` MUST stay in the main class declaration (not extensions)
- Methods called from other files must use `internal` access (no `private` keyword)
- Methods only called within their own file/extension can stay `private`
- Each extension file should have one clear responsibility

**When you split a file, you MUST also add the new files to `Miswag.xcodeproj/project.pbxproj`.** Each new Swift file needs 4 entries:
1. `PBXFileReference` — declares the file
2. `PBXBuildFile` — marks it for compilation
3. `PBXGroup` — places it in the right folder group
4. `PBXSourcesBuildPhase` — adds it to the target's compile sources

Verify with: `grep -c "NewFileName" Miswag.xcodeproj/project.pbxproj` — should return ≥ 4.

---

## 🧩 Block System (BlocksParser)

### Translation Pipeline

```
Server JSON → [BlockResult] (Codable) → BlockResultTranslater → [BlockSection] → UICollectionView
```

### BlockResultTranslater Registry Pattern

`translate()` uses a `[BlockType: BlockFactory]` dictionary instead of a switch:

```swift
public func translate(result: BlockResult, ...) -> BlockSection? {
    let context = BlockTranslationContext(loader: loader, background: background,
                                          extra: extra, isNestedBlock: isNestedBlock)
    guard let factory = Self.registry[result.blockType] else { return nil }
    return factory(result, context)
}
```

`BlockTranslationContext` carries extra-JSON data: `loader`, `background`, `extra`, `isNestedBlock`.

### Adding a New Block Type

When the server introduces a new block type, update ALL of these in order:
1. `BlockType` enum in `BlockResult.swift` — add the raw string case
2. `BlockResult` enum in `BlockResult.swift` — add the associated value case
3. `BlockResult.init(from:)` — add decoding case
4. `BlockResult.encode(to:)` — add encoding case
5. `BlockResult.blockType` computed property — add mapping
6. `BlockResultTranslater.buildRegistry()` — add factory to the appropriate `addXxxFactories` sub-function (each sub-function must stay under cyclomatic complexity 10)
7. Create `BLXxxBlockResult` typealias, `Block` enum case, and `XxxBlockModel` class

**See:** `docs/architecture_and_ui/BLOCK_RESULT_TRANSLATER.md` for full details.

### blockType Property

`BlockResult` and `BlockType` have some mismatched names (historical). The `.blockType` computed property handles the mapping:
- `.girdProducts` → `.gridProducts` (typo in BlockResult)
- `.category` → `.breadcrumb`
- `.productGroup` → `.productsGroup`
- `.markdownSpecs` → `.markSpecBlock`

---

## 🧠 Memory Management (ARC)

- **Closures**: Use `[weak self]` in ALL async blocks, API callbacks, delegates, and escaping closures
- **Delegates**: All delegate protocols must bind to `AnyObject`; delegate properties must be `weak var`
- **Tests**: Verify memory deallocation in tests when fixing leaks (set `sut = nil` in tearDown, assert weakRef is nil)

---

## 🔄 Networking & API

- **JSON Decoding**: Always use `Network.decoder()` from `CoreAPI` — never `JSONDecoder()` directly
- **Response types**: Always use `GenericResult`, `InfoWrappedResult`, or `ActionResult` for API responses — never raw model types
- **Error handling**: Report non-user errors to Sentry; filter expected/noisy errors (see `AppDelegate-Sentry.swift`)

---

## ✨ UI & Styling

- Strictly use design tokens — never hardcode colors, fonts, or corner radii
- Use `MiswagUI` components and `MiswagCore` utilities
- All VCs inherit from `MGViewController`; navigation goes through `Router.swift`

---

## 🔍 Code Quality & Linting

- Run `swiftlint lint --strict` before every commit — must be 0 violations
- Use `swiftlint --fix` to auto-correct what it can, then review
- **Never use `// swiftlint:disable`** for structural violations (file_length, type_body_length, cyclomatic_complexity) — fix the code instead
- For cyclomatic_complexity: extract switch cases into private methods or registry factories
- Pre-commit hooks enforce SwiftLint — fix violations before committing

---

## ✅ Definition of Done (REQUIRED before every commit)

Before committing ANY change, you MUST complete ALL of the following:

### 1. Add new files to Xcode project
New Swift files must be in `Miswag.xcodeproj/project.pbxproj` with 4 entries each.

### 2. SwiftLint clean
```bash
swiftlint lint --strict   # Must show: 0 violations, 0 serious
```

### 3. Unit tests
- Check `MiswagTests/UnitTests/` for the relevant category
- Write tests for new logic; update tests for changed logic
- Verify memory deallocation when fixing leaks
- Reference: `docs/testing_and_quality/TESTING_GUIDE.md`

### 4. Documentation
- Bug fixes → `docs/testing_and_quality/BUG_FIXES_AND_MITIGATIONS.md`
- New features → create or update the relevant doc in `docs/`
- New block types → update `docs/architecture_and_ui/BLOCK_RESULT_TRANSLATER.md`

### 5. Commit with meaningful message
Follow the project's commit convention: `type(scope): description`

---

## 🚀 Senior Level Mindset

- **Root cause first**: Reproduce the bug in a test before writing a fix
- **Kaizen**: Leave code cleaner than you found it (remove force-unwraps, fix naming)
- **Defensive programming**: Use `guard let` for early exits; avoid deeply nested `if let`
- **No half-measures**: If splitting a file, do it properly with all 4 pbxproj entries
