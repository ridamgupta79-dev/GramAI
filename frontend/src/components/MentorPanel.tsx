import { useState } from 'react'
import { mentorChat } from '../dashboardApi'

interface Props { reportId?: string }

export default function MentorPanel({ reportId }: Props) {
  const [messages, setMessages] = useState<{ role: 'user' | 'mentor'; text: string }[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)

  async function send() {
    const q = input.trim()
    if (!q || busy) return
    setMessages(m => [...m, { role: 'user', text: q }])
    setInput(''); setBusy(true)
    try {
      const { answer } = await mentorChat(q, reportId)
      setMessages(m => [...m, { role: 'mentor', text: answer }])
    } catch {
      setMessages(m => [...m, { role: 'mentor', text: 'Sorry, something went wrong.' }])
    } finally { setBusy(false) }
  }

  return (
    <div className="card">
      <h2>🤖 AI Mentor</h2>
      <div style={{ maxHeight: 260, overflowY: 'auto', marginBottom: '.5rem' }}>
        {messages.length === 0 && (
          <p style={{ color: '#5d6f64' }}>Ask anything about your business plan, loan or schemes…</p>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{
            margin: '.4rem 0', padding: '.55rem .8rem', borderRadius: 10,
            background: m.role === 'user' ? '#eef6f0' : '#f1f3f2',
            marginLeft: m.role === 'user' ? '2rem' : 0,
          }}>{m.text}</div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: '.5rem' }}>
        <input type="text" value={input} placeholder="Type your question…"
               onChange={e => setInput(e.target.value)}
               onKeyDown={e => e.key === 'Enter' && send()} />
        <button className="btn" style={{ marginTop: 0 }} disabled={busy} onClick={send}>Send</button>
      </div>
    </div>
  )
}
