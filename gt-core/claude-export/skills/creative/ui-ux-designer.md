# ui-ux-designer

> >

## Metadata

- **Version:** 1.0.0
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/creative/ui-ux-designer/SKILL.md`

## Skill Body

# UI/UX Designer Skill

## Design Philosophy
- **Sci-fi aesthetic**: Dark backgrounds, neon accents, holographic elements
- **Information density**: High data density without clutter
- **Motion tells story**: Animations guide attention and show state changes
- **Tactile feedback**: Every interaction has visual/audio response
- **Hierarchy through light**: Brighter = more important, dimmer = background

## Color Systems

### Jarvis/Cyberpunk Palette
```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0f1c;      /* Deep space blue-black */
  --bg-secondary: #111827;    /* Slate 900 */
  --bg-tertiary: #1e293b;     /* Slate 800 */
  
  /* Accents */
  --accent-cyan: #06b6d4;      /* Primary action */
  --accent-blue: #3b82f6;       /* Secondary */
  --accent-purple: #8b5cf6;     /* Tertiary */
  --accent-green: #10b981;      /* Success */
  --accent-red: #ef4444;        /* Error */
  --accent-amber: #f59e0b;      /* Warning */
  
  /* Text */
  --text-primary: #f8fafc;      /* White-ish */
  --text-secondary: #94a3b8;    /* Muted */
  --text-dim: #475569;          /* Very muted */
  
  /* Glows */
  --glow-cyan: 0 0 10px rgba(6, 182, 212, 0.5);
  --glow-blue: 0 0 15px rgba(59, 130, 246, 0.4);
  --glow-purple: 0 0 20px rgba(139, 92, 246, 0.3);
}
```

### Usage Rules
- Primary actions: Cyan glow
- Active/selected: Blue glow + border
- Success states: Green pulse
- Alerts: Red with shake animation
- Background data: Dimmed, no glow

## Component Patterns

### HUD Panel
```tsx
const HUDPanel = ({ title, children, active = false }) => (
  <div className={`
    relative rounded-lg border p-4
    ${active 
      ? 'border-cyan-500/50 bg-slate-800/80 shadow-[0_0_20px_rgba(6,182,212,0.15)]' 
      : 'border-slate-700/50 bg-slate-900/50'}
    transition-all duration-300
  `}>
    {/* Corner accents */}
    <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-cyan-500/50" />
    <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-cyan-500/50" />
    <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-cyan-500/50" />
    <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-cyan-500/50" />
    
    {/* Header */}
    <div className="flex items-center gap-2 mb-3">
      <div className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`} />
      <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">{title}</span>
    </div>
    
    {children}
  </div>
);
```

### Data Stream (Terminal Effect)
```tsx
const DataStream = ({ lines }) => (
  <div className="font-mono text-xs text-cyan-400/80 space-y-1">
    {lines.map((line, i) => (
      <div key={i} className="flex gap-2">
        <span className="text-slate-600">{new Date().toLocaleTimeString()}</span>
        <span className={`
          ${line.type === 'error' ? 'text-red-400' : ''}
          ${line.type === 'success' ? 'text-green-400' : ''}
        `}>
          {line.text}
        </span>
      </div>
    ))}
  </div>
);
```

### Circular Progress (Radar Style)
```tsx
const CircularProgress = ({ value, label }) => (
  <div className="relative w-24 h-24">
    <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="45" fill="none" stroke="#1e293b" strokeWidth="8" />
      <circle 
        cx="50" cy="50" r="45" fill="none" stroke="#06b6d4" strokeWidth="8"
        strokeDasharray={`${value * 2.83} 283`}
        strokeLinecap="round"
        className="transition-all duration-1000"
        filter="url(#glow)"
      />
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
    </svg>
    <div className="absolute inset-0 flex flex-col items-center justify-center">
      <span className="text-lg font-bold text-white">{value}%</span>
      <span className="text-[10px] text-slate-500 uppercase">{label}</span>
    </div>
  </div>
);
```

## Animation Patterns

### Scan Line
```css
.scan-line {
  position: relative;
  overflow: hidden;
}
.scan-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(6,182,212,0.5), transparent);
  animation: scan 3s linear infinite;
}
@keyframes scan {
  0% { transform: translateY(0); }
  100% { transform: translateY(100vh); }
}
```

### Glitch Text
```css
.glitch {
  position: relative;
  animation: glitch-skew 3s infinite;
}
.glitch::before,
.glitch::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}
.glitch::before {
  left: 2px;
  text-shadow: -2px 0 #ff00c1;
  clip: rect(44px, 450px, 56px, 0);
  animation: glitch-anim 5s infinite linear alternate-reverse;
}
.glitch::after {
  left: -2px;
  text-shadow: -2px 0 #00fff9;
  clip: rect(44px, 450px, 56px, 0);
  animation: glitch-anim2 5s infinite linear alternate-reverse;
}
```

### Breathing Glow
```css
.breathe {
  animation: breathe 4s ease-in-out infinite;
}
@keyframes breathe {
  0%, 100% { opacity: 0.6; filter: drop-shadow(0 0 5px rgba(6,182,212,0.3)); }
  50% { opacity: 1; filter: drop-shadow(0 0 15px rgba(6,182,212,0.6)); }
}
```

## Layout Patterns

### Command Center Grid
```
+--------------------------------------------------+
|  HEADER (status, time, alerts)                    |
+----------+---------------------------------------+
|          |                                       |
| SIDEBAR  |    MAIN CONTENT AREA                  |
| (nav)    |    (adaptive grid of panels)          |
|          |                                       |
+----------+---------------------------------------+
|  FOOTER (system stats, version)                   |
+--------------------------------------------------+
```

### Panel Hierarchy
1. **Critical alerts**: Top bar, pulsing red, always visible
2. **Primary metrics**: Top row, large numbers, cyan glow
3. **Secondary data**: Middle, charts and tables
4. **System status**: Bottom, small text, dimmed
5. **Navigation**: Left sidebar, icons + labels

## Typography
- **Headings**: Inter, bold, tracking-tight
- **Data/Numbers**: JetBrains Mono, tabular-nums
- **Labels**: Inter, uppercase, tracking-widest, text-xs
- **Body**: Inter, normal, leading-relaxed

## Iconography
- Use **Lucide React** icons
- Style: thin stroke (1.5px), geometric
- Color: inherit from parent (cyan for active, slate for inactive)
- Size: 16px for inline, 20px for buttons, 24px for nav

## Responsive Behavior
- **Desktop (>1280px)**: Full sidebar, 3-column grid
- **Tablet (768-1280px)**: Collapsed sidebar, 2-column grid
- **Mobile (<768px)**: Bottom nav, single column, cards stack

## Accessibility in Sci-Fi UI
- All glow effects respect `prefers-reduced-motion`
- Text remains readable without glow (fallback colors)
- Interactive elements have focus rings (cyan dashed)
- Color is never sole indicator (icons + text + patterns)

## Tools
- **Figma**: Primary design tool
- **Tailwind**: Implementation
- **Framer Motion**: Complex animations
- **CSS**: Simple animations (better performance)
