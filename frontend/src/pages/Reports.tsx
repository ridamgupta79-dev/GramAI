import { DashboardPayload, downloadReport } from '../dashboardApi'

export default function Reports({
  payload,
}: {
  payload: DashboardPayload | null
}) {
  // New analysis structure:
  // sections
  //   └── analysis
  //        └── data
  const analysis = payload?.sections?.analysis?.data

  const swot = analysis?.swot
  const financial = analysis?.financial
  const loan = analysis?.loan_eligibility

  const location = analysis?.location
  const market = analysis?.market
  const risk = analysis?.risk_profile

  return (
    <div
      style={{
        display: 'flex',
        gap: 24,
        alignItems: 'flex-start',
      }}
    >
      {/* =====================================================
          MAIN REPORT
         ===================================================== */}

      <div className="card" style={{ flex: 1 }}>
        <div
          className="mono-label"
          style={{ color: 'var(--primary)' }}
        >
          Confidential Business Plan
        </div>

        <h1
          className="headline-lg"
          style={{ margin: '4px 0 8px' }}
        >
          {payload
            ? `${String(payload.context.sector || '')
                .replace('_', ' ')
                .replace(/\b\w/g, c => c.toUpperCase())} — ${
                payload.context.block ||
                location?.village ||
                'Business Analysis'
              }`
            : 'Business Report'}
        </h1>

        <p className="muted label-sm">
          {payload
            ? `Feasibility for ${
                payload.context.village ||
                location?.village ||
                payload.context.block ||
                'selected location'
              }, ${
                payload.context.district || ''
              }, ${
                payload.context.state || ''
              }`
            : 'Run an analysis to generate your first report.'}
        </p>

        {payload && (
          <>
            {/* =================================================
                1. EXECUTIVE SUMMARY
               ================================================= */}

            <h2
              className="title-md"
              style={{ margin: '24px 0 8px' }}
            >
              1. Executive Summary
            </h2>

            <div
              className="card-low"
              style={{
                lineHeight: 1.7,
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
              }}
            >
              <div>
                <div className="mono-label muted">
                  Viability Score
                </div>

                <div
                  style={{
                    fontSize: 28,
                    fontWeight: 700,
                    marginTop: 4,
                  }}
                >
                  {analysis?.viability_score ?? '—'}
                  <span
                    style={{
                      fontSize: 14,
                      fontWeight: 400,
                      marginLeft: 4,
                    }}
                  >
                    / 100
                  </span>
                </div>
              </div>

              <div>
                <div className="mono-label muted">
                  Viability Rating
                </div>

                <div
                  style={{
                    fontSize: 20,
                    fontWeight: 600,
                    marginTop: 8,
                  }}
                >
                  {analysis?.viability_rating ?? '—'}
                </div>
              </div>

              <div>
                <div className="mono-label muted">
                  Market Opportunity
                </div>

                <div style={{ marginTop: 6 }}>
                  {market?.market_opportunity ?? '—'}
                </div>
              </div>

              <div>
                <div className="mono-label muted">
                  Overall Risk
                </div>

                <div style={{ marginTop: 6 }}>
                  <span
                    className={`badge ${
                      risk?.overall === 'high'
                        ? 'red'
                        : risk?.overall === 'moderate'
                        ? 'orange'
                        : 'green'
                    }`}
                  >
                    {risk?.overall
                      ? String(risk.overall).toUpperCase()
                      : '—'}
                  </span>
                </div>
              </div>
            </div>

            {/* =================================================
                LOCATION + MARKET
               ================================================= */}

            <h2
              className="title-md"
              style={{ margin: '24px 0 8px' }}
            >
              2. Market & Location Intelligence
            </h2>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
              }}
            >
              <div className="card-low">
                <div className="mono-label muted">
                  Location
                </div>

                <div
                  style={{
                    marginTop: 8,
                    lineHeight: 1.8,
                    fontSize: 14,
                  }}
                >
                  <div>
                    Village:{' '}
                    <b>
                      {location?.village ||
                        payload.context.village ||
                        '—'}
                    </b>
                  </div>

                  <div>
                    Population:{' '}
                    <b>
                      {(
                        location?.population ?? 0
                      ).toLocaleString('en-IN')}
                    </b>
                  </div>

                  <div>
                    Latitude:{' '}
                    <b>{location?.latitude ?? '—'}</b>
                  </div>

                  <div>
                    Longitude:{' '}
                    <b>{location?.longitude ?? '—'}</b>
                  </div>
                </div>
              </div>

              <div className="card-low">
                <div className="mono-label muted">
                  Market Signals
                </div>

                <div
                  style={{
                    marginTop: 8,
                    lineHeight: 1.8,
                    fontSize: 14,
                  }}
                >
                  <div>
                    Target Customers:{' '}
                    <b>
                      {(
                        market?.target_customer_base ?? 0
                      ).toLocaleString('en-IN')}
                    </b>
                  </div>

                  <div>
                    Competitors within 10 km:{' '}
                    <b>
                      {market?.competitors_within_10km ?? 0}
                    </b>
                  </div>

                  <div>
                    Competition:{' '}
                    <b>
                      {market?.competition_level ?? '—'}
                    </b>
                  </div>

                  <div>
                    Pricing Pressure:{' '}
                    <b>
                      {market?.pricing_pressure ?? '—'}
                    </b>
                  </div>
                </div>
              </div>
            </div>

            {/* =================================================
                SWOT
               ================================================= */}

            {swot && (
              <>
                <h2
                  className="title-md"
                  style={{ margin: '24px 0 8px' }}
                >
                  3. SWOT Analysis
                </h2>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: 12,
                  }}
                >
                  {(
                    [
                      [
                        'Strengths',
                        swot.strengths,
                        'green',
                      ],
                      [
                        'Weaknesses',
                        swot.weaknesses,
                        'red',
                      ],
                      [
                        'Opportunities',
                        swot.opportunities,
                        'blue',
                      ],
                      [
                        'Threats',
                        swot.threats,
                        'orange',
                      ],
                    ] as const
                  ).map(
                    ([title, items, color]) => (
                      <div
                        key={title}
                        className="card-low"
                      >
                        <span
                          className={`badge ${color}`}
                        >
                          {title}
                        </span>

                        <ul
                          style={{
                            paddingLeft: 18,
                            fontSize: 13,
                            lineHeight: 1.7,
                          }}
                        >
                          {(items as string[])
                            ?.slice(0, 4)
                            .map((item, index) => (
                              <li key={index}>
                                {item}
                              </li>
                            ))}
                        </ul>
                      </div>
                    )
                  )}
                </div>
              </>
            )}

            {/* =================================================
                FINANCIAL PROJECTIONS
               ================================================= */}

            <h2
              className="title-md"
              style={{ margin: '24px 0 8px' }}
            >
              4. Financial Projections
            </h2>

            <table className="gramai">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Value</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td>Project Cost</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.project_cost ?? 0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>

                <tr>
                  <td>Margin</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.margin_amount ?? 0
                      ).toLocaleString('en-IN')}
                    </b>
                    {' '}
                    ({financial?.margin_pct ?? 0}%)
                  </td>
                </tr>

                <tr>
                  <td>Loan Amount</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.loan_amount ??
                        loan?.loan_amount ??
                        0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>

                <tr>
                  <td>Monthly EMI</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.monthly_emi ??
                        loan?.emi ??
                        0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>

                <tr>
                  <td>Monthly Revenue</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.monthly_revenue ?? 0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>

                <tr>
                  <td>Monthly Operating Cost</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.monthly_opex ?? 0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>

                <tr>
                  <td>Monthly Operating Profit</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.monthly_profit ?? 0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>

                <tr>
                  <td>Total Interest</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.total_interest ??
                        loan?.total_interest ??
                        0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>

                <tr>
                  <td>6-Month Working Capital</td>
                  <td>
                    <b>
                      ₹
                      {(
                        financial?.working_capital_6_months ??
                        0
                      ).toLocaleString('en-IN')}
                    </b>
                  </td>
                </tr>
              </tbody>
            </table>

            {/* =================================================
                PRICING
               ================================================= */}

            {analysis?.pricing && (
              <>
                <h2
                  className="title-md"
                  style={{ margin: '24px 0 8px' }}
                >
                  5. Pricing Intelligence
                </h2>

                <div className="card-low">
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns:
                        '1fr 1fr',
                      gap: 16,
                    }}
                  >
                    <div>
                      <div className="mono-label muted">
                        Competitor Price
                      </div>

                      <div
                        style={{
                          fontSize: 22,
                          fontWeight: 700,
                          marginTop: 4,
                        }}
                      >
                        ₹
                        {(
                          analysis.pricing
                            .competitor_price ?? 0
                        ).toLocaleString('en-IN')}
                      </div>
                    </div>

                    <div>
                      <div className="mono-label muted">
                        Recommended Price
                      </div>

                      <div
                        style={{
                          fontSize: 22,
                          fontWeight: 700,
                          marginTop: 4,
                        }}
                      >
                        ₹
                        {(
                          analysis.pricing
                            .recommended_price ?? 0
                        ).toLocaleString('en-IN')}
                      </div>
                    </div>
                  </div>

                  {analysis.pricing.note && (
                    <p
                      className="muted"
                      style={{
                        fontSize: 12,
                        marginBottom: 0,
                      }}
                    >
                      {analysis.pricing.note}
                    </p>
                  )}
                </div>
              </>
            )}

            {/* =================================================
                GOVERNMENT SCHEMES
               ================================================= */}

            {analysis?.scheme_matches && (
              <>
                <h2
                  className="title-md"
                  style={{ margin: '24px 0 8px' }}
                >
                  6. Government Scheme Matches
                </h2>

                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                  }}
                >
                  {analysis.scheme_matches
                    .filter(
                      (scheme: any) =>
                        scheme.eligible
                    )
                    .map(
                      (
                        scheme: any,
                        index: number
                      ) => (
                        <div
                          key={
                            scheme.name ||
                            scheme.scheme ||
                            index
                          }
                          className="card-low"
                          style={{
                            display: 'flex',
                            justifyContent:
                              'space-between',
                            alignItems:
                              'center',
                            gap: 12,
                          }}
                        >
                          <div>
                            <b>
                              {scheme.name ||
                                scheme.scheme ||
                                'Government Scheme'}
                            </b>

                            {scheme.description && (
                              <div
                                className="muted"
                                style={{
                                  fontSize: 12,
                                  marginTop: 4,
                                }}
                              >
                                {
                                  scheme.description
                                }
                              </div>
                            )}
                          </div>

                          <span className="badge green">
                            Potentially Eligible
                          </span>
                        </div>
                      )
                    )}
                </div>
              </>
            )}

            {/* =================================================
                RISK
               ================================================= */}

            {risk && (
              <>
                <h2
                  className="title-md"
                  style={{ margin: '24px 0 8px' }}
                >
                  7. Risk Assessment
                </h2>

                <div className="card-low">
                  <div
                    style={{
                      marginBottom: 10,
                    }}
                  >
                    Overall Risk:{' '}
                    <span
                      className={`badge ${
                        risk.overall === 'high'
                          ? 'red'
                          : risk.overall ===
                            'moderate'
                          ? 'orange'
                          : 'green'
                      }`}
                    >
                      {String(
                        risk.overall || 'low'
                      ).toUpperCase()}
                    </span>
                  </div>

                  {risk.risk_factors?.length ? (
                    <ul
                      style={{
                        paddingLeft: 20,
                        lineHeight: 1.7,
                        fontSize: 13,
                      }}
                    >
                      {risk.risk_factors.map(
                        (
                          factor: string,
                          index: number
                        ) => (
                          <li key={index}>
                            {factor}
                          </li>
                        )
                      )}
                    </ul>
                  ) : (
                    <div className="muted">
                      No major risk factors
                      identified.
                    </div>
                  )}
                </div>
              </>
            )}

            {/* =================================================
                ASSUMPTIONS
               ================================================= */}

            {financial?.assumptions && (
              <>
                <h2
                  className="title-md"
                  style={{ margin: '24px 0 8px' }}
                >
                  8. Financial Assumptions
                </h2>

                <div
                  className="card-low"
                  style={{
                    fontSize: 13,
                    lineHeight: 1.7,
                  }}
                >
                  <div>
                    Monthly OPEX assumption:{' '}
                    <b>
                      {
                        financial.assumptions
                          .monthly_opex_pct_of_project_cost
                      }
                      %
                    </b>{' '}
                    of project cost
                  </div>

                  <div>
                    Monthly revenue multiplier:{' '}
                    <b>
                      {
                        financial.assumptions
                          .monthly_revenue_multiplier
                      }
                      ×
                    </b>
                  </div>

                  {financial.assumptions.note && (
                    <p
                      className="muted"
                      style={{
                        marginBottom: 0,
                      }}
                    >
                      {
                        financial.assumptions
                          .note
                      }
                    </p>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </div>

      {/* =====================================================
          SIDEBAR
         ===================================================== */}

      <div
        style={{
          width: 260,
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        <div className="card">
          <h2
            className="title-md"
            style={{ marginTop: 0 }}
          >
            Actions
          </h2>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            <button
              className="btn"
              disabled={!payload}
              onClick={() =>
                payload &&
                downloadReport(
                  payload.report_id
                )
              }
            >
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 18 }}
              >
                download
              </span>{' '}
              Download PDF
            </button>

            <button className="btn btn-ghost">
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 18 }}
              >
                share
              </span>{' '}
              Share with Bank
            </button>

            <button
              className="btn btn-ghost"
              onClick={() => window.print()}
            >
              <span
                className="material-symbols-outlined"
                style={{ fontSize: 18 }}
              >
                print
              </span>{' '}
              Print Report
            </button>
          </div>
        </div>

        <div className="card">
          <div className="mono-label muted">
            Document Info
          </div>

          <div
            style={{
              marginTop: 8,
              fontSize: 14,
              lineHeight: 2,
            }}
          >
            <div>
              Status:{' '}
              <span className="badge green">
                Final Review
              </span>
            </div>

            <div>
              Author: <b>GramAI</b>
            </div>

            <div>
              Report ID:{' '}
              <b>{payload?.report_id || '—'}</b>
            </div>

            <div>
              Data:{' '}
              <b>Prototype / Demo</b>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}