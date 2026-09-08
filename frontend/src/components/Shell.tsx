import { ReactNode } from 'react'
import { Page } from '../App'

const NAV: { id: Page; icon: string; label: string }[] = [
  { id: 'home', icon: 'grid_view', label: 'Home' },
  { id: 'new', icon: 'post_add', label: 'New Analysis' },
  { id: 'schemes', icon: 'account_balance', label: 'Schemes' },
  { id: 'reports', icon: 'description', label: 'Reports' },
  { id: 'advisor', icon: 'support_agent', label: 'AI Advisor' },
  { id: 'profile', icon: 'person', label: 'Profile' },
  { id: 'admin', icon: 'settings', label: 'Admin' },
]

interface Props {
  page: Page
  onNavigate: (p: Page) => void
  userName: string
  isAdmin?: boolean
  onSignOut?: () => void
  children: ReactNode
}

export default function Shell({
  page,
  onNavigate,
  userName,
  isAdmin,
  onSignOut,
  children,
}: Props) {
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="leaf">
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 16 }}
            >
              eco
            </span>
          </span>
          Gram<b>AI</b>
        </div>

        <nav className="nav-group">
          {NAV.filter(
            n => n.id !== 'admin' || isAdmin
          ).map(n => (
            <button
              key={n.id}
              className={`nav-item ${
                page === n.id ? 'active' : ''
              }`}
              onClick={() => onNavigate(n.id)}
            >
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 20 }}
              >
                {n.icon}
              </span>
              {n.label}
            </button>
          ))}
        </nav>

        <div className="nav-spacer" />
      </aside>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="topbar">
          <div className="search">
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 20 }}
            >
              search
            </span>
            <input placeholder="Search analysis, maps or reports..." />
          </div>

          <div
            className="user-chip"
            onClick={onSignOut}
            style={{
              cursor: onSignOut ? 'pointer' : undefined,
            }}
            title={
              onSignOut
                ? 'Click to sign out'
                : undefined
            }
          >
            <div style={{ textAlign: 'right' }}>
              <div>{userName}</div>
              <div className="status">● ONLINE</div>
            </div>

            <div className="avatar">
              {userName[0]?.toUpperCase()}
            </div>
          </div>
        </div>

        <main className="content">{children}</main>
      </div>
    </div>
  )
}