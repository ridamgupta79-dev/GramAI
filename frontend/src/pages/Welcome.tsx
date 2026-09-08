const LANGS = [
  ['English', 'English'], ['Hindi', 'हिन्दी'], ['Marathi', 'मराठी'],
  ['Tamil', 'தமிழ்'], ['Telugu', 'తెలుగు'], ['Bengali', 'বাংলা'],
] as const

export default function Welcome({ onStart }: { onStart: () => void }) {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', textAlign: 'center',
      background: 'linear-gradient(135deg, #eef2ff 0%, #f9f9ff 50%, #eafaf0 100%)',
      padding: 24,
    }}>
      <div style={{
        width: 64, height: 64, borderRadius: 18,
        background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#fff', marginBottom: 20, boxShadow: 'var(--shadow-card)',
      }}>
        <span className="material-symbols-outlined" style={{ fontSize: 32 }}>eco</span>
      </div>
      <h1 style={{ fontSize: 40, fontWeight: 800, margin: '0 0 12px' }}>
        Gram<span style={{ color: 'var(--primary)' }}>AI</span>
      </h1>
      <h2 style={{ fontSize: 26, fontWeight: 700, maxWidth: 560, margin: '0 0 12px', lineHeight: 1.3 }}>
        Empowering Rural Entrepreneurs with AI Intelligence
      </h2>
      <p className="muted" style={{ maxWidth: 480, margin: '0 0 32px', lineHeight: 1.6 }}>
        Unlock actionable insights, optimize your agricultural business, and connect
        with global markets using advanced, localized artificial intelligence.
      </p>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button className="btn" onClick={onStart}>
          Start Your Journey <span className="material-symbols-outlined" style={{ fontSize: 18 }}>arrow_forward</span>
        </button>
        <select className="suggest-chip" defaultValue="English"
                style={{ padding: '12px 16px', borderRadius: 999 }}>
          {LANGS.map(([v, l]) => <option key={v}>{l}</option>)}
        </select>
      </div>
      <div style={{
        position: 'fixed', bottom: 16, left: 24, fontSize: 11, color: 'var(--outline)',
      }}>V2.4.0-BETA</div>
      <div style={{
        position: 'fixed', bottom: 16, right: 24, fontSize: 11, color: 'var(--secondary)',
      }}>● SYSTEM ONLINE</div>
    </div>
  )
}
