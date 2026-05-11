# mobile-ui

> Mobile UI design patterns, iOS Human Interface Guidelines, responsive design, touch targets, gestures, accessibility, and SwiftUI component best practices.

## Metadata

- **Version:** 1.0.0
- **Author:** Hermes Agent
- **License:** MIT
- **Tags:** iOS, SwiftUI, UI, mobile, HIG, accessibility, design, touch
- **Related Skills:** swiftui-pro, swiftui-expert-skill, hig-foundations, hig-patterns
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/ios-development/mobile-ui/SKILL.md`

## Skill Body

# Mobile UI

Design and build mobile interfaces that follow Apple's Human Interface Guidelines, respect platform conventions, and work beautifully on all device sizes. This skill covers design patterns, responsive layout, touch interaction, accessibility, and SwiftUI best practices for mobile.

## When to Use This Skill

- Building or reviewing iOS/iPadOS app interfaces
- Adapting a design for mobile from desktop/web
- Adding accessibility support to existing UI
- Choosing between UI patterns (sheets, alerts, navigation)
- Reviewing touch target sizes and gesture handling
- Ensuring responsive layout across iPhone sizes and iPad multitasking

## iOS Human Interface Guidelines (HIG) — Core Principles

### Clarity

- Use legible text at all Dynamic Type sizes
- Provide enough contrast (minimum 4.5:1 for normal text, 3:1 for large text)
- Avoid clutter — one primary action per screen
- Use standard terminology, not jargon

### Deference

- Content is king — UI chrome should not compete
- Use translucent materials (`.ultraThinMaterial`) to let wallpaper peek through
- Minimize use of heavy borders and separators
- Let gestures and animations feel physical and responsive

### Depth

- Use layers and motion to communicate hierarchy
- Sheets slide up for modal tasks, push navigation for drill-down
- Context menus reveal actions without leaving the current screen
- Tab bars provide persistent top-level navigation

## Responsive Design for Mobile

### Device Size Classes

SwiftUI uses size classes and geometry to adapt:

```swift
@Environment(\.horizontalSizeClass) var horizontalSizeClass
@Environment(\.verticalSizeClass) var verticalSizeClass

// Compact = iPhone portrait, iPad Slide Over
// Regular = iPhone landscape (Plus/Max), iPad full screen
```

### Layout adaptation patterns

| Pattern | Use When |
|---------|----------|
| `VStack` / `HStack` with conditional | Simple adaptive layouts |
| `NavigationSplitView` | iPad master-detail, iPhone stack fallback |
| `UIScene` / multi-window | iPad multitasking, Stage Manager |
| `GeometryReader` | Precise proportional sizing |
| `ViewThatFits` | iOS 17+ — pick the view that fits the space |

### Safe areas and margins

```swift
// Respect safe areas (notch, home indicator, Dynamic Island)
.contentMargins(.horizontal, 16, for: .scrollContent)

// Or explicitly ignore for full-bleed backgrounds
.ignoresSafeArea(.container, edges: .top)
```

### Dynamic Type

```swift
// Use text styles, not fixed sizes
Text("Title").font(.headline)
Text("Body").font(.body)

// Custom font with dynamic scaling
Text("Custom").font(.custom("Inter", size: 17, relativeTo: .body))

// Check if larger accessibility sizes are active
@Environment(\.dynamicTypeSize) var dynamicTypeSize
```

## Touch Targets and Gestures

### Minimum touch target

- **44×44 points** is the absolute minimum
- **48×48 points** preferred for primary actions
- Pad tappable areas visually if the icon is smaller

```swift
// Bad: 24×24 button
Image(systemName: "heart")
    .onTapGesture { ... }

// Good: 44×44 tappable area
Button(action: { ... }) {
    Image(systemName: "heart")
        .frame(minWidth: 44, minHeight: 44)
        .contentShape(Rectangle())
}
```

### Gesture hierarchy

| Gesture | Priority | Use For |
|---------|----------|---------|
| Tap | Highest | Buttons, selection, navigation |
| Long press | Medium | Context menus, peek, secondary actions |
| Swipe | Medium | Delete, archive, navigate between items |
| Pan / drag | Lower | Reordering, drawing, maps |
| Pinch | Lowest | Zoom, resize |

### Gesture best practices

- Do not put conflicting gestures on the same element
- Provide visual feedback during gestures (opacity, scale, haptics)
- Use `.simultaneousGesture` only when truly needed
- Support system gestures (back swipe, pull-to-refresh) rather than overriding them

## SwiftUI UI Components — Best Practices

### Buttons

```swift
// Use the new initializer for icon + label
Button("Add to Favorites", systemImage: "heart") {
    addToFavorites()
}

// Primary action style
Button("Save") { ... }
    .buttonStyle(.borderedProminent)

// Destructive action
Button("Delete", role: .destructive) { ... }
```

### Lists

```swift
// Use .swipeActions for quick actions
List {
    ForEach(items) { item in
        ItemRow(item)
            .swipeActions {
                Button("Delete", role: .destructive) { delete(item) }
                Button("Pin") { pin(item) }
            }
    }
}

// Use .listRowSpacing and .listRowSeparator for fine control
.listRowSpacing(8)
```

### Sheets and presentations

```swift
// Prefer sheets for modal tasks
.sheet(isPresented: $showEditor) {
    EditorView()
}

// Use .presentationDetents for resizable sheets
.sheet(isPresented: $showDetails) {
    DetailView()
        .presentationDetents([.medium, .large])
}

// Full screen cover for immersive experiences
.fullScreenCover(isPresented: $showCamera) {
    CameraView()
}
```

### Navigation

```swift
// NavigationStack for iOS 16+
NavigationStack {
    List(destinations) { destination in
        NavigationLink(destination.name, value: destination)
    }
    .navigationDestination(for: Destination.self) { destination in
        DestinationDetail(destination)
    }
}

// NavigationSplitView for iPad / macOS
NavigationSplitView {
    SidebarView()
} content: {
    ContentListView()
} detail: {
    DetailView()
}
```

### Alerts and confirmation dialogs

```swift
// Alert for critical decisions
.alert("Delete Account?", isPresented: $showDeleteAlert) {
    Button("Cancel", role: .cancel) { }
    Button("Delete", role: .destructive) { deleteAccount() }
} message: {
    Text("This action cannot be undone.")
}

// ConfirmationDialog for multiple choices
.confirmationDialog("Sort By", isPresented: $showSortOptions) {
    Button("Date") { sortByDate() }
    Button("Name") { sortByName() }
    Button("Cancel", role: .cancel) { }
}
```

## Accessibility

### Minimum viable accessibility

```swift
// Every interactive element must have a label
Button("Send Message", systemImage: "paperplane") { ... }

// If using a custom tap area, add an accessibility label
Image(decorative: "hero-banner")
    .accessibilityLabel("Summer sale banner")
    .accessibilityHint("Double-tap to view deals")

// Group related elements
VStack {
    Text("Temperature")
    Text("72°")
}
.accessibilityElement(children: .combine)
.accessibilityLabel("Temperature, 72 degrees")
```

### Dynamic Type support

```swift
// Test at AX5 size in Simulator
// Use scalable images
Image(systemName: "gear")
    .imageScale(.large)

// Avoid fixed frame heights that clip text
Text("Long description here")
    .fixedSize(horizontal: false, vertical: true)
```

### VoiceOver

```swift
// Hide decorative elements
Image("background-pattern")
    .accessibilityHidden(true)

// Adjust sort order
HStack {
    Text("Name")
    Text("Status")
}
.accessibilitySortPriority(1) // Read "Name" first
```

### Reduce Motion

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

// Skip heavy animations when user prefers reduced motion
if !reduceMotion {
    withAnimation(.spring()) {
        isExpanded.toggle()
    }
} else {
    isExpanded.toggle()
}
```

## Platform-Specific Patterns

### iPhone

- Single column, stack-based navigation
- Tab bar for top-level sections
- Bottom sheets for secondary tasks
- Pull-to-refresh in lists

### iPad

- Multi-column layouts with `NavigationSplitView`
- Popovers instead of full-screen sheets for selections
- Support for multitasking (Slide Over, Split View, Stage Manager)
- Hover effects for pointer interaction

### macOS (Mac Catalyst / native)

- Toolbar-based navigation
- Menu bar commands
- Keyboard shortcuts
- Pointer-precision interactions (smaller targets acceptable)

## Dark Mode

```swift
// Use semantic colors, never hardcoded hex
.background(Color(.systemBackground))
.foregroundStyle(Color(.label))

// Custom colors that adapt
@Environment(\.colorScheme) var colorScheme

// Or define asset catalog colors with Light/Dark variants
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Fixed font sizes | Use `.font(.body)` etc. |
| 24×24 tap targets | Enlarge to 44×44 minimum |
| Ignoring safe areas | Use `.safeAreaInset` or respect defaults |
| No accessibility labels | Add `.accessibilityLabel` to every interactive element |
| Hardcoded frames | Use `GeometryReader`, `ViewThatFits`, or stacks |
| Overriding system gestures | Support back swipe, pull-to-refresh natively |
| No empty states | Show placeholder when list is empty |
| No loading states | Use `ProgressView` or skeleton placeholders |
| No error states | Show friendly error UI, not raw alerts |

## Quick Reference

```swift
// Adaptive layout
@Environment(\.horizontalSizeClass) var hSizeClass
@Environment(\.dynamicTypeSize) var dynamicTypeSize

// Touch target
.frame(minWidth: 44, minHeight: 44)
.contentShape(Rectangle())

// Accessibility
.accessibilityLabel("Description")
.accessibilityHint("Double-tap to activate")
.accessibilityHidden(true)

// Dark mode safe
.background(Color(.systemBackground))
.foregroundStyle(Color(.label))
```

## Summary

1. **Follow HIG** — clarity, deference, depth
2. **44×44 minimum touch targets** — pad small icons
3. **Support Dynamic Type** — never use fixed font sizes
4. **Label everything for VoiceOver** — every interactive element
5. **Respect safe areas** — design for notches, home indicators, Dynamic Island
6. **Use semantic colors** — automatic dark mode support
7. **Test on real devices** — Simulator misses touch feel and performance
8. **Test accessibility sizes** — AX5 in Simulator reveals layout bugs
