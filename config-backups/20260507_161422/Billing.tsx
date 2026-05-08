import { useState, useEffect } from 'react'
import { api } from '../api/client'
import {
  CreditCard,
  TrendingUp,
  AlertTriangle,
  Wallet,
  Key,
  Clock,
  Calendar,
  Zap,
  Loader2,
  RefreshCw,
  CheckCircle,
  XCircle,
  DollarSign,
  BarChart3,
} from 'lucide-react'

interface BalanceAccount {
  provider: string
  label: string
  api_key_env: string
  api_key_masked: string
  base_url: string
  balance: number | null
  currency: string
  cash_balance?: number | null
  voucher_balance?: number | null
  status: string
  message?: string
  response_ms: number
}

interface UsageSummary {
  provider: string
  api_key_env: string
  api_key_masked: string
  today_tokens: number
  today_requests: number
  today_cost: number
  week_tokens: number
  week_requests: number
  week_cost: number
  month_tokens: number
  month_requests: number
  month_cost: number
  total_tokens: number
  total_requests: number
  total_cost: number
}

export default function Billing() {
  const [balanceData, setBalanceData] = useState<any>(null)
  const [usageSummary, setUsageSummary] = useState<any>(null)
  const [recentUsage, setRecentUsage] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'usage' | 'history'>('overview')

  async function loadAll(force = false) {
    if (force) setRefreshing(true)
    try {
      const [b, u, r] = await Promise.all([
        api.get('/billing/balance').catch(() => null),
        api.get('/billing/usage/summary').catch(() => null),
        api.get('/billing/usage/recent?limit=20').catch(() => null),
      ])
      setBalanceData(b)
      setUsageSummary(u)
      setRecentUsage(r?.records || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadAll()
    const interval = setInterval(() => loadAll(), 300000) // auto-refresh every 5 min
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
        <span className="ml-3 text-gray-500">Loading billing data...</span>
      </div>
    )
  }

  const accounts: BalanceAccount[] = balanceData?.accounts || []
  const summaries: UsageSummary[] = usageSummary?.summaries || []
  const grandTotal = usageSummary?.grand_total || {}
  const summary = balanceData?.summary || {}

  const totalBalance = accounts.reduce((acc, a) => acc + (a.balance || 0), 0)
  const lowBalanceAccounts = accounts.filter(a => (a.balance || 0) < 5 && a.status === 'ok')

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Wallet className="w-6 h-6 text-emerald-400" />
            Billing & Usage
          </h2>
          <p className="text-gray-500 text-sm">Track all API keys, balances, and token usage across providers</p>
        </div>
        <button
          className="btn-secondary"
          onClick={() => loadAll(true)}
          disabled={refreshing}
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 bg-gray-900 rounded-lg p-1 w-fit">
        {[
          { key: 'overview', label: 'Overview', icon: BarChart3 },
          { key: 'usage', label: 'Usage Details', icon: TrendingUp },
          { key: 'history', label: 'Recent Calls', icon: Clock },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key as any)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === t.key
                ? 'bg-blue-900/40 text-blue-300'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            <t.icon className="w-4 h-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Low balance alerts */}
      {lowBalanceAccounts.length > 0 && (
        <div className="bg-yellow-950/20 border border-yellow-900/30 rounded-lg px-4 py-3 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-400">Low Balance Alert</p>
            <p className="text-xs text-yellow-500/80 mt-1">
              {lowBalanceAccounts.map(a => `${a.label} ($${a.balance?.toFixed(2)})`).join(', ')} — top up soon.
            </p>
          </div>
        </div>
      )}

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card">
              <div className="flex items-center gap-3 mb-3">
                <DollarSign className="w-5 h-5 text-emerald-400" />
                <h3 className="font-semibold">Total Balance</h3>
              </div>
              <p className="text-3xl font-bold">${totalBalance.toFixed(2)}</p>
              <p className="text-sm text-gray-500 mt-1">Across {summary.total_accounts || 0} accounts</p>
            </div>

            <div className="card">
              <div className="flex items-center gap-3 mb-3">
                <Zap className="w-5 h-5 text-blue-400" />
                <h3 className="font-semibold">Today's Usage</h3>
              </div>
              <p className="text-3xl font-bold">{grandTotal.today_tokens?.toLocaleString() || 0}</p>
              <p className="text-sm text-gray-500 mt-1">
                {grandTotal.today_requests || 0} requests · ${grandTotal.today_cost?.toFixed(4) || '0.0000'}
              </p>
            </div>

            <div className="card">
              <div className="flex items-center gap-3 mb-3">
                <Calendar className="w-5 h-5 text-purple-400" />
                <h3 className="font-semibold">This Week</h3>
              </div>
              <p className="text-3xl font-bold">{grandTotal.week_tokens?.toLocaleString() || 0}</p>
              <p className="text-sm text-gray-500 mt-1">
                {grandTotal.week_requests || 0} requests · ${grandTotal.week_cost?.toFixed(4) || '0.0000'}
              </p>
            </div>
          </div>

          {/* Accounts table */}
          <div className="card">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Key className="w-4 h-4 text-blue-400" />
              API Accounts
            </h3>
            {accounts.length === 0 ? (
              <p className="text-gray-500 text-sm">No API keys configured. Add keys in ~/.hermes/.env</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Provider</th>
                    <th>Key</th>
                    <th>Balance</th>
                    <th>Status</th>
                    <th>Today</th>
                    <th>Week</th>
                  </tr>
                </thead>
                <tbody>
                  {accounts.map((a, i) => {
                    const usage = summaries.find(
                      s => s.provider === a.provider && s.api_key_env === a.api_key_env
                    )
                    return (
                      <tr key={i}>
                        <td>
                          <div className="font-medium text-sm">{a.label}</div>
                          <div className="text-xs text-gray-500">{a.provider}</div>
                        </td>
                        <td className="font-mono text-xs text-gray-400">{a.api_key_masked}</td>
                        <td>
                          {a.balance != null ? (
                            <span className="font-mono font-medium">
                              ${a.balance.toFixed(2)} <span className="text-gray-500">{a.currency}</span>
                            </span>
                          ) : (
                            <span className="text-gray-500 text-xs">—</span>
                          )}
                        </td>
                        <td>
                          {a.status === 'ok' ? (
                            <span className="badge-green text-xs flex items-center gap-1 w-fit">
                              <CheckCircle className="w-3 h-3" /> OK
                            </span>
                          ) : (
                            <span className="badge-red text-xs flex items-center gap-1 w-fit">
                              <XCircle className="w-3 h-3" /> Error
                            </span>
                          )}
                        </td>
                        <td className="font-mono text-xs">
                          {usage ? `${usage.today_tokens.toLocaleString()} tk` : '—'}
                        </td>
                        <td className="font-mono text-xs">
                          {usage ? `${usage.week_tokens.toLocaleString()} tk` : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* USAGE DETAILS TAB */}
      {activeTab === 'usage' && (
        <div className="card">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            Usage Breakdown by Key
          </h3>
          {summaries.length === 0 ? (
            <p className="text-gray-500 text-sm">No usage recorded yet. Usage is tracked when API calls are made through the dashboard, pi, or hermes.</p>
          ) : (
            <div className="space-y-3">
              {summaries.map((s, i) => (
                <div key={i} className="bg-gray-900/50 border border-gray-800 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium capitalize">{s.provider}</span>
                      <span className="font-mono text-xs text-gray-500">{s.api_key_masked}</span>
                    </div>
                    <span className="text-xs text-gray-500">{s.total_requests} total calls</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-xs">
                    <div className="bg-gray-950 rounded p-2">
                      <div className="text-gray-600 mb-1">Today</div>
                      <div className="font-mono font-medium">{s.today_tokens.toLocaleString()} tk</div>
                      <div className="text-gray-500">{s.today_requests} req · ${s.today_cost.toFixed(4)}</div>
                    </div>
                    <div className="bg-gray-950 rounded p-2">
                      <div className="text-gray-600 mb-1">This Week</div>
                      <div className="font-mono font-medium">{s.week_tokens.toLocaleString()} tk</div>
                      <div className="text-gray-500">{s.week_requests} req · ${s.week_cost.toFixed(4)}</div>
                    </div>
                    <div className="bg-gray-950 rounded p-2">
                      <div className="text-gray-600 mb-1">This Month</div>
                      <div className="font-mono font-medium">{s.month_tokens.toLocaleString()} tk</div>
                      <div className="text-gray-500">{s.month_requests} req · ${s.month_cost.toFixed(4)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* RECENT CALLS TAB */}
      {activeTab === 'history' && (
        <div className="card">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-blue-400" />
            Recent API Calls
          </h3>
          {recentUsage.length === 0 ? (
            <p className="text-gray-500 text-sm">No API calls recorded yet.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Provider</th>
                  <th>Model</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                  <th>Status</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {recentUsage.map((r, i) => (
                  <tr key={i}>
                    <td className="text-xs text-gray-400">
                      {r.created_at ? new Date(r.created_at).toLocaleTimeString() : '—'}
                    </td>
                    <td className="text-xs capitalize">{r.provider}</td>
                    <td className="text-xs font-mono text-gray-400">{r.model || '—'}</td>
                    <td className="text-xs font-mono">{r.tokens_total?.toLocaleString() || 0}</td>
                    <td className="text-xs font-mono">${r.cost_usd?.toFixed(4) || '—'}</td>
                    <td>
                      {r.request_status === 'success' ? (
                        <CheckCircle className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <XCircle className="w-3 h-3 text-red-400" />
                      )}
                    </td>
                    <td className="text-xs text-gray-500">{r.source_system || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
