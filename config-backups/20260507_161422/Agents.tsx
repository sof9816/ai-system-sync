import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import { Send, Bot, User, History, Trash2 } from 'lucide-react'

interface AgentDef {
  name: string
  role: string
  icon?: string
  tab?: string
}

export default function Agents() {
  const [agents, setAgents] = useState<AgentDef[]>([])
  const [selected, setSelected] = useState<string>('')
  const [messages, setMessages] = useState<{role: string, content: string}[]>([])
  const [input, setInput] = useState('')
  const [running, setRunning] = useState(false)
  const [loadingHistory, setLoadingHistory] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.getAgents().then((d: any) => {
      const list: AgentDef[] = Array.isArray(d) ? d : (d.agents || [])
      setAgents(list)
      if (list.length > 0 && !selected) {
        setSelected(list[0].name)
      }
    })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (!selected) return
    setMessages([])
    setLoadingHistory(true)
    api.getAgentHistory(selected, 50)
      .then((history: any[]) => {
        const loaded = history.map(h => ({
          role: h.role === 'user' ? 'user' : 'assistant',
          content: h.message,
          timestamp: h.timestamp,
        }))
        setMessages(loaded)
      })
      .catch(() => setMessages([]))
      .finally(() => setLoadingHistory(false))
  }, [selected])

  async function send() {
    if (!input.trim() || running || !selected) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setRunning(true)
    try {
      const res = await api.chat(selected, userMsg)
      setMessages(prev => [...prev, { role: 'assistant', content: res.response || 'No response' }])
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + e.message }])
    } finally {
      setRunning(false)
    }
  }

  function clearChat() {
    setMessages([])
  }

  return (
    <div className="space-y-4 h-[calc(100vh-6rem)] flex flex-col">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Agents</h2>
          <p className="text-gray-500 text-sm">Chat with any configured agent</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="btn-secondary text-xs"
            onClick={clearChat}
            title="Clear local chat view"
          >
            <Trash2 className="w-3.5 h-3.5" /> Clear
          </button>
          <select
            className="input w-56"
            value={selected}
            onChange={e => {
              setSelected(e.target.value)
            }}
          >
            {agents.map((a: AgentDef) => (
              <option key={a.name} value={a.name}>{a.name} — {a.role}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 card flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
          {loadingHistory && (
            <div className="text-center text-gray-500 mt-10">
              <History className="w-6 h-6 mx-auto mb-2 animate-spin opacity-50" />
              <p className="text-sm">Loading history...</p>
            </div>
          )}
          {!loadingHistory && messages.length === 0 && (
            <div className="text-center text-gray-500 mt-10">
              <Bot className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p>Start a conversation with the {selected} agent</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center shrink-0">
                {m.role === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5 text-blue-400" />}
              </div>
              <div className={`max-w-[80%] px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${
                m.role === 'user' ? 'bg-blue-900/40 text-blue-100' : 'bg-gray-800 text-gray-200'
              }`}>
                {m.content}
              </div>
            </div>
          ))}
          {running && (
            <div className="flex gap-3">
              <div className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center">
                <Bot className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
              </div>
              <div className="px-3 py-2 rounded-lg text-sm bg-gray-800 text-gray-500">Thinking...</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="mt-3 flex gap-2">
          <input
            className="input flex-1"
            placeholder={`Message ${selected}...`}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send()}
            disabled={running}
          />
          <button className="btn-primary" onClick={send} disabled={running}>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
