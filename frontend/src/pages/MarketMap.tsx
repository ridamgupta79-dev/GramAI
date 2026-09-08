import { DashboardPayload } from '../dashboardApi'

interface Props {
  payload: DashboardPayload | null
}

export default function MarketMap({ payload }: Props) {
  const insights =
    payload?.sections?.analysis?.data ?? {}

  const market = insights.market ?? {}

  const competitors = Number(
    market.competitors_within_10km ?? 0
  )

  const customers = Number(
    market.target_customer_base ?? 0
  )

  const population = Number(
    market.population ?? 0
  )

  const radius = Number(
    market.radius_km ?? 10
  )

  const competition =
    market.competition_level ?? '—'

  const pricingPressure =
    market.pricing_pressure ?? '—'

  const opportunity =
    market.market_opportunity ?? '—'

  const village =
    payload?.context?.location?.village ||
    'Selected Village'

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 24,
      }}
    >
      {/* Header */}
      <div>
        <span className="badge blue">
          Hyper-Local Intelligence
        </span>

        <h1
          className="headline-lg"
          style={{ margin: '8px 0 0' }}
        >
          Market Intelligence Map
        </h1>

        <p
          className="muted label-sm"
          style={{ maxWidth: 650 }}
        >
          Understand the local business environment around{' '}
          <strong>{village}</strong> using competitor density,
          estimated customers and market signals.
        </p>
      </div>

      {/* Demo data notice */}
      <div
        className="card-low"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}
      >
        <span
          className="material-symbols-outlined"
          style={{ color: 'var(--primary)' }}
        >
          info
        </span>

        <div>
          <div style={{ fontWeight: 700 }}>
            Prototype GIS View
          </div>

          <div className="label-sm muted">
            Location intelligence is currently powered by
            synthetic demo GIS data for this prototype.
          </div>
        </div>
      </div>

      <div className="bento">

        {/* Map visualization */}
        <div
          className="card col-8"
          style={{
            minHeight: 480,
            position: 'relative',
            overflow: 'hidden',
            background:
              'var(--surface-container-low)',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              position: 'relative',
              zIndex: 2,
            }}
          >
            <div>
              <h2
                className="title-md"
                style={{ margin: 0 }}
              >
                {village}
              </h2>

              <div className="label-sm muted">
                {radius} km analysis radius
              </div>
            </div>

            <span
              className="badge"
              style={{
                background:
                  'var(--surface-container-high)',
              }}
            >
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 15 }}
              >
                location_on
              </span>
              Local Area
            </span>
          </div>

          {/* Map-style background */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              opacity: 0.45,
              backgroundImage:
                'linear-gradient(var(--outline-variant) 1px, transparent 1px), linear-gradient(90deg, var(--outline-variant) 1px, transparent 1px)',
              backgroundSize: '48px 48px',
            }}
          />

          {/* Analysis radius */}
          <div
            style={{
              position: 'absolute',
              width: 330,
              height: 330,
              borderRadius: '50%',
              border:
                '2px dashed var(--primary)',
              left: '50%',
              top: '55%',
              transform:
                'translate(-50%, -50%)',
              opacity: 0.55,
            }}
          />

          {/* Center business */}
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: '55%',
              transform:
                'translate(-50%, -50%)',
              width: 72,
              height: 72,
              borderRadius: '50%',
              background:
                'var(--primary)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow:
                '0 8px 24px rgba(0,0,0,.18)',
              zIndex: 3,
            }}
          >
            <span
              className="material-symbols-outlined"
              style={{ fontSize: 32 }}
            >
              storefront
            </span>
          </div>

          {/* Competitor markers */}
          {Array.from({
            length: Math.min(competitors, 8),
          }).map((_, index) => {
            const positions = [
              { left: '31%', top: '42%' },
              { left: '67%', top: '38%' },
              { left: '72%', top: '65%' },
              { left: '35%', top: '72%' },
              { left: '52%', top: '30%' },
              { left: '26%', top: '60%' },
              { left: '76%', top: '52%' },
              { left: '48%', top: '78%' },
            ]

            const position =
              positions[index]

            return (
              <div
                key={index}
                title={`Competitor ${index + 1}`}
                style={{
                  position: 'absolute',
                  ...position,
                  width: 34,
                  height: 34,
                  borderRadius: '50%',
                  background:
                    'var(--surface-container-high)',
                  border:
                    '2px solid var(--tertiary-fixed-dim)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  zIndex: 4,
                }}
              >
                <span
                  className="material-symbols-outlined"
                  style={{
                    fontSize: 18,
                    color:
                      'var(--tertiary-fixed-dim)',
                  }}
                >
                  store
                </span>
              </div>
            )
          })}

          {/* Legend */}
          <div
            style={{
              position: 'absolute',
              bottom: 18,
              left: 18,
              display: 'flex',
              gap: 16,
              padding: '8px 12px',
              borderRadius: 10,
              background:
                'var(--surface-container)',
              zIndex: 5,
            }}
          >
            <span className="label-sm">
              🏪 Competitor
            </span>

            <span className="label-sm">
              📍 Your Business
            </span>
          </div>
        </div>

        {/* Market metrics */}
        <div
          className="card col-4"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          <h2
            className="title-md"
            style={{ margin: 0 }}
          >
            Local Market Signals
          </h2>

          <div className="stat-mini">
            <div className="mono-label muted">
              Nearby Competitors
            </div>

            <div className="title-md">
              {competitors}
            </div>

            <div className="label-sm muted">
              within {radius} km
            </div>
          </div>

          <div className="stat-mini">
            <div className="mono-label muted">
              Estimated Population
            </div>

            <div className="title-md">
              {population.toLocaleString('en-IN')}
            </div>

            <div className="label-sm muted">
              local population
            </div>
          </div>

          <div className="stat-mini">
            <div className="mono-label muted">
              Target Customers
            </div>

            <div className="title-md">
              {customers.toLocaleString('en-IN')}
            </div>

            <div className="label-sm muted">
              estimated customer base
            </div>
          </div>

          <div className="stat-mini">
            <div className="mono-label muted">
              Competition
            </div>

            <div className="title-md">
              {competition}
            </div>
          </div>

          <div className="stat-mini">
            <div className="mono-label muted">
              Pricing Pressure
            </div>

            <div className="title-md">
              {pricingPressure}
            </div>
          </div>

          <div className="stat-mini">
            <div className="mono-label muted">
              Market Opportunity
            </div>

            <div className="title-md">
              {opportunity}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}