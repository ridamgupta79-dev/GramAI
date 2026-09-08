import { useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import { DashboardPayload } from '../dashboardApi'
import { applyForScheme, downloadReport } from '../dashboardApi'
import MentorPanel from './MentorPanel'

const inr = (n: number) => '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="card">
      <h2>{title}</h2>
      {children}
    </div>
  )
}

function Bullets({ items }: { items: any[] }) {
  return (
    <ul className="plain">
      {items.map((it, i) => (
        <li key={i}>{typeof it === 'string' ? it : JSON.stringify(it)}</li>
      ))}
    </ul>
  )
}

export default function Dashboard({ payload }: { payload: DashboardPayload }) {
  const s = payload.sections
  const [applyState, setApplyState] = useState<{ done?: boolean; msg?: string }>({})
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')

  const loan = s.loan_eligibility?.data ?? {}
  const schemeRec = (s.scheme_recommendation?.data?.recommended ?? [])[0] ?? {}
  const demand = s.market_demand?.data ?? {}
  const comp = s.competitor_map?.data ?? {}
  const swot = s.swot_analysis?.data ?? {}
  const risks = s.risk_analysis?.data?.risks ?? []
  const pricing = s.pricing_suggestions?.data ?? {}
  const wc = s.working_capital?.data ?? {}
  const emi = s.emi_schedule?.data ?? {}
  const cashflow = s.cash_flow_forecast?.data?.forecast ?? []
  const tips = s.ai_mentor?.data?.tips ?? []

  return (
    <>
      <Section title="🏦 Loan Eligibility">
        <div className="stat-row">
          <div className="stat"><div className="value">{inr(loan.project_cost ?? 0)}</div><div className="label">Project Cost</div></div>
          <div className="stat"><div className="value">{inr(loan.max_loan_amount ?? 0)}</div><div className="label">Max Loan (90%)</div></div>
          <div className="stat"><div className="value">{schemeRec.scheme ?? '—'}</div><div className="label">Recommended Scheme</div></div>
          {schemeRec.interest_rate_pa && (
            <div className="stat"><div className="value">{schemeRec.interest_rate_pa}% p.a.</div><div className="label">Interest · {schemeRec.tenure_years} yrs</div></div>
          )}
        </div>
        {s.scheme_recommendation?.sources?.length ? (
          <p style={{ marginTop: '.6rem' }}>
            Grounded in: {s.scheme_recommendation.sources.join(', ')}
          </p>
        ) : null}
      </Section>

      <Section title="📈 Market Demand">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={[
            { name: '5 km', population: demand.population_5km },
            { name: '10 km', population: demand.population_10km },
            { name: 'Target base', population: demand.target_customer_base },
          ]}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" /><YAxis />
            <Tooltip formatter={(v: number) => v.toLocaleString('en-IN')} />
            <Bar dataKey="population" fill="#1a7f4b" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p>Estimated annual demand value: <strong>{inr(demand.estimated_annual_demand_value ?? 0)}</strong></p>
        <Bullets items={demand.distribution_channels ?? []} />
      </Section>

      <Section title="🗺️ Competitor Map">
        <p>
          Estimated competitors in block: <strong>{comp.estimated_competitors_in_block}</strong>{' '}
          (<span className="badge">{comp.density_assessment} density</span>)
          <br /><small style={{ color: '#5d6f64' }}>{comp.notes}</small>
        </p>
      </Section>

      <Section title="⚖️ SWOT Analysis">
        <div className="grid-2">
          <div><h3 style={{ fontSize: '.95rem' }}>💪 Strengths</h3><Bullets items={swot.strengths ?? []} /></div>
          <div><h3 style={{ fontSize: '.95rem' }}>⚠️ Weaknesses</h3><Bullets items={swot.weaknesses ?? []} /></div>
          <div><h3 style={{ fontSize: '.95rem' }}>🌱 Opportunities</h3><Bullets items={swot.opportunities ?? []} /></div>
          <div><h3 style={{ fontSize: '.95rem' }}>🚨 Threats</h3><Bullets items={swot.threats ?? []} /></div>
        </div>
      </Section>

      <Section title="🛡️ Risk Analysis">
        <table className="schedule">
          <thead><tr><th>Risk</th><th>Severity</th><th>Mitigation</th></tr></thead>
          <tbody>
            {risks.map((r: any, i: number) => (
              <tr key={i}><td style={{ textAlign: 'left' }}>{r.risk}</td>
                  <td><span className="badge">{r.severity}</span></td>
                  <td style={{ textAlign: 'left' }}>{r.mitigation}</td></tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="🏷️ Pricing Suggestions">
        <p><strong>Strategy:</strong> {pricing.strategy}<br />
           <strong>Predicted local market value:</strong> {inr(pricing.predicted_local_market_value ?? 0)}<br />
           <small style={{ color: '#5d6f64' }}>{pricing.rationale}</small></p>
      </Section>

      <Section title="💧 Working Capital">
        <div className="stat-row">
          <div className="stat"><div className="value">{inr(wc.monthly_operating_cost_estimate ?? 0)}</div><div className="label">Monthly Operating Cost</div></div>
          <div className="stat"><div className="value">{inr(wc.working_capital_requirement ?? 0)}</div><div className="label">6-Month Reserve Needed</div></div>
        </div>
        <p style={{ color: '#5d6f64' }}>{wc.note}</p>
      </Section>

      <Section title="📅 EMI Schedule">
        <p>Quarterly EMI: <strong>{inr(emi.quarterly_emi ?? 0)}</strong> · Total interest:{' '}
           <strong>{inr(emi.total_interest ?? 0)}</strong> · Total repayment:{' '}
           <strong>{inr(emi.total_repayment ?? 0)}</strong></p>
        <table className="schedule">
          <thead><tr><th>Qtr</th><th>Phase</th><th>Interest</th><th>Principal</th><th>Payment</th><th>Balance</th></tr></thead>
          <tbody>
            {(emi.schedule ?? []).map((r: any) => (
              <tr key={r.quarter} className={r.phase === 'moratorium' ? 'moratorium' : ''}>
                <td>Q{r.quarter}</td><td>{r.phase === 'moratorium' ? 'Moratorium' : 'Repayment'}</td>
                <td>{inr(r.interest_due)}</td><td>{inr(r.principal_repaid)}</td>
                <td>{inr(r.total_payment)}</td><td>{inr(r.closing_balance)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="💹 Cash Flow Forecast">
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={cashflow}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="quarter" tickFormatter={(q: number) => `Q${q}`} />
            <YAxis />
            <Tooltip formatter={(v: number) => inr(v)} />
            <Line type="monotone" dataKey="revenue" stroke="#1a7f4b" name="Revenue" />
            <Line type="monotone" dataKey="gross_profit" stroke="#2b7fb8" name="Gross Profit" />
            <Line type="monotone" dataKey="cumulative_cash" stroke="#c0392b" name="Cumulative Cash" />
          </LineChart>
        </ResponsiveContainer>
      </Section>

      <MentorPanel reportId={payload.report_id} />

      <Section title="⬇️ Download & Apply">
        <button className="btn" onClick={() => downloadReport(payload.report_id)}>
          📄 Download Business Report
        </button>
        {!applyState.done ? (
          <div style={{ marginTop: '1rem' }}>
            <label>Your Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} />
            <label>Phone</label>
            <input type="text" value={phone} onChange={e => setPhone(e.target.value)} />
            <button className="btn" disabled={!name || !phone}
                    onClick={async () => {
                      try {
                        const r = await applyForScheme(payload.report_id, name, phone,
                          schemeRec.scheme ?? '')
                        setApplyState({ done: true, msg: `${r.message} (ID: ${r.application_id})` })
                      } catch { setApplyState({ msg: 'Application failed — please retry.' }) }
                    }}>
              ✅ Apply for Government Scheme
            </button>
          </div>
        ) : (
          <p style={{ background: '#eef6f0', padding: '.75rem 1rem', borderRadius: 8, marginTop: '1rem' }}>
            {applyState.msg}
          </p>
        )}
        {applyState.msg && !applyState.done &&
          <p className="error" style={{ marginTop: '.5rem' }}>{applyState.msg}</p>}
      </Section>
    </>
  )
}
