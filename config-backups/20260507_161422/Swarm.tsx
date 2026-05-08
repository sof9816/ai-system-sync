import { useState } from 'react'
import { api } from '../api/client'
import {
  Zap,
  Send,
  Bot,
  Users,
  Clock,
  CheckCircle,
  AlertTriangle,
  Copy,
} from 'lucide-react'

interface SwarmResult {
  response: string
  plan?: {
    mode: string
    agents: string[]
  }
}

export default function Swarm() {
  const [input, setInput] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<SwarmResult | null>(null)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  async function runSwarm() {
    if (!input.trim() || running) return
    setRunning(true)
    setError('')
    setResult(null)
    try {
      const res = await fetch(`${import.meta.env.PROD ? '/api' : 'http://localhost:7373/api'}/agents/swarm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input.trim() }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || res.statusText)
      }
      const data = await res.json()
      setResult(data)
    } catch (e: any) {
      setError(e.message || 'Swarm failed')
    } finally {
      setRunning(false)
    }
  }

  function copyResult() {
    if (!result?.response) return
    navigator.clipboard.writeText(result.response)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Swarm Mode</h2>
        <p className="text-gray-500 text-sm mt-1">
          Delegate to multiple specialist agents in parallel. The system routes your query to the right experts and synthesizes a unified response.
        </p>
      </div>

      <div className="card space-y-3">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-yellow-400" />
          <h3 className="font-semibold">Multi-Agent Query</h3>
        </div>
        <textarea
          className="textarea w-full min-h-[120px]"
          placeholder="e.g. 'I want to build a real-time crypto tracking app. What's the best stack and how much will it cost?'"
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={running}
        />
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Users className="w-3.5 h-3.5" />
            <span>Auto-routes to 1-3 agents</span>
            <span className="text-gray-700">|</span>
            <Clock className="w-3.5 h-3.5" />
            <span>~60-90s</span>
          </div>
          <button
            className="btn-primary"
            onClick={runSwarm}
            disabled={running || !input.trim()}
          >
            {running ? (
              <>
                <Bot className="w-4 h-4 animate-pulse" /> Running Swarm...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" /> Run Swarm
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="card border-red-900/50 bg-red-900/10 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-300">Swarm Error</p>
            <p className="text-xs text-red-400 mt-1">{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="card space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              <h3 className="font-semibold">Synthesized Result</h3>
            </div>
            <button className="btn-secondary text-xs" onClick={copyResult}>
              {copied ? (
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )}
              {copied ? ' Copied' : ' Copy'}
            </button>
          </div>
          <div className="bg-gray-950 rounded-lg border border-gray-800 p-4 text-sm whitespace-pre-wrap leading-relaxed text-gray-300 max-h-[60vh] overflow-y-auto">
            {result.response}
          </div>
        </div>
      )}

      <div className="card">
        <h3 className="font-semibold mb-3 text-sm text-gray-400">How it works</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
          <div className="bg-gray-950 rounded p-3 border border-gray-800">
            <p className="font-medium text-blue-400 mb-1">1. Route</p>
            <p className="text-gray-500 text-xs">Keyword-based router instantly picks the right specialist agents.</p>
          </div>
          <div className="bg-gray-950 rounded p-3 border border-gray-800">
            <p className="font-medium text-purple-400 mb-1">2. Execute</p>
            <p className="text-gray-500 text-xs">Selected agents run in parallel with your query.</p>
          </div>
          <div className="bg-gray-950 rounded p-3 border border-gray-800">
            <p className="font-medium text-emerald-400 mb-1">3. Synthesize</p>
            <p className="text-gray-500 text-xs">A final synthesis merges all outputs into one coherent answer.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
