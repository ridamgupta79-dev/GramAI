import { useEffect, useState } from 'react'
import { api } from '../api'

interface Scheme {
  slug: string
  name: string
  level: string
  min_loan?: number
  max_loan?: number
  interest_guidance?: string
  description_md?: string
  documents_required?: string[]
  tiers?: string[]
  source_url?: string
}

function formatMoney(value?: number) {
  if (value === undefined || value === null) {
    return 'As per scheme norms'
  }

  return `₹${value.toLocaleString('en-IN')}`
}

function cleanDescription(text?: string) {
  if (!text) {
    return 'Scheme details and eligibility depend on the applicable government guidelines.'
  }

  return text.replace(/\*\*/g, '')
}

function getEligibilityPoints(scheme: Scheme) {
  const points: string[] = []

  points.push('Eligibility is subject to the applicable scheme guidelines.')

  if (
    scheme.min_loan !== undefined &&
    scheme.max_loan !== undefined
  ) {
    points.push(
      `Loan range: ${formatMoney(scheme.min_loan)} – ${formatMoney(
        scheme.max_loan,
      )}`,
    )
  }

  if (scheme.slug === 'mudra' || scheme.slug === 'pmmy') {
    points.push(
      'Designed for eligible micro-enterprises and income-generating activities.',
    )
  }

  if (scheme.slug === 'stand_up_india') {
    points.push(
      'Designed for eligible SC/ST and women entrepreneurs establishing greenfield enterprises.',
    )
  }

  if (scheme.slug === 'mahila_samriddhi') {
    points.push(
      'Designed for eligible women beneficiaries under the applicable channelising-agency framework.',
    )
  }

  if (
    scheme.slug === 'micro_finance_sca' ||
    scheme.slug === 'term_loan_sca'
  ) {
    points.push(
      'Eligibility is evaluated under the applicable State Channelising Agency framework.',
    )
  }

  if (scheme.slug === 'pmegp') {
    points.push(
      'Available for eligible new micro-enterprises subject to PMEGP rules.',
    )
  }

  return points
}

function getBenefits(scheme: Scheme) {
  const benefits: string[] = []

  if (scheme.interest_guidance) {
    benefits.push(scheme.interest_guidance)
  }

  if (scheme.level) {
    benefits.push(
      `${scheme.level === 'central' ? 'Central' : 'State'} government-linked scheme`,
    )
  }

  if (
    scheme.slug === 'mudra' ||
    scheme.slug === 'pmmy'
  ) {
    benefits.push(
      'Multiple financing tiers are available based on the loan requirement.',
    )
  }

  if (scheme.slug === 'pmegp') {
    benefits.push(
      'Credit-linked margin-money subsidy may be available subject to applicable rules.',
    )
  }

  if (scheme.slug === 'stand_up_india') {
    benefits.push(
      'Supports eligible SC/ST and women entrepreneurs with larger greenfield financing.',
    )
  }

  if (scheme.slug === 'micro_finance_sca') {
    benefits.push(
      'Concessional financing framework for smaller projects.',
    )
  }

  if (scheme.slug === 'term_loan_sca') {
    benefits.push(
      'Concessional term-loan support for larger eligible projects.',
    )
  }

  if (scheme.slug === 'mahila_samriddhi') {
    benefits.push(
      'Concessional financing support for eligible women beneficiaries.',
    )
  }

  return benefits
}

export default function Schemes() {
  const [schemes, setSchemes] = useState<Scheme[]>([])
  const [selectedSlug, setSelectedSlug] = useState<string>('')
  const [selected, setSelected] = useState<Scheme | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => {
    async function loadSchemes() {
      try {
        setLoading(true)

        const response = await api.get('/schemes')
        const items: Scheme[] = response.data ?? []

        setSchemes(items)

        if (items.length > 0) {
          setSelectedSlug(items[0].slug)
        }
      } catch (error) {
        console.error('Failed to load schemes:', error)
      } finally {
        setLoading(false)
      }
    }

    loadSchemes()
  }, [])

  useEffect(() => {
    if (!selectedSlug) return

    async function loadSchemeDetails() {
      try {
        setDetailLoading(true)

        const response = await api.get(
          `/schemes/${selectedSlug}`,
        )

        setSelected(response.data)
      } catch (error) {
        console.error(
          'Failed to load scheme details:',
          error,
        )

        /*
         * Fallback to the scheme from the list endpoint
         * so the page does not become empty if the detail
         * request fails.
         */
        const fallback =
          schemes.find(s => s.slug === selectedSlug) ?? null

        setSelected(fallback)
      } finally {
        setDetailLoading(false)
      }
    }

    loadSchemeDetails()
  }, [selectedSlug, schemes])

  function handleSchemeChange(slug: string) {
    if (slug === selectedSlug) return

    setSelectedSlug(slug)
  }

  function handleApply() {
    if (!selected?.source_url) return

    window.open(
      selected.source_url,
      '_blank',
      'noopener,noreferrer',
    )
  }

  const eligibilityPoints = selected
    ? getEligibilityPoints(selected)
    : []

  const benefits = selected
    ? getBenefits(selected)
    : []

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 24,
      }}
    >
      {/* =====================================================
          Header
          ===================================================== */}
      <div>
        <span className="badge blue">
          Financial Support
        </span>

        <h1
          className="headline-lg"
          style={{
            margin: '8px 0 0',
          }}
        >
          {selected?.name ?? 'Government Schemes'}
        </h1>

        <p
          className="muted label-sm"
          style={{
            maxWidth: 760,
            lineHeight: 1.6,
            marginTop: 8,
          }}
        >
          {cleanDescription(selected?.description_md)}
        </p>
      </div>

      {/* =====================================================
          Scheme selector
          ===================================================== */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
        }}
      >
        {loading ? (
          <div className="muted">
            Loading government schemes…
          </div>
        ) : (
          schemes.map(scheme => {
            const active =
              selectedSlug === scheme.slug

            return (
              <button
                key={scheme.slug}
                className="suggest-chip"
                type="button"
                onClick={() =>
                  handleSchemeChange(scheme.slug)
                }
                style={{
                  background: active
                    ? 'var(--primary)'
                    : undefined,
                  color: active
                    ? '#fff'
                    : undefined,
                  cursor: 'pointer',
                }}
              >
                {scheme.name}
              </button>
            )
          })
        )}
      </div>

      {/* =====================================================
          Loading selected scheme
          ===================================================== */}
      {detailLoading && (
        <div
          className="card"
          style={{
            textAlign: 'center',
            padding: 32,
          }}
        >
          <div
            className="muted"
            style={{
              fontSize: 14,
            }}
          >
            Loading scheme details…
          </div>
        </div>
      )}

      {/* =====================================================
          Selected scheme details
          ===================================================== */}
      {selected && !detailLoading && (
        <div
          className="bento"
          key={selected.slug}
        >
          {/* =================================================
              Eligibility
              ================================================= */}
          <div className="card col-6">
            <h2
              className="title-md"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  color: 'var(--secondary)',
                }}
              >
                check_circle
              </span>

              Eligibility Criteria
            </h2>

            <ul
              className="muted"
              style={{
                lineHeight: 1.8,
                paddingLeft: 20,
                marginBottom: 0,
              }}
            >
              {eligibilityPoints.map(point => (
                <li key={point}>{point}</li>
              ))}
            </ul>
          </div>

          {/* =================================================
              Key benefits
              ================================================= */}
          <div className="card col-6">
            <h2
              className="title-md"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{
                  color: 'var(--primary)',
                }}
              >
                star
              </span>

              Key Benefits
            </h2>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
              }}
            >
              {benefits.map(benefit => (
                <div
                  key={benefit}
                  className="card-low"
                  style={{
                    lineHeight: 1.5,
                  }}
                >
                  ✓ {benefit}
                </div>
              ))}
            </div>
          </div>

          {/* =================================================
              Loan information
              ================================================= */}
          <div className="card col-12">
            <h2
              className="title-md"
              style={{
                marginTop: 0,
              }}
            >
              Scheme Overview
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns:
                  'repeat(3, minmax(0, 1fr))',
                gap: 12,
              }}
            >
              <div className="card-low">
                <div className="mono-label muted">
                  LEVEL
                </div>

                <div
                  style={{
                    fontWeight: 700,
                    marginTop: 4,
                    textTransform: 'capitalize',
                  }}
                >
                  {selected.level}
                </div>
              </div>

              <div className="card-low">
                <div className="mono-label muted">
                  LOAN RANGE
                </div>

                <div
                  style={{
                    fontWeight: 700,
                    marginTop: 4,
                  }}
                >
                  {formatMoney(selected.min_loan)}
                  {' – '}
                  {formatMoney(selected.max_loan)}
                </div>
              </div>

              <div className="card-low">
                <div className="mono-label muted">
                  INTEREST / TERMS
                </div>

                <div
                  style={{
                    fontWeight: 700,
                    marginTop: 4,
                    lineHeight: 1.4,
                  }}
                >
                  {selected.interest_guidance ??
                    'As per applicable norms'}
                </div>
              </div>
            </div>
          </div>

          {/* =================================================
              Documents
              ================================================= */}
          <div className="card col-12">
            <h2
              className="title-md"
              style={{
                marginTop: 0,
              }}
            >
              Documents Required
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns:
                  'repeat(3, minmax(0, 1fr))',
                gap: 12,
              }}
            >
              {(
                selected.documents_required ?? [
                  'Aadhaar Card',
                  'PAN Card',
                  'Business / Project Details',
                ]
              ).map(document => (
                <div
                  key={document}
                  className="card-low"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <span
                    className="material-symbols-outlined"
                    style={{
                      color: 'var(--primary)',
                    }}
                  >
                    badge
                  </span>

                  <div>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: 14,
                      }}
                    >
                      {document}
                    </div>

                    <div className="mono-label muted">
                      Check applicability
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* =================================================
                Actions
                ================================================= */}
            <div
              style={{
                display: 'flex',
                gap: 10,
                flexWrap: 'wrap',
                marginTop: 16,
              }}
            >
              <button
                className="btn"
                type="button"
                onClick={handleApply}
                disabled={!selected.source_url}
              >
                View Official Scheme
                <span
                  className="material-symbols-outlined"
                  style={{
                    fontSize: 18,
                  }}
                >
                  open_in_new
                </span>
              </button>

              <div
                className="mono-label muted"
                style={{
                  alignSelf: 'center',
                }}
              >
                Verify final eligibility and terms with
                the official scheme authority.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================
          Empty state
          ===================================================== */}
      {!loading && !selected && (
        <div
          className="card"
          style={{
            textAlign: 'center',
            padding: 40,
          }}
        >
          <h2 className="title-md">
            No scheme information available
          </h2>

          <p className="muted">
            Please try again or run a business analysis
            to get personalized scheme recommendations.
          </p>
        </div>
      )}
    </div>
  )
}