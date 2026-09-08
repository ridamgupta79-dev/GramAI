import { useEffect, useState } from 'react'
import { api, clearAuth } from '../api'
import { Page } from '../App'

export default function Profile({ onNavigate }: { onNavigate: (p: Page) => void }) {
  const [me, setMe] = useState<any>(null)
  const [reports, setReports] = useState<any[]>([])
  const [apps, setApps] = useState(0)

  useEffect(() => {
    api.get('/users/me').then(r => setMe(r.data)).catch(() => {})
    api.get('/reports', { params: { limit: 10 } }).then(r => setReports(r.data)).catch(() => {})
    api.get('/users/me/dashboard').then(r => setApps(r.data.recent_reports?.length ?? 0)).catch(() => {})
  }, [])

  if (!me) return <div className="card loading">Loading profile…</div>

  const initials = (me.full_name || me.mobile || 'U')[0]?.toUpperCase()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div className="card" style={{
        background: 'linear-gradient(120deg, var(--surface-container-low), var(--primary-fixed))',
        display: 'flex', alignItems: 'center', gap: 24,
      }}>
        <div className="avatar" style={{ width: 88, height: 88, fontSize: 32 }}>{initials}</div>
        <div style={{ flex: 1 }}>
          <h1 className="headline-lg" style={{ margin: 0 }}>{me.full_name || 'GramAI User'}</h1>
          <div className="label-sm muted">+91 {String(me.mobile).replace(/(\d{5})(\d{5})/, '$1 $2')}</div>
          <div className="mono-label muted" style={{ marginTop: 4 }}>
            Member · Role: {me.role}
          </div>
        </div>
      </div>

      <div className="bento">
        <div className="card col-4">
          <div className="mono-label muted">Reports Generated</div>
          <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--primary)' }}>{reports.length}</div>
          <div className="label-sm muted">saved in your account</div>
        </div>
        <div className="card col-4">
          <div className="mono-label muted">Preferred Language</div>
          <div style={{ fontSize: 22, fontWeight: 700, textTransform: 'uppercase' }}>{me.preferred_lang}</div>
          <div className="label-sm muted">used for reports & advisor</div>
        </div>
        <div className="card col-4">
          <div className="mono-label muted">Profile Completeness</div>
          <div style={{ fontSize: 32, fontWeight: 800 }}>{me.full_name ? 80 : 40}%</div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: me.full_name ? '80%' : '40%' }} />
          </div>
        </div>

        <div className="card col-8">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2 className="title-md" style={{ margin: 0 }}>My Reports</h2>
            <button className="btn btn-sm btn-ghost" onClick={() => onNavigate('reports')}>View All</button>
          </div>
          {reports.length === 0 ? (
            <p className="muted label-sm" style={{ marginTop: 12 }}>
              No reports yet — run your first analysis from the Home page.
            </p>
          ) : (
            <table className="gramai">
              <thead><tr><th>Report</th><th>Created</th><th></th></tr></thead>
              <tbody>
                {reports.map(r => (
                  <tr key={r.id}>
                    <td style={{ fontWeight: 600, textTransform: 'capitalize' }}>{r.title || r.id}</td>
                    <td className="muted">{new Date(r.created_at).toLocaleDateString()}</td>
                    <td><span className="badge green">Saved</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="col-4" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <h2 className="title-md" style={{ marginTop: 0 }}>Settings</h2>
            <div className="field">
              <label>Language</label>
              <select defaultValue={me.preferred_lang} disabled>
                {['en', 'hi', 'mr', 'ta'].map(l => <option key={l}>{l}</option>)}
              </select>
            </div>
            <button className="btn btn-ghost" style={{ color: 'var(--error)', width: '100%', justifyContent: 'center' }}
                    onClick={() => { clearAuth(); window.location.reload() }}>
              <span className="material-symbols-outlined" style={{ fontSize: 18 }}>logout</span> Sign Out
            </button>
          </div>
          <div className="card">
            <h2 className="title-md" style={{ marginTop: 0 }}>Account</h2>
            <div style={{ fontSize: 14, lineHeight: 2 }}>
              <div>User ID: <b>#{me.id}</b></div>
              <div>Mobile: <b>+91 {String(me.mobile).replace(/(\d{5})(\d{5})/, '$1 $2')}</b></div>
              <div>Role: <span className="badge">{me.role}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
