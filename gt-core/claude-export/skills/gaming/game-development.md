# game-development

> General game development patterns, game loop, state management, physics, collision, animation, asset pipeline, performance optimization, and cross-platform considerations. Use when designing or reviewing game projects.

## Metadata

- **License:** MIT
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/gaming/game-development/SKILL.md`

## Skill Body

# Game Development

## Overview

General game development patterns applicable across engines and frameworks. This skill covers architecture, state management, physics, animation, asset pipelines, performance, and cross-platform considerations.

## Game Loop and State Management

- The game loop consists of: Input -> Update -> Render. Keep each stage deterministic and frame-rate independent where possible.
- Use `delta` time for all movement and animation calculations to ensure consistent behavior across frame rates.
- Separate game state from presentation. The simulation should be able to run without rendering.
- Use a finite state machine (FSM) or hierarchical state machine (HSM) for entity behavior and game flow.
- For complex AI, consider behavior trees or utility AI layered on top of an FSM.
- Use an event bus or observer pattern for decoupled communication between subsystems (UI, audio, gameplay).
- Save/load systems should serialize game state (not engine objects) to JSON, binary, or a custom format.

## Physics and Collision

- Choose the right physics body type for the use case: kinematic for player-controlled, dynamic/rigid for physics-driven, static for immovable world geometry.
- Use continuous collision detection (CCD) for fast-moving objects to prevent tunneling.
- Simplify collision shapes: use boxes/spheres/capsules instead of mesh colliders where possible.
- Use physics layers and masks to filter collisions and reduce unnecessary overlap checks.
- Process physics at a fixed timestep; decouple rendering frame rate from physics updates if the engine allows.
- Implement custom gravity or forces for game-feel tuning (e.g., coyote time, jump buffering).

## Animation

- Drive gameplay logic from animation states, not the other way around. Animation should reflect state.
- Use animation blending trees for smooth transitions between locomotion states.
- Trigger gameplay events (hitboxes, sound, particles) via animation events/notifies/keyframe callbacks.
- Use root motion for character movement when precise animation-driven positioning is required.
- Separate cosmetic animation from functional state to avoid desync bugs.

## Asset Pipeline

- Establish a naming convention and folder structure early and enforce it.
- Use source control for raw assets (PSD, Blender, audio) and a separate pipeline for engine-ready exports.
- Automate asset import settings where possible (texture compression, mesh LOD generation, audio format conversion).
- Use atlasing for 2D sprites to reduce draw calls; use texture arrays or streaming for large 3D worlds.
- Version your asset pipeline alongside your code to prevent breakages.
- Use placeholder assets (grayboxing) to prototype gameplay before final art passes.

## Performance Optimization

- Profile first, optimize second. Use built-in profilers to identify bottlenecks (CPU, GPU, memory).
- Object pooling: reuse bullets, enemies, particles, and UI elements instead of instantiating/destroying repeatedly.
- Level of Detail (LOD): use lower-poly meshes and lower-resolution textures for distant objects.
- Frustum and occlusion culling: do not render objects outside the camera view or hidden behind others.
- Batch draw calls by minimizing material/texture switches; use GPU instancing for repeated geometry.
- Optimize physics by reducing collision pairs, using simpler shapes, and sleeping inactive bodies.
- Use coroutines or async loading for level transitions and asset streaming to avoid hitches.
- Minimize garbage collection pressure in managed languages by pooling objects and avoiding per-frame allocations.

## Cross-Platform Considerations

- Abstract input handling: support keyboard, mouse, gamepad, and touch with a unified input mapping layer.
- Use relative coordinates and scalable UI layouts to handle different screen resolutions and aspect ratios.
- Test on target hardware early; desktop performance does not translate to mobile or console.
- Platform-specific code should live behind abstraction layers or conditional compilation.
- Handle save file paths, permissions, and cloud saves per platform requirements.
- For mobile: optimize for touch, consider battery/thermal throttling, and respect platform store guidelines.
- For web: minimize initial download size, be mindful of audio autoplay policies, and test on multiple browsers.

## Common Patterns

### Object Pool
```
Pool:
  - pre-allocate N objects at startup
  - borrow(): return active object or expand pool
  - return(obj): deactivate and push back to available list
  - reset(): clear all borrowed objects
```

### Game Manager / State Machine
```
GameManager:
  - current_state: Menu | Playing | Paused | GameOver
  - transition_to(new_state)
  - each state handles its own update/render/input
```

### Entity Component System (ECS) Lite
```
Entity:
  - unique id
  - list of Component references

Component:
  - data only (position, health, sprite)

System:
  - queries entities with specific components
  - runs update logic on matching entities
```

## Anti-Patterns to Avoid

- Putting all game logic in a single "God Object" or mega-script.
- Mixing presentation code with simulation code (e.g., spawning particles inside a physics calculation).
- Using string comparisons or magic numbers for state checks; use enums or typed state objects.
- Blocking the main thread during loading; use async/streaming approaches.
- Hardcoding resolution, input keys, or file paths; use configurable settings and abstraction layers.

## References

- Game Programming Patterns (Robert Nystrom): https://gameprogrammingpatterns.com/
- Game Engine Architecture (Jason Gregory)
- GDC Vault: https://gdcvault.com/
