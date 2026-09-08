import { useEffect, useState } from 'react'
import { api } from '../api'

export default function Admin() {
  const [metrics, setMetrics] = useState<any>(null)
  const [users, setUsers] = useState<any[]>([])
  const [audit, setAudit] = useState<any[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/admin/metrics').then(r => setMetrics(r.data))
       .catch(e => setError(e?.response?.data?.detail ?? 'Admin access required'))
    api.get('/admin/users').then(r => setUsers(r.data)).catch(() => {})
    api.get('/admin/audit-log').then(r => setAudit(r.data)).catch(() => {})
  }, [])

  if (error) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <span className="material-symbols-outlined" style={{ fontSize: 48, color: 'var(--outline)' }}>lock</span>
        <h2 className="title-md" style={{ margin: '12px 0 4px' }}>Admin access required</h2>
        <p className="muted label-sm">Sign in with an admin account to view platform analytics.</p>
      </div>
    )
  }

  const stats: [string, any, string][] = [
    ['Total Users', metrics?.users ?? '—', 'registered accounts'],
    ['Analyses Run', metrics?.analyses ?? '—', 'all time'],
    ['Reports Generated', metrics?.reports ?? '—', 'all time'],
    ['Scheme Applications', metrics?.applications ?? '—', 'submitted'],
  ]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
        <div>
          <h1 className="display-lg" style={{ margin: 0, fontSize: 40 }}>Platform Command</h1>
          <p className="muted label-sm" style={{ margin: '4px 0 0' }}>
            Live platform statistics from the database.
          </p>
        </div>
      </div>

      <div className="bento">
        {stats.map(([label, val, sub]) => (
          <div className="card col-3" key={label}>
            <div className="mono-label muted">{label}</div>
            <div style={{ fontSize: 30, fontWeight: 800 }}>
              {typeof val === 'number' ? val.toLocaleString('en-IN') : val}
            </div>
            <div className="label-sm muted">{sub}</div>
          </div>
        ))}
        <div className="card col-3">
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div className="mono-label muted">System Health</div>
            <span className="dot" style={{ background: 'var(--secondary)' }} />
          </div>
          <div style={{ fontSize: 30, fontWeight: 800, color: 'var(--secondary)' }}>
            {metrics?.uptime_pct ?? '—'}%
          </div>
          <div className="label-sm muted">Conversations: {metrics?.conversations ?? 0}</div>
        </div>

        <div className="card col-8">
          <h2 className="title-md" style={{ marginTop: 0 }}>Users</h2>
          {users.length === 0 ? (
            <p className="muted label-sm">No users registered yet.</p>
          ) : (
            <table className="gramai">
              <thead><tr><th>User</th><th>Mobile</th><th>Role</th><th>Joined</th></tr></thead>
              <tbody>
                {users.map((u: any) => (
                  <tr key={u.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div className="avatar" style={{ width: 32, height: 32, fontSize: 13 }}>
                          {(u.name ?? '?')[0]?.toUpperCase()}
                        </div>
                        <div style={{ fontWeight: 600 }}>{u.name}</div>
                      </div>
                    </td>
                    <td className="muted">+91 {String(u.mobile).replace(/(\d{5})(\d{5})/, '$1 $2')}</td>
                    <td><span className={`badge ${u.role === 'admin' ? 'blue' : ''}`}>{u.role}</span></td>
                    <td className="muted">{u.joined}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card col-4" style={{ background: 'var(--inverse-surface)', color: '#edf0ff' }}>
          <h2 className="title-md" style={{ marginTop: 0, color: '#fff' }}>Activity Log</h2>
          {audit.length === 0 ? (
            <p style={{ opacity: .7, fontSize: 13 }}>No activity yet.</p>
          ) : (
            <div style={{ fontFamily: 'monospace', fontSize: 12, lineHeight: 2, opacity: .85, maxHeight: 320, overflowY: 'auto' }}>
              {audit.map((e: any) => (
                <div key={e.id + e.action}>
                  {new Date(e.ts * 1000).toLocaleTimeString()} [{e.action.split('.')[0].toUpperCase()}] {e.action}
                  {e.detail?.sector ? ` — ${e.detail.sector}` : ''}
                  {e.detail?.scheme ? ` — ${e.detail.scheme}` : ''}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
