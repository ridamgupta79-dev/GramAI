import { useEffect, useState } from 'react'
import { DashboardPayload } from '../dashboardApi'

const SECTORS = [
  ['dairy', 'Dairy'], ['retail', 'Retail / Kirana'], ['textiles', 'Textiles'],
  ['food_processing', 'Food Processing'], ['agriservices', 'Agri-Services'],
  ['poultry', 'Poultry'], ['handicrafts', 'Handicrafts'], ['other', 'Other'],
] as const

const STEPS = ['Location', 'Category', 'Financing', 'Review']

interface ApplicantProfile {
  isWoman: boolean
  isSCST: boolean
  previousTarunRepaid: boolean
}

/* ============================================================
   Browser Speech Recognition types
   ============================================================ */

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionInstance {
  lang: string
  continuous: boolean
  interimResults: boolean
  start: () => void
  stop: () => void
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognitionInstance
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}

interface Props {
  states: string[]
  districts: string[]
  blocks: string[]
  villages: string[]
  loc: { state: string; district: string; block: string; village: string }
  setLoc: (l: any) => void
  onStates: (s: string) => void
  onDistricts: (d: string) => void
  onBlocks: (b: string) => void
  sector: string
  setSector: (s: string) => void
  margin: number
  setMargin: (m: number) => void

  // Applicant profile is now passed to the parent when analysis starts
  onRun: (profile: ApplicantProfile) => void

  loading: boolean
  error: string
  payload: DashboardPayload | null
}

export default function NewAnalysis(p: Props) {
  const [step, setStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)

  // Applicant profile for personalized government-scheme matching
  const [isWoman, setIsWoman] = useState(false)
  const [isSCST, setIsSCST] = useState(false)
  const [previousTarunRepaid, setPreviousTarunRepaid] = useState(false)

  // Voice-first UX
  const [isListening, setIsListening] = useState(false)
  const [voiceText, setVoiceText] = useState('')
  const [voiceSupported, setVoiceSupported] = useState(true)

  useEffect(() => {
    if (!p.loading) {
      setElapsed(0)
      return
    }

    const t = setInterval(() => setElapsed(e => e + 1), 1000)

    return () => clearInterval(t)
  }, [p.loading])

  /* ============================================================
     Voice recognition
     ============================================================ */

  const startVoiceInput = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      setVoiceSupported(false)
      return
    }

    const recognition = new SpeechRecognition()

    recognition.lang = 'en-IN'
    recognition.continuous = false
    recognition.interimResults = false

    setIsListening(true)
    setVoiceText('')

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = event.results[0]?.[0]?.transcript || ''

      setVoiceText(transcript)

      const text = transcript.toLowerCase()

      // Detect business category
      if (text.includes('dairy') || text.includes('milk')) {
        p.setSector('dairy')
      } else if (
        text.includes('retail') ||
        text.includes('kirana') ||
        text.includes('shop') ||
        text.includes('store')
      ) {
        p.setSector('retail')
      } else if (
        text.includes('textile') ||
        text.includes('clothes') ||
        text.includes('garment')
      ) {
        p.setSector('textiles')
      } else if (
        text.includes('food processing') ||
        text.includes('food')
      ) {
        p.setSector('food_processing')
      } else if (
        text.includes('agri') ||
        text.includes('agriculture') ||
        text.includes('farming')
      ) {
        p.setSector('agriservices')
      } else if (text.includes('poultry') || text.includes('chicken')) {
        p.setSector('poultry')
      } else if (
        text.includes('handicraft') ||
        text.includes('handicrafts')
      ) {
        p.setSector('handicrafts')
      }

      // Detect common spoken numbers / rupee amounts
      const numericMatch = text.match(
        /(?:₹|rs\.?|rupees?)?\s*([\d,]+(?:\.\d+)?)\s*(?:thousand|k|lakh|lakhs|l)?/
      )

      if (numericMatch) {
        const raw = numericMatch[1].replace(/,/g, '')
        let amount = Number(raw)

        if (!Number.isNaN(amount)) {
          if (text.includes('lakh')) {
            amount *= 100000
          } else if (text.includes('thousand') || text.includes(' k')) {
            amount *= 1000
          }

          if (amount > 0) {
            p.setMargin(amount)
          }
        }
      }

      setIsListening(false)
    }

    recognition.onerror = () => {
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.start()
  }

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition

    setVoiceSupported(Boolean(SpeechRecognition))
  }, [])

  const canNext = [
    p.loc.state && p.loc.district && p.loc.block,
    true,
    p.margin > 0,
    true,
  ][step]

  const applicantProfile: ApplicantProfile = {
    isWoman,
    isSCST,
    previousTarunRepaid,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      <div>
        <h1 className="headline-lg" style={{ margin: 0 }}>
          New Business Wizard
        </h1>

        <p className="muted label-sm" style={{ margin: '4px 0 0' }}>
          Configure location, category, and financing to generate a comprehensive AI-driven market analysis.
        </p>
      </div>

      {/* ============================================================
          VOICE-FIRST INPUT
          ============================================================ */}

      {step === 1 || step === 2 ? (
        <div
          className="card-low"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
            padding: '14px 18px',
          }}
        >
          <div>
            <div
              className="mono-label"
              style={{ color: 'var(--primary)' }}
            >
              VOICE-FIRST INPUT
            </div>

            <div style={{ fontWeight: 600, marginTop: 4 }}>
              {isListening
                ? 'Listening... speak your business idea'
                : voiceText
                  ? `"${voiceText}"`
                  : 'Tell GramAI what business you want to start'}
            </div>

            {!voiceSupported && (
              <div className="muted label-sm" style={{ marginTop: 4 }}>
                Voice input is not supported in this browser. You can continue manually.
              </div>
            )}
          </div>

          <button
            className="btn"
            type="button"
            disabled={!voiceSupported || isListening}
            onClick={startVoiceInput}
            style={{
              minWidth: 150,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <span className="material-symbols-outlined">
              {isListening ? 'graphic_eq' : 'mic'}
            </span>

            {isListening ? 'Listening…' : 'Speak'}
          </button>
        </div>
      ) : null}

      {/* Stepper */}
      <div style={{ display: 'flex', gap: 4 }}>
        {STEPS.map((label, i) => (
          <div key={label} style={{ flex: 1 }}>
            <div
              style={{
                height: 4,
                borderRadius: 999,
                background:
                  i <= step
                    ? 'var(--primary)'
                    : 'var(--surface-container-highest)',
              }}
            />

            <div
              className="label-sm"
              style={{
                marginTop: 6,
                color:
                  i <= step
                    ? 'var(--primary)'
                    : 'var(--outline)',
                fontWeight: i === step ? 700 : 500,
              }}
            >
              {i + 1}. {label}
            </div>
          </div>
        ))}
      </div>

      {p.loading ? (

        /* ============================================================
           AI ANALYZING SCREEN
           ============================================================ */

        <div className="bento">

          <div
            className="card col-8"
            style={{
              textAlign: 'center',
              padding: 48,
            }}
          >
            <div
              style={{
                width: 140,
                height: 140,
                margin: '0 auto 24px',
                borderRadius: '999px',
                border: '3px solid var(--surface-container-highest)',
                borderTopColor: 'var(--primary)',
                animation: 'spin 1s linear infinite',
              }}
            />

            <style>
              {'@keyframes spin{to{transform:rotate(360deg)}}'}
            </style>

            <h2
              className="headline-lg"
              style={{ margin: '0 0 8px' }}
            >
              Generating Insights
            </h2>

            <p className="muted">
              Our intelligence engine is crunching millions of rural data points…
            </p>

            <div
              className="mono-label"
              style={{
                color: 'var(--primary)',
                marginTop: 16,
              }}
            >
              ELAPSED {elapsed}s
            </div>
          </div>

          <div className="card col-4">
            <h2
              className="title-md"
              style={{ marginTop: 0 }}
            >
              Analysis Progress
            </h2>

            {[
              [
                'done',
                'Analyzing local demographics',
                'Gathering census data for the 50km radius.',
              ],
              [
                'done',
                'Finding nearby competitors',
                'Mapping existing businesses and market gaps.',
              ],
              [
                'active',
                'Calculating financial feasibility',
                'Projecting CAPEX, OPEX, and break-even.',
              ],
              [
                'pending',
                'Generating final report',
                'Compiling visualizations and strategy.',
              ],
            ].map(([state, title, sub]) => (
              <div className="step-row" key={title}>
                <div className={`step-icon ${state}`}>
                  <span
                    className="material-symbols-outlined"
                    style={{ fontSize: 16 }}
                  >
                    {state === 'done'
                      ? 'check'
                      : state === 'active'
                        ? 'sync'
                        : 'radio_button_unchecked'}
                  </span>
                </div>

                <div>
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 14,
                    }}
                  >
                    {title}
                  </div>

                  <div className="label-sm muted">
                    {sub}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      ) : (

        <div className="card">

          {p.error && (
            <div
              className="error-box"
              style={{ marginBottom: 16 }}
            >
              {p.error}
            </div>
          )}

          {/* =====================================================
              STEP 1 — LOCATION
             ===================================================== */}

          {step === 0 && (
            <>
              <h2
                className="title-md"
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
              >
                Select Target Location

                <span className="badge blue">
                  <span
                    className="material-symbols-outlined"
                    style={{ fontSize: 14 }}
                  >
                    my_location
                  </span>

                  Detect GPS
                </span>
              </h2>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 16,
                }}
              >
                <div className="field">
                  <label>State</label>

                  <select
                    value={p.loc.state}
                    onChange={e => p.onStates(e.target.value)}
                  >
                    <option value="">
                      Select State
                    </option>

                    {p.states.map(s => (
                      <option key={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>District</label>

                  <select
                    value={p.loc.district}
                    disabled={!p.loc.state}
                    onChange={e =>
                      p.onDistricts(e.target.value)
                    }
                  >
                    <option value="">
                      Select District
                    </option>

                    {p.districts.map(d => (
                      <option key={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>Block / Taluka</label>

                  <select
                    value={p.loc.block}
                    disabled={!p.loc.district}
                    onChange={e =>
                      p.onBlocks(e.target.value)
                    }
                  >
                    <option value="">
                      Select Block
                    </option>

                    {p.blocks.map(b => (
                      <option key={b}>
                        {b}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="field">
                  <label>Village</label>

                  <select
                    value={p.loc.village}
                    disabled={!p.loc.block}
                    onChange={e =>
                      p.setLoc({
                        ...p.loc,
                        village: e.target.value,
                      })
                    }
                  >
                    <option value="">
                      Select Village
                    </option>

                    {p.villages.map(v => (
                      <option key={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </>
          )}

          {/* =====================================================
              STEP 2 — BUSINESS CATEGORY
             ===================================================== */}

          {step === 1 && (
            <>
              <h2 className="title-md">
                Choose Business Category
              </h2>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 12,
                }}
              >
                {SECTORS.map(([v, l]) => (
                  <button
                    key={v}
                    className="btn"
                    type="button"
                    style={{
                      background:
                        p.sector === v
                          ? 'var(--primary)'
                          : 'var(--surface-container-low)',
                      color:
                        p.sector === v
                          ? '#fff'
                          : 'var(--on-surface)',
                    }}
                    onClick={() => p.setSector(v)}
                  >
                    {l}
                  </button>
                ))}
              </div>

              {voiceText && (
                <div
                  className="card-low"
                  style={{ marginTop: 16 }}
                >
                  <div className="mono-label muted">
                    VOICE TRANSCRIPT
                  </div>

                  <div style={{ marginTop: 6 }}>
                    {voiceText}
                  </div>
                </div>
              )}
            </>
          )}

          {/* =====================================================
              STEP 3 — FINANCING + APPLICANT PROFILE
             ===================================================== */}

          {step === 2 && (
            <>
              <h2 className="title-md">
                Financing — Margin Money
              </h2>

              <div
                className="field"
                style={{ maxWidth: 400 }}
              >
                <label>
                  Available Margin Capital (₹) — your 10% contribution
                </label>

                <input
                  type="number"
                  min={1000}
                  step={1000}
                  value={p.margin}
                  onChange={e =>
                    p.setMargin(Number(e.target.value))
                  }
                />
              </div>

              <div
                className="card-low"
                style={{ maxWidth: 400 }}
              >
                <div className="mono-label muted">
                  Indicative Structure
                </div>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginTop: 8,
                  }}
                >
                  <span>Project Cost</span>

                  <b>
                    ₹{(p.margin * 10).toLocaleString('en-IN')}
                  </b>
                </div>

                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>Max Loan (90%)</span>

                  <b>
                    ₹{(p.margin * 9).toLocaleString('en-IN')}
                  </b>
                </div>
              </div>

              {/* Applicant Profile */}

              <div style={{ marginTop: 28 }}>
                <h3
                  className="title-md"
                  style={{
                    fontSize: 18,
                    marginBottom: 4,
                  }}
                >
                  Applicant Profile
                </h3>

                <p
                  className="muted label-sm"
                  style={{ margin: '0 0 14px' }}
                >
                  These details help GramAI identify government schemes
                  you may qualify for.
                </p>

                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 12,
                  }}
                >

                  {/* Woman */}

                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      cursor: 'pointer',
                      padding: '10px 12px',
                      borderRadius: 10,
                      background:
                        'var(--surface-container-low)',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isWoman}
                      onChange={e =>
                        setIsWoman(e.target.checked)
                      }
                    />

                    <span>
                      <b>Woman applicant</b>

                      <span
                        className="muted"
                        style={{
                          display: 'block',
                          fontSize: 12,
                        }}
                      >
                        Helps identify women-focused financing options.
                      </span>
                    </span>
                  </label>

                  {/* SC/ST */}

                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      cursor: 'pointer',
                      padding: '10px 12px',
                      borderRadius: 10,
                      background:
                        'var(--surface-container-low)',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isSCST}
                      onChange={e =>
                        setIsSCST(e.target.checked)
                      }
                    />

                    <span>
                      <b>SC/ST applicant</b>

                      <span
                        className="muted"
                        style={{
                          display: 'block',
                          fontSize: 12,
                        }}
                      >
                        Helps identify category-specific schemes.
                      </span>
                    </span>
                  </label>

                  {/* Previous Tarun repayment */}

                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      cursor: 'pointer',
                      padding: '10px 12px',
                      borderRadius: 10,
                      background:
                        'var(--surface-container-low)',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={previousTarunRepaid}
                      onChange={e =>
                        setPreviousTarunRepaid(
                          e.target.checked
                        )
                      }
                    />

                    <span>
                      <b>
                        Previously repaid a Tarun MUDRA loan
                      </b>

                      <span
                        className="muted"
                        style={{
                          display: 'block',
                          fontSize: 12,
                        }}
                      >
                        Important for checking Tarun Plus eligibility.
                      </span>
                    </span>
                  </label>

                </div>
              </div>
            </>
          )}

          {/* =====================================================
              STEP 4 — REVIEW
             ===================================================== */}

          {step === 3 && (
            <>
              <h2 className="title-md">
                Review & Run
              </h2>

              <div
                className="card-low"
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, 1fr)',
                  gap: 12,
                }}
              >
                <div>
                  <div className="mono-label muted">
                    Location
                  </div>

                  <b>
                    {p.loc.village || p.loc.block},{' '}
                    {p.loc.district}
                  </b>
                </div>

                <div>
                  <div className="mono-label muted">
                    Sector
                  </div>

                  <b
                    style={{
                      textTransform: 'capitalize',
                    }}
                  >
                    {p.sector.replace('_', ' ')}
                  </b>
                </div>

                <div>
                  <div className="mono-label muted">
                    Margin
                  </div>

                  <b>
                    ₹{p.margin.toLocaleString('en-IN')}
                  </b>
                </div>

                <div>
                  <div className="mono-label muted">
                    Project Cost
                  </div>

                  <b>
                    ₹{(p.margin * 10).toLocaleString('en-IN')}
                  </b>
                </div>
              </div>

              {/* Applicant profile summary */}

              <div
                className="card-low"
                style={{ marginTop: 16 }}
              >
                <div className="mono-label muted">
                  Applicant Profile
                </div>

                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 8,
                    marginTop: 10,
                  }}
                >
                  {isWoman && (
                    <span className="badge blue">
                      Woman applicant
                    </span>
                  )}

                  {isSCST && (
                    <span className="badge blue">
                      SC/ST applicant
                    </span>
                  )}

                  {previousTarunRepaid && (
                    <span className="badge blue">
                      Previous Tarun repayment
                    </span>
                  )}

                  {!isWoman &&
                    !isSCST &&
                    !previousTarunRepaid && (
                      <span className="muted label-sm">
                        No special applicant criteria selected
                      </span>
                    )}
                </div>
              </div>

              <div
                className="muted label-sm"
                style={{ marginTop: 12 }}
              >
                GramAI will use this profile along with your
                location, business category and financing requirements
                to match relevant government schemes.
              </div>
            </>
          )}

          {/* Navigation */}

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginTop: 24,
            }}
          >
            <button
              className="btn btn-outline"
              type="button"
              disabled={step === 0}
              onClick={() =>
                setStep(s => s - 1)
              }
            >
              ← Back
            </button>

            {step < 3 ? (

              <button
                className="btn"
                type="button"
                disabled={!canNext}
                onClick={() =>
                  setStep(s => s + 1)
                }
              >
                Continue →
              </button>

            ) : (

              <button
                className="btn"
                type="button"
                disabled={!canNext || p.loading}
                onClick={() =>
                  p.onRun(applicantProfile)
                }
              >
                🚀 Run AI Analysis
              </button>

            )}
          </div>

        </div>
      )}
    </div>
  )
}