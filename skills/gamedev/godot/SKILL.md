---
name: godot
description: Godot Engine 4.x patterns, GDScript best practices, node tree architecture, signals, scene composition, and export/deployment. Use when developing or reviewing Godot projects.
license: MIT
metadata:
  author: AI Skills
  version: "1.0"
---

# Godot Engine 4.x

## Overview

Godot 4.x is a free, open-source game engine with a node-based architecture. It uses GDScript (Python-like), C#, or C++ for scripting. This skill covers patterns, best practices, and architecture for Godot 4.x development.

## Node Tree Architecture

- Everything in Godot is a Node. Scenes are trees of nodes.
- The root node determines the scene type (e.g., Node2D, Node3D, Control).
- Use composition over inheritance: build complex objects by combining nodes rather than deep inheritance hierarchies.
- Keep scenes focused and reusable. A scene should represent a single logical entity.
- Use `get_node()` or `$` shorthand sparingly; prefer exported NodePath variables or `@onready` variables for maintainability.

## GDScript Best Practices

- Use static typing with `:` annotations and `->` return types for performance and clarity.
- Use `@onready var` to cache node references after the node enters the tree.
- Prefer `const` for immutable values, `enum` for state sets.
- Use `match` (pattern matching) for clean state machines and branching.
- Avoid tight coupling: communicate between nodes via signals, not direct method calls.
- Group related functionality into autoloads (singletons) only when truly global (e.g., GameState, AudioManager).
- Use `preload()` for scene/script resources at the top of files; use `load()` only for dynamic/runtime loading.
- Name signals in past tense (`health_changed`, `player_died`) to indicate events that already occurred.

## Signals and Callbacks

- Signals are Godot’s decoupled event system. Emitters do not need to know about receivers.
- Connect signals in `_ready()` or via the editor. Use `Callable` for dynamic connections.
- Disconnect signals when nodes are removed to prevent dangling references.
- Use `await` (GDScript 2.0) for one-shot async operations instead of manual signal connection/disconnection.
- Group related signals on a common parent or use an autoload event bus for cross-scene communication.

## Scene Composition

- Break levels and UI into reusable sub-scenes.
- Use instancing (PackedScene) for repeated elements (enemies, items, UI panels).
- Leverage `Editable Children` only when necessary; prefer exposing parameters via exported variables.
- Use `CanvasLayer` for UI that must render independently of the world camera.
- Use `ParallaxBackground` / `ParallaxLayer` for 2D background scrolling.
- For 3D, use `WorldEnvironment` and `Camera3D` nodes to control rendering and view.

## Physics and Collision

- Use `Area2D` / `Area3D` for trigger zones and `CharacterBody2D` / `CharacterBody3D` for player/NPC movement.
- Use `RigidBody2D` / `RigidBody3D` for physics-driven objects.
- Process physics in `_physics_process(delta)`, not `_process(delta)`.
- Use collision layers and masks to organize what collides with what. Document your layer assignments.
- Use `move_and_slide()` for `CharacterBody` nodes; it handles floor snapping and sliding automatically.

## Animation

- Use `AnimationPlayer` for any property animation (position, rotation, modulate, even function calls).
- Use `AnimationTree` for state-machine-driven animation blending (especially in 3D).
- Prefer blending animations via `BlendSpace1D` / `BlendSpace2D` for locomotion.
- Trigger gameplay events from animation keyframes using `call_method` tracks.

## Performance Optimization

- Use `VisibleOnScreenNotifier2D/3D` to pause processing for off-screen objects.
- Use `OccluderInstance3D` and occlusion culling in 3D scenes.
- Limit the number of simultaneous `RigidBody` objects; use sleeping when possible.
- Batch draw calls by reusing materials and textures.
- Use `MultiMeshInstance2D/3D` for large numbers of identical meshes.
- Profile with Godot’s built-in Profiler and Debugger monitors.

## Export and Deployment

- Use `Project > Export` to configure target platforms (Windows, macOS, Linux, Web, Android, iOS, consoles).
- For Web export, use the Godot 4.3+ web export with threads disabled for broader compatibility.
- Use `Export Presets` to manage platform-specific settings and custom build templates.
- Strip debug symbols and compress textures for release builds.
- Use `ResourceLoader` threading for large scene transitions to avoid frame drops.

## Common Patterns

### State Machine (Finite State Machine)
```gdscript
class_name StateMachine
extends Node

@export var initial_state: State
var current_state: State
var states: Dictionary = {}

func _ready():
    for child in get_children():
        if child is State:
            states[child.name.to_lower()] = child
            child.transitioned.connect(_on_transition)
    if initial_state:
        initial_state.enter()
        current_state = initial_state

func _physics_process(delta):
    if current_state:
        current_state.physics_update(delta)

func _on_transition(new_state_name: String):
    var new_state = states.get(new_state_name.to_lower())
    if new_state and new_state != current_state:
        current_state.exit()
        new_state.enter()
        current_state = new_state
```

### Autoload (Singleton) Pattern
```gdscript
# GameState.gd (added to Project > Autoload)
extends Node

signal score_changed(new_score: int)
var score: int = 0:
    set(value):
        score = value
        score_changed.emit(score)
```

## Anti-Patterns to Avoid

- Calling `get_tree().change_scene_to_file()` from deep inside gameplay logic; use an autoload scene manager instead.
- Using `_process` for physics or input handling; use `_physics_process` and `_unhandled_input`.
- Deep node paths like `$"../../Some/Deep/Node"`; refactor to use signals or exported references.
- Overusing autoloads for data that should be scoped to a scene or object.

## References

- Godot Docs: https://docs.godotengine.org/
- GDScript Reference: https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_basics.html
- Godot Best Practices: https://docs.godotengine.org/en/stable/tutorials/best_practices/index.html
