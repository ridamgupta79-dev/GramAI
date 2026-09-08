import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { FeasibilityReport } from '../api'

function List({ title, items }: { title: string; items: string[] }) {
  if (!items?.length) return null
  return (
    <div style={{ marginTop: '.75rem' }}>
      <h3 style={{ margin: '0 0 .35rem', fontSize: '.95rem' }}>{title}</h3>
      <ul className="plain">{items.map((t, i) => <li key={i}>{t}</li>)}</ul>
    </div>
  )
}

export default function ReportView({ report }: { report: FeasibilityReport }) {
  const reach = report.market_reach
  const chartData = [
    { name: '5 km radius', population: reach.estimated_population_5km },
    { name: '10 km radius', population: reach.estimated_population_10km },
    { name: 'Target customers', population: reach.target_customer_base },
  ]

  return (
    <div className="card">
      <h2>📊 Hyper-Local Business Feasibility Report</h2>
      <p>{report.summary}</p>

      <h3 style={{ fontSize: '.95rem' }}>Market Reach</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip formatter={(v: number) => v.toLocaleString('en-IN')} />
          <Bar dataKey="population" fill="#1a7f4b" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <List title="Primary Distribution Channels" items={reach.primary_distribution_channels} />

      <List title="Opportunity Analysis" items={report.opportunity_analysis} />

      <h3 style={{ fontSize: '.95rem', marginTop: '1rem' }}>SWOT Analysis</h3>
      <div className="grid-2">
        <List title="💪 Strengths" items={report.swot.strengths} />
        <List title="⚠️ Weaknesses" items={report.swot.weaknesses} />
        <List title="🌱 Opportunities" items={report.swot.opportunities} />
        <List title="🚨 Threats" items={report.swot.threats} />
      </div>

      <List title="Key Local Threats" items={report.threats} />

      <h3 style={{ fontSize: '.95rem', marginTop: '1rem' }}>Competitor Mapping</h3>
      <p>
        Estimated competitors in block: <strong>{report.competitor_mapping.estimated_competitors_in_block}</strong>{' '}
        (<span className="badge">{report.competitor_mapping.density_assessment} density</span>)
        <br /><small style={{ color: '#5d6f64' }}>{report.competitor_mapping.notes}</small>
      </p>

      <h3 style={{ fontSize: '.95rem' }}>Pricing & Market Value</h3>
      <p><strong>Suggested pricing:</strong> {report.pricing.suggested_price_range}<br />
         <strong>Predicted local market value:</strong> {report.pricing.predicted_local_market_value}<br />
         <small style={{ color: '#5d6f64' }}>{report.pricing.rationale}</small></p>
    </div>
  )
}
