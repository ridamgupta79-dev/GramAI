import { useEffect, useState } from 'react'
import { DashboardPayload } from '../dashboardApi'
import { Page } from '../App'
import { fetchMyReports } from '../api'

const inr = (n: number) =>
  '₹' +
  Number(n ?? 0).toLocaleString('en-IN', {
    maximumFractionDigits: 0,
  })

interface Props {
  payload: DashboardPayload | null
  loading: boolean
  error: string
  states: string[]
  districts: string[]
  blocks: string[]
  villages: string[]
  loc: {
    state: string
    district: string
    block: string
    village: string
  }
  setLoc: (l: any) => void
  onStates: (s: string) => void
  onDistricts: (d: string) => void
  onBlocks: (b: string) => void
  sector: string
  setSector: (s: string) => void
  margin: number
  setMargin: (m: number) => void
  onRun: () => void
  onNavigate: (p: Page) => void
  userName: string
}

/* ============================================================
   VIABILITY GAUGE
   ============================================================ */

function Gauge({ score }: { score: number }) {
  const safeScore = Math.max(0, Math.min(100, score))
  const C = 2 * Math.PI * 54
  const offset = C * (1 - safeScore / 100)

  return (
    <div
      style={{
        position: 'relative',
        width: 180,
        height: 180,
        margin: '0 auto',
      }}
    >
      <svg width="180" height="180" viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="var(--surface-container-highest)"
          strokeWidth="8"
        />

        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="var(--primary)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={C}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
        />
      </svg>

      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ fontSize: 36, fontWeight: 800 }}>
          {safeScore}
          <span style={{ fontSize: 18 }}>%</span>
        </div>

        <div
          className="mono-label"
          style={{ color: 'var(--secondary)' }}
        >
          {safeScore >= 75
            ? 'EXCELLENT'
            : safeScore >= 50
              ? 'PROMISING'
              : 'RISKY'}
        </div>
      </div>
    </div>
  )
}

/* ============================================================
   SMALL STAT CARD
   ============================================================ */

function Stat({
  label,
  value,
  sub,
}: {
  label: string
  value: string
  sub?: string
}) {
  return (
    <div
      className="stat-mini"
      style={{
        minHeight: 90,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
      }}
    >
      <div className="mono-label muted">{label}</div>

      <div
        className="title-md"
        style={{
          marginTop: 6,
          fontWeight: 800,
        }}
      >
        {value}
      </div>

      {sub && (
        <div
          className="label-sm muted"
          style={{ marginTop: 2 }}
        >
          {sub}
        </div>
      )}
    </div>
  )
}

/* ============================================================
   HOME
   ============================================================ */

export default function Home(p: Props) {
  const [reports, setReports] = useState<any[]>([])

  useEffect(() => {
    fetchMyReports()
      .then(setReports)
      .catch(() => {})
  }, [p.payload])

  const insights =
    p.payload?.sections?.analysis?.data ?? {}

  const loan = insights.loan_eligibility ?? {}
  const market = insights.market ?? {}
  const risk = insights.risk_profile ?? {}

  const score = Number(
    insights.viability_score ?? 0,
  )

  const competitors = Number(
    market.competitors_within_10km ?? 0,
  )

  const population = Number(
    market.population_within_10km ?? 0,
  )

  const targetCustomers = Number(
    market.target_customer_base ?? 0,
  )

  const demandRatio =
    population > 0
      ? targetCustomers / population
      : 0

  const demandLabel =
    demandRatio >= 0.4
      ? 'High'
      : demandRatio >= 0.2
        ? 'Medium'
        : 'Low'

  const competitionLabel =
    competitors <= 3
      ? 'Low'
      : competitors <= 8
        ? 'Medium'
        : 'High'

  const recommendedScheme =
    loan.scheme ?? 'No scheme matched'

  const loanAmount = Number(
    loan.loan_amount ?? 0,
  )

  const emi = Number(
    loan.emi ?? 0,
  )

  const riskLevel =
    risk.overall ??
    risk.level ??
    '—'

  const hasAnalysis = Boolean(p.payload)

  const rawLocation = p.payload?.context?.location

  const locationText =
    typeof rawLocation === 'string'
      ? rawLocation
      : rawLocation &&
          typeof rawLocation === 'object'
        ? [
            rawLocation.village,
            rawLocation.block,
            rawLocation.district,
            rawLocation.state,
          ]
            .filter(Boolean)
            .join(', ')
        : p.loc.village ||
          p.loc.block ||
          'Your selected location'

  const sectorText =
    p.payload?.context?.sector ||
    p.sector ||
    'Business'

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 24,
      }}
    >

      {/* ======================================================
          HEADER
         ====================================================== */}

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-end',
          gap: 20,
        }}
      >
        <div>
          <div className="mono-label muted">
            GRAMAI BUSINESS INTELLIGENCE
          </div>

          <h1
            className="display-lg"
            style={{ margin: '6px 0 0' }}
          >
            Hello, {p.userName || 'there'}.
          </h1>

          <p
            className="headline-lg muted"
            style={{ margin: '4px 0 0' }}
          >
            {hasAnalysis
              ? 'Your latest business intelligence is ready.'
              : 'Turn a business idea into a data-backed decision.'}
          </p>
        </div>

        <button
          className="btn"
          onClick={() => p.onNavigate('new')}
          disabled={p.loading}
        >
          <span className="material-symbols-outlined">
            add
          </span>
          New Analysis
        </button>
      </div>

      {/* ======================================================
          ERROR
         ====================================================== */}

      {p.error && (
        <div className="error-box">
          {p.error}
        </div>
      )}

      {/* ======================================================
          ACTIVE ANALYSIS BANNER
         ====================================================== */}

      {p.loading && (
        <div
          className="card"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 16,
            borderLeft: '4px solid var(--primary)',
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{
              color: 'var(--primary)',
              fontSize: 30,
            }}
          >
            auto_awesome
          </span>

          <div>
            <div style={{ fontWeight: 800 }}>
              GramAI is analysing your business
            </div>

            <div className="label-sm muted">
              Market, competition, financial feasibility and
              government schemes are being evaluated.
            </div>
          </div>
        </div>
      )}

      {/* ======================================================
          NO ANALYSIS — PRIMARY CTA
         ====================================================== */}

      {!hasAnalysis && !p.loading && (
        <div
          className="card-primary"
          style={{
            padding: 32,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 24,
          }}
        >
          <div>
            <div
              className="mono-label"
              style={{ opacity: 0.8 }}
            >
              START WITH YOUR IDEA
            </div>

            <h2
              className="headline-lg"
              style={{
                color: '#fff',
                margin: '8px 0',
              }}
            >
              Is your business idea viable here?
            </h2>

            <p
              style={{
                color: 'var(--primary-fixed-dim)',
                margin: 0,
                maxWidth: 620,
              }}
            >
              GramAI combines local market signals, competition,
              financial feasibility and government schemes to help
              you make a better business decision.
            </p>
          </div>

          <button
            className="btn"
            onClick={() => p.onNavigate('new')}
            style={{
              background: '#fff',
              color: 'var(--primary)',
              whiteSpace: 'nowrap',
            }}
          >
            Start Analysis
            <span className="material-symbols-outlined">
              arrow_forward
            </span>
          </button>
        </div>
      )}

      {/* ======================================================
          MAIN ANALYSIS DASHBOARD
         ====================================================== */}

      {hasAnalysis && (
        <>
          {/* Context strip */}

          <div
            className="card-low"
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              gap: 20,
              padding: '14px 18px',
            }}
          >
            <div>
              <div className="mono-label muted">
                LOCATION
              </div>
              <b>{locationText}</b>
            </div>

            <div
              style={{
                width: 1,
                height: 32,
                background:
                  'var(--surface-container-highest)',
              }}
            />

            <div>
              <div className="mono-label muted">
                BUSINESS
              </div>
              <b style={{ textTransform: 'capitalize' }}>
                {String(sectorText).replace(/_/g, ' ')}
              </b>
            </div>

            <div style={{ marginLeft: 'auto' }}>
              <span className="badge green">
                <span
                  className="material-symbols-outlined"
                  style={{ fontSize: 14 }}
                >
                  verified
                </span>
                Analysis Complete
              </span>
            </div>
          </div>

          <div className="bento">

            {/* =================================================
                VIABILITY
               ================================================= */}

            <div
              className="card col-4"
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 14,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div className="mono-label muted">
                    DECISION SIGNAL
                  </div>

                  <h2
                    className="title-md"
                    style={{ margin: '4px 0 0' }}
                  >
                    Viability Score
                  </h2>
                </div>

                <span
                  className="material-symbols-outlined"
                  style={{
                    color: 'var(--primary)',
                    fontSize: 28,
                  }}
                >
                  analytics
                </span>
              </div>

              <Gauge score={score} />

              <div
                className="label-sm muted"
                style={{
                  textAlign: 'center',
                  lineHeight: 1.5,
                }}
              >
                Combined signal from market,
                financial feasibility and risk indicators.
              </div>
            </div>

            {/* =================================================
                AI ADVISOR
               ================================================= */}

            <div
              className="card-primary col-5"
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: 20,
              }}
            >
              <div>
                <span
                  className="badge"
                  style={{
                    background: 'rgba(255,255,255,.15)',
                    color: '#fff',
                  }}
                >
                  <span
                    className="material-symbols-outlined"
                    style={{ fontSize: 14 }}
                  >
                    psychology
                  </span>
                  AI Advisor
                </span>

                <h2
                  className="headline-lg"
                  style={{
                    margin: '18px 0 8px',
                    color: '#fff',
                  }}
                >
                  Your business,
                  <br />
                  explained simply.
                </h2>

                <p
                  style={{
                    color: 'var(--primary-fixed-dim)',
                    margin: 0,
                    lineHeight: 1.5,
                  }}
                >
                  Ask GramAI about pricing, competition,
                  financing, schemes, risk or market demand.
                </p>
              </div>

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                }}
              >
                {[
                  'Suggest local pricing strategies',
                  'Find relevant government schemes',
                  'Explain my business risks',
                ].map(text => (
                  <button
                    key={text}
                    className="btn btn-sm"
                    style={{
                      background: 'rgba(255,255,255,.12)',
                      color: '#fff',
                      justifyContent: 'space-between',
                    }}
                    onClick={() =>
                      p.onNavigate('advisor')
                    }
                  >
                    {text}

                    <span className="material-symbols-outlined">
                      arrow_forward
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* =================================================
                QUICK ACTIONS
               ================================================= */}

            <div
              className="col-3"
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
              }}
            >
              {[
                {
                  icon: 'map',
                  title: 'Market Map',
                  sub: 'Explore local competition',
                  page: 'market' as Page,
                },
                {
                  icon: 'description',
                  title: 'Reports',
                  sub: 'View your business reports',
                  page: 'reports' as Page,
                },
                {
                  icon: 'psychology',
                  title: 'AI Advisor',
                  sub: 'Ask about your business',
                  page: 'advisor' as Page,
                },
              ].map(action => (
                <button
                  key={action.title}
                  className="card-tile"
                  onClick={() =>
                    p.onNavigate(action.page)
                  }
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    cursor: 'pointer',
                    border: 'none',
                    textAlign: 'left',
                  }}
                >
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 14,
                      background: 'var(--primary)',
                      color: '#fff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    <span className="material-symbols-outlined">
                      {action.icon}
                    </span>
                  </div>

                  <div>
                    <div style={{ fontWeight: 800 }}>
                      {action.title}
                    </div>

                    <div className="label-sm muted">
                      {action.sub}
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* =================================================
                MARKET SNAPSHOT
               ================================================= */}

            <div className="card col-8">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div className="mono-label muted">
                    HYPER-LOCAL INTELLIGENCE
                  </div>

                  <h2
                    className="title-md"
                    style={{ margin: '4px 0 0' }}
                  >
                    Market Snapshot
                  </h2>

                  <div className="label-sm muted">
                    Within {market.radius_km ?? 10} km of
                    the selected location
                  </div>
                </div>

                <button
                  className="btn btn-sm btn-outline"
                  onClick={() =>
                    p.onNavigate('market')
                  }
                >
                  Open Map
                  <span className="material-symbols-outlined">
                    map
                  </span>
                </button>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns:
                    'repeat(4, 1fr)',
                  gap: 10,
                  marginTop: 18,
                }}
              >
                <Stat
                  label="CUSTOMERS"
                  value={targetCustomers.toLocaleString('en-IN')}
                  sub="estimated target base"
                />

                <Stat
                  label="COMPETITORS"
                  value={String(competitors)}
                  sub="within 10 km"
                />

                <Stat
                  label="DEMAND"
                  value={demandLabel}
                  sub="local signal"
                />

                <Stat
                  label="COMPETITION"
                  value={competitionLabel}
                  sub="business density"
                />
              </div>

              <div
                className="card-low"
                style={{
                  marginTop: 14,
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: 16,
                }}
              >
                <div>
                  <div className="mono-label muted">
                    MARKET OPPORTUNITY
                  </div>

                  <b>
                    {market.market_opportunity ?? '—'}
                  </b>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div className="mono-label muted">
                    PRICING PRESSURE
                  </div>

                  <b>
                    {market.pricing_pressure ?? '—'}
                  </b>
                </div>
              </div>
            </div>

            {/* =================================================
                FINANCING
               ================================================= */}

            <div className="card col-4">
              <div className="mono-label muted">
                FINANCIAL STRUCTURE
              </div>

              <h2
                className="title-md"
                style={{ margin: '4px 0 18px' }}
              >
                Financing Match
              </h2>

              <div
                style={{
                  padding: 14,
                  borderRadius: 14,
                  background:
                    'var(--surface-container-low)',
                }}
              >
                <div className="label-sm muted">
                  RECOMMENDED SCHEME
                </div>

                <div
                  style={{
                    fontSize: 20,
                    fontWeight: 800,
                    color: 'var(--primary)',
                    marginTop: 4,
                  }}
                >
                  {recommendedScheme}
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 10,
                  marginTop: 12,
                }}
              >
                <Stat
                  label="LOAN"
                  value={inr(loanAmount)}
                />

                <Stat
                  label="EMI"
                  value={inr(emi)}
                  sub="per month"
                />
              </div>

              <button
                className="btn btn-outline"
                style={{
                  width: '100%',
                  marginTop: 12,
                }}
                onClick={() =>
                  p.onNavigate('reports')
                }
              >
                View Full Report
              </button>
            </div>

            {/* =================================================
                RISK
               ================================================= */}

            <div className="card col-4">
              <div className="mono-label muted">
                RISK INTELLIGENCE
              </div>

              <h2
                className="title-md"
                style={{ margin: '4px 0 18px' }}
              >
                Business Risk
              </h2>

              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: 14,
                  borderRadius: 14,
                  background:
                    'var(--surface-container-low)',
                }}
              >
                <span
                  className="material-symbols-outlined"
                  style={{
                    color: 'var(--primary)',
                    fontSize: 28,
                  }}
                >
                  shield
                </span>

                <div>
                  <div className="label-sm muted">
                    OVERALL RISK
                  </div>

                  <div
                    style={{
                      fontWeight: 800,
                      fontSize: 20,
                    }}
                  >
                    {String(riskLevel)}
                  </div>
                </div>
              </div>

              <p
                className="label-sm muted"
                style={{
                  lineHeight: 1.5,
                  margin: '14px 0',
                }}
              >
                GramAI evaluates operational, market and
                financial risk signals before giving its
                recommendation.
              </p>

              <button
                className="btn btn-outline"
                style={{ width: '100%' }}
                onClick={() =>
                  p.onNavigate('advisor')
                }
              >
                Ask AI About Risk
              </button>
            </div>

            {/* =================================================
                NEW ANALYSIS
               ================================================= */}

            <div className="card col-8">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 20,
                }}
              >
                <div>
                  <div className="mono-label muted">
                    EXPLORE ANOTHER IDEA
                  </div>

                  <h2
                    className="title-md"
                    style={{ margin: '4px 0 4px' }}
                  >
                    Test a different business
                  </h2>

                  <p
                    className="label-sm muted"
                    style={{ margin: 0 }}
                  >
                    Compare another location, sector or
                    financing requirement.
                  </p>
                </div>

                <button
                  className="btn"
                  onClick={() =>
                    p.onNavigate('new')
                  }
                >
                  New Analysis
                  <span className="material-symbols-outlined">
                    arrow_forward
                  </span>
                </button>
              </div>
            </div>

            {/* =================================================
                RECENT REPORTS
               ================================================= */}

            <div className="card col-4">
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div className="mono-label muted">
                    HISTORY
                  </div>

                  <h2
                    className="title-md"
                    style={{ margin: '4px 0 0' }}
                  >
                    Recent Reports
                  </h2>
                </div>

                <button
                  className="btn btn-sm btn-ghost"
                  onClick={() =>
                    p.onNavigate('reports')
                  }
                >
                  View All
                </button>
              </div>

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8,
                  marginTop: 14,
                }}
              >
                {reports
                  .slice(0, 4)
                  .map(r => (
                    <div
                      key={r.id}
                      className="card-low"
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        gap: 10,
                      }}
                    >
                      <div style={{ minWidth: 0 }}>
                        <div
                          style={{
                            fontWeight: 700,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {r.title || r.id}
                        </div>

                        <div className="label-sm muted">
                          {r.created_at
                            ? new Date(
                                r.created_at,
                              ).toLocaleDateString(
                                'en-IN',
                              )
                            : 'Saved report'}
                        </div>
                      </div>

                      <span className="badge green">
                        Saved
                      </span>
                    </div>
                  ))}

                {reports.length === 0 && (
                  <div
                    className="card-low"
                    style={{
                      textAlign: 'center',
                      padding: 20,
                    }}
                  >
                    <span
                      className="material-symbols-outlined muted"
                      style={{ fontSize: 30 }}
                    >
                      description
                    </span>

                    <p
                      className="muted label-sm"
                      style={{ margin: '8px 0 0' }}
                    >
                      Your saved reports will appear here.
                    </p>
                  </div>
                )}
              </div>
            </div>

          </div>

          {/* ==================================================
              SAFETY / DECISION NOTE
             ================================================== */}

          <div
            className="card-low"
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 10,
            }}
          >
            <span
              className="material-symbols-outlined"
              style={{
                color: 'var(--primary)',
                fontSize: 20,
              }}
            >
              info
            </span>

            <div className="label-sm muted">
              <b style={{ color: 'var(--on-surface)' }}>
                Decision support, not a guarantee.
              </b>{' '}
              Market estimates, financial projections and scheme
              matches are indicative. Final lending and government
              scheme eligibility must be verified with the relevant
              institution.
            </div>
          </div>
        </>
      )}

      {/* ======================================================
          FOOTER
         ====================================================== */}

      <div
        className="label-sm muted"
        style={{
          textAlign: 'center',
          padding: '4px 0 12px',
        }}
      >
        GramAI · Hyper-local business intelligence for rural
        entrepreneurs
      </div>
    </div>
  )
}