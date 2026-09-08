import { useState } from 'react'
import { sendOtp, setAuth, verifyOtp } from '../api'

export default function Login({ onDone }: { onDone: (user: any) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [mobile, setMobile] = useState('')
  const [name, setName] = useState('')
  const [otp, setOtp] = useState('')
  const [otpSent, setOtpSent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function requestOtp() {
    if (!/^\d{10}$/.test(mobile)) { setError('Enter a valid 10-digit mobile number'); return }
    setBusy(true); setError('')
    try {
      await sendOtp(mobile)
      setOtpSent(true)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to send OTP')
    } finally { setBusy(false) }
  }

  async function verify() {
    if (otp.length !== 6) { setError('Enter the 6-digit OTP'); return }
    setBusy(true); setError('')
    try {
      const data = await verifyOtp(mobile, otp, mode === 'register' ? name : '')
      setAuth(data.access_token, data.user)
      onDone(data.user)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Invalid OTP')
    } finally { setBusy(false) }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #eef2ff 0%, #f9f9ff 50%, #eafaf0 100%)', padding: 24,
    }}>
      <div className="card" style={{ width: 380, padding: 32 }}>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <span style={{ fontSize: 30, fontWeight: 800 }}>
            <span style={{ color: 'var(--primary)' }}>🌿</span> Gram<span style={{ color: 'var(--primary)' }}>AI</span>
          </span>
        </div>

        <div style={{ display: 'flex', background: 'var(--surface-container)', borderRadius: 12, padding: 4, marginBottom: 20 }}>
          {(['login', 'register'] as const).map(m => (
            <button key={m} style={{
              flex: 1, border: 'none', borderRadius: 9, padding: '10px 0', cursor: 'pointer',
              fontWeight: 600, fontSize: 14,
              background: mode === m ? 'var(--surface-container-lowest)' : 'transparent',
              color: mode === m ? 'var(--on-surface)' : 'var(--outline)',
              boxShadow: mode === m ? 'var(--shadow-card)' : undefined,
            }} onClick={() => { setMode(m); setOtpSent(false); setError('') }}>
              {m === 'login' ? 'Login' : 'Register'}
            </button>
          ))}
        </div>

        {error && <div className="error-box" style={{ marginBottom: 12 }}>{error}</div>}

        {mode === 'register' && !otpSent && (
          <div className="field">
            <label>Full Name</label>
            <input value={name} onChange={e => setName(e.target.value)}
                   placeholder="e.g. Ramesh Kumar" />
          </div>
        )}

        {!otpSent ? (
          <>
            <div className="field">
              <label>Mobile Number</label>
              <input value={mobile} onChange={e => setMobile(e.target.value.replace(/\D/g, '').slice(0, 10))}
                     placeholder="e.g. +91 98765 43210" inputMode="numeric" />
            </div>
            <button className="btn" style={{ width: '100%', justifyContent: 'center' }}
                    disabled={busy || mobile.length !== 10} onClick={requestOtp}>
              {busy ? 'Sending…' : 'Send OTP'}
            </button>
          </>
        ) : (
          <>
            <div className="field">
              <label>Enter OTP (demo: 123456)</label>
              <input value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                     placeholder="••••••" inputMode="numeric"
                     style={{ letterSpacing: 8, textAlign: 'center', fontSize: 20 }} />
            </div>
            <button className="btn" style={{ width: '100%', justifyContent: 'center' }}
                    disabled={busy || otp.length !== 6} onClick={verify}>
              {busy ? 'Verifying…' : 'Continue'}
            </button>
            <button className="btn btn-ghost btn-sm" style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}
                    onClick={() => { setOtpSent(false); setOtp('') }}>
              Change number
            </button>
          </>
        )}

        <div className="mono-label muted" style={{ marginTop: 20, textAlign: 'center' }}>
          Secure access to GramAI intelligence platform.
        </div>
      </div>
    </div>
  )
}
