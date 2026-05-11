# dashboard-architect

> >

## Metadata

- **Version:** 1.0.0
- **Source:** `/Users/gt/Public/MyFiles/agent-home/gt-core/skills-repo/software-development/dashboard-architect/SKILL.md`

## Skill Body

# Dashboard Architect Skill

## Dashboard Types

### System Control Panel (GT Center)
- **Purpose**: Monitor and control AI system components
- **Key metrics**: Health score, active agents, token usage, skill count
- **Controls**: Provider switch, config apply, sync triggers
- **Alerts**: Component failures, high costs, model updates

### Project Dashboard
- **Purpose**: Overview of all projects and their status
- **Key metrics**: Active projects, completion rate, agent assignments
- **Visuals**: Kanban board, timeline, resource allocation

### Analytics Dashboard
- **Purpose**: Performance and usage analytics
- **Key metrics**: Token consumption, cost per project, model performance
- **Visuals**: Time-series charts, heatmaps, comparison tables

## Layout Architecture

### The "Mission Control" Pattern
```
┌─────────────────────────────────────────────────────────┐
│  [LOGO]  GT CENTER    [Health: 100%]    [Alerts: 0]   │  ← Status Bar
├──────────┬────────────────────────────────────────────┤
│          │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  NAV     │  │ METRIC 1 │  │ METRIC 2 │  │ METRIC 3 │  │  ← Primary Metrics
│          │  └──────────┘  └──────────┘  └──────────┘  │
│  · Skills│                                              │
│  · Config│  ┌────────────────────────────────────────┐  │
│  · Agents│  │         MAIN CONTENT AREA              │  │  ← Detail View
│  · Proj  │  │    (tables, charts, logs)              │  │
│  · Secr  │  └────────────────────────────────────────┘  │
│          │                                              │
├──────────┴────────────────────────────────────────────┤
│  System: Online | Agents: 5 | Last Sync: 2 min ago   │  ← Footer
└─────────────────────────────────────────────────────────┘
```

### Component Hierarchy
1. **Status Bar**: Fixed top, always visible, system-wide info
2. **Navigation**: Left sidebar, collapsible, icon + label
3. **Metrics Row**: Top of main area, 3-4 large numbers
4. **Content Area**: Adaptive, changes based on route
5. **Footer**: Fixed bottom, version, last update, quick actions

## Data Visualization

### Health Score Gauge
```tsx
const HealthGauge = ({ score }) => {
  const color = score >= 90 ? 'text-green-400' : 
                score >= 70 ? 'text-amber-400' : 'text-red-400';
  
  return (
    <div className="flex items-center gap-3">
      <div className={`text-4xl font-bold font-mono ${color}`}>
        {score}%
      </div>
      <div className="flex flex-col">
        <span className="text-xs text-slate-500 uppercase">Health</span>
        <div className="w-24 h-1.5 bg-slate-800 rounded-full mt-1">
          <div 
            className={`h-full rounded-full ${color.replace('text', 'bg')}`}
            style={{ width: `${score}%` }}
          />
        </div>
      </div>
    </div>
  );
};
```

### Agent Status Grid
```tsx
const AgentGrid = ({ agents }) => (
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
    {agents.map(agent => (
      <div key={agent.id} className={`
        rounded-lg border p-3
        ${agent.status === 'active' 
          ? 'border-green-500/30 bg-green-500/5' 
          : 'border-slate-700 bg-slate-800/30'}
      `}>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            agent.status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-slate-600'
          }`} />
          <span className="text-sm font-medium text-white">{agent.name}</span>
        </div>
        <div className="mt-2 text-xs text-slate-500">
          {agent.task || 'Idle'}
        </div>
      </div>
    ))}
  </div>
);
```

### Real-Time Log Stream
```tsx
const LogStream = ({ logs }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [logs]);
  
  return (
    <div 
      ref={scrollRef}
      className="h-48 overflow-y-auto font-mono text-xs bg-slate-900/50 rounded-lg p-3"
    >
      {logs.map((log, i) => (
        <div key={i} className="flex gap-2 py-0.5">
          <span className="text-slate-600 shrink-0">
            {log.timestamp}
          </span>
          <span className={`
            ${log.level === 'error' ? 'text-red-400' : ''}
            ${log.level === 'warn' ? 'text-amber-400' : ''}
            ${log.level === 'info' ? 'text-cyan-400' : ''}
          `}>
            {log.message}
          </span>
        </div>
      ))}
    </div>
  );
};
```

## State Management

### Dashboard Store (Zustand)
```ts
interface DashboardState {
  health: number;
  alerts: Alert[];
  activeAgents: Agent[];
  systemConfig: Config;
  
  // Actions
  refreshHealth: () => Promise<void>;
  dismissAlert: (id: string) => void;
  switchProvider: (provider: string) => Promise<void>;
  syncSkills: () => Promise<void>;
}

const useDashboardStore = create<DashboardState>((set, get) => ({
  health: 100,
  alerts: [],
  activeAgents: [],
  systemConfig: {},
  
  refreshHealth: async () => {
    const res = await fetch('/api/gt/health');
    const data = await res.json();
    set({ health: data.score });
  },
  
  dismissAlert: (id) => {
    set(state => ({
      alerts: state.alerts.filter(a => a.id !== id)
    }));
  },
  
  switchProvider: async (provider) => {
    await fetch(`/api/gt/secrets/activate`, {
      method: 'POST',
      body: JSON.stringify({ provider })
    });
    await get().refreshHealth();
  },
  
  syncSkills: async () => {
    await fetch('/api/webhooks/skills-sync', { method: 'POST' });
  }
}));
```

## Real-Time Updates

### WebSocket Connection
```ts
const useWebSocket = (url: string) => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => setLastMessage(JSON.parse(event.data));
    
    return () => ws.close();
  }, [url]);
  
  return { connected, lastMessage };
};
```

### Polling Fallback
```ts
const usePolling = (fetchFn: () => Promise<any>, interval = 5000) => {
  useEffect(() => {
    const timer = setInterval(fetchFn, interval);
    return () => clearInterval(timer);
  }, [fetchFn, interval]);
};
```

## Responsive Breakpoints
- **4K (>1920px)**: 4-column metrics, expanded sidebar
- **Desktop (1280-1920px)**: 3-column metrics, full sidebar
- **Laptop (1024-1280px)**: 2-column metrics, collapsed sidebar
- **Tablet (768-1024px)**: 2-column metrics, hidden sidebar (hamburger)
- **Mobile (<768px)**: 1-column, bottom nav, cards stack vertically

## Performance
- Virtualize long lists (react-window)
- Debounce rapid updates (lodash.debounce)
- Use CSS transforms for animations (GPU accelerated)
- Lazy load chart libraries (dynamic imports)
- Memoize expensive computations (useMemo)

## Keyboard Shortcuts
- `Cmd/Ctrl + K`: Command palette
- `Cmd/Ctrl + 1-9`: Switch between main sections
- `Cmd/Ctrl + R`: Refresh data
- `Esc`: Close modals/panels
- `?`: Show shortcut help

## Error States
- **Loading**: Skeleton screens with pulse animation
- **Empty**: Illustration + CTA button
- **Error**: Red panel with retry button and error details
- **Offline**: Yellow banner with reconnect countdown

## References
- `references/billing-tab-redesign.md` — API key billing display patterns (usage-based vs balance-based providers)

## Related Skills
- `frontend-developer` — React/Tailwind implementation
- `ui-ux-designer` — Sci-fi interface design
- `gt-centralized-system` — GT Core integration
