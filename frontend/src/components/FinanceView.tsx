import { LoanPlan } from '../api'

const inr = (n: number) =>
  '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 0 })

export default function FinanceView({ plan }: { plan: LoanPlan }) {
  return (
    <div className="card">
      <h2>💰 Financial Roadmap — <span className="badge">{plan.scheme}</span></h2>
      {plan.advice && <div className="error" style={{ marginBottom: '.75rem' }}>{plan.advice}</div>}
      <div className="stat-row">
        <div className="stat"><div className="value">{inr(plan.project_cost)}</div><div className="label">Total Project Cost</div></div>
        <div className="stat"><div className="value">{inr(plan.margin_money)}</div><div className="label">Your Margin (10%)</div></div>
        <div className="stat"><div className="value">{inr(plan.max_loan_amount)}</div><div className="label">Max Loan Eligibility</div></div>
        <div className="stat"><div className="value">{plan.interest_rate_pa}% p.a.</div><div className="label">Interest Rate</div></div>
        <div className="stat"><div className="value">{inr(plan.quarterly_emi)}</div><div className="label">Quarterly EMI (after moratorium)</div></div>
        <div className="stat"><div className="value">{inr(plan.total_repayment)}</div><div className="label">Total Repayment ({plan.tenure_years} yrs)</div></div>
        <div className="stat"><div className="value">{inr(plan.working_capital_estimate)}</div><div className="label">Working Capital Needed (~6 months)</div></div>
      </div>

      <h2 style={{ marginTop: '1.25rem' }}>Quarterly Repayment Schedule</h2>
      <table className="schedule">
        <thead>
          <tr>
            <th>Quarter</th><th>Phase</th><th>Opening Balance</th>
            <th>Interest</th><th>Principal</th><th>Payment</th><th>Closing Balance</th>
          </tr>
        </thead>
        <tbody>
          {plan.schedule.map(r => (
            <tr key={r.quarter} className={r.phase === 'moratorium' ? 'moratorium' : ''}>
              <td>Q{r.quarter}</td>
              <td>{r.phase === 'moratorium' ? 'Moratorium' : 'Repayment'}</td>
              <td>{inr(r.opening_balance)}</td>
              <td>{inr(r.interest_due)}</td>
              <td>{inr(r.principal_repaid)}</td>
              <td>{inr(r.total_payment)}</td>
              <td>{inr(r.closing_balance)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
