# frontend-developer

> >

## Metadata

- **Version:** 1.0.0
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/software-development/frontend-developer/SKILL.md`

## Skill Body

# Frontend Developer Skill

## Tech Stack
- **Framework**: React 18+ with hooks, concurrent features, Suspense
- **Language**: TypeScript (strict mode, no any)
- **Styling**: Tailwind CSS v3+ with custom design tokens
- **Build**: Vite (fast HMR, optimized builds)
- **State**: Zustand or React Query (avoid Redux unless complex)
- **Animation**: Framer Motion for transitions, CSS for simple
- **Icons**: Lucide React (consistent, lightweight)
- **Charts**: Recharts or Chart.js

## Code Patterns

### Component Structure
```tsx
// Atomic: single responsibility, typed props
interface CardProps {
  title: string;
  value: number;
  trend?: "up" | "down" | "neutral";
  onClick?: () => void;
}

export const MetricCard = ({ title, value, trend, onClick }: CardProps) => {
  return (
    <div 
      className="rounded-xl bg-slate-800/50 border border-slate-700 p-4 
                 hover:border-cyan-500/50 transition-all cursor-pointer"
      onClick={onClick}
    >
      <h3 className="text-slate-400 text-sm">{title}</h3>
      <p className="text-2xl font-bold text-white">{value.toLocaleString()}</p>
      {trend && <TrendBadge trend={trend} />}
    </div>
  );
};
```

### Tailwind Custom Theme
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#f0f9ff",
          500: "#06b6d4", // cyan
          900: "#164e63",
        },
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          800: "#1e293b",
          900: "#0f172a",
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['"Inter"', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(6, 182, 212, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(6, 182, 212, 0.8), 0 0 40px rgba(6, 182, 212, 0.4)' },
        }
      }
    }
  }
}
```

### Animation Patterns
```tsx
// Fade in on mount
const fadeIn = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.3 }
};

// Stagger children
const stagger = {
  animate: { transition: { staggerChildren: 0.1 } }
};

// Glow effect for active elements
const glowClass = "animate-glow border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.3)]";
```

## Performance Rules
- Use `React.memo` for expensive renders
- Lazy load routes with `React.lazy()`
- Use `useMemo`/`useCallback` for computed values and callbacks
- Images: WebP format, lazy loading, proper sizing
- Avoid layout thrashing (read then write DOM)

## Accessibility
- All interactive elements keyboard accessible
- ARIA labels for icons and non-text elements
- Color contrast ratio >= 4.5:1
- Respect `prefers-reduced-motion`

## File Organization
```
src/
  components/       # Reusable UI components
    ui/             # Primitive components (Button, Input, Card)
    layout/         # Layout components (Sidebar, Header, Grid)
    data/           # Data display (Table, Chart, Metric)
  pages/            # Route-level components
  hooks/            # Custom React hooks
  stores/           # Zustand state stores
  api/              # API client and queries
  types/            # Global TypeScript types
  utils/            # Helper functions
  styles/           # Global CSS, Tailwind imports
```

## Dashboard-Specific Patterns
- Real-time data: WebSocket or polling with React Query
- Status indicators: Color + icon + pulse animation
- Command palette: Cmd+K search with fuzzy matching
- Notifications: Toast system with auto-dismiss
- Dark mode default: Sci-fi/dashboard aesthetic

## Anti-Patterns (Don't)
- Don't use inline styles for dynamic values (use Tailwind arbitrary values)
- Don't put business logic in components (use hooks/stores)
- Don't use `any` type (use `unknown` with type guards)
- Don't import entire libraries (tree-shake with named imports)
- Don't use CSS-in-JS (Tailwind is faster, no runtime cost)
