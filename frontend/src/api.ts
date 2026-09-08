import axios from 'axios'

export const TOKEN_KEY = 'gramai_token'
export const USER_KEY = 'gramai_user'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const getStoredUser = (): { id: number; mobile: string; full_name: string } | null => {
  try { return JSON.parse(localStorage.getItem(USER_KEY) ?? 'null') } catch { return null }
}
export const setAuth = (token: string, user: any) => {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}
export const clearAuth = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(cfg => {
  const t = getToken()
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

api.interceptors.response.use(
  r => r,
  err => {
    if (err?.response?.status === 401 && getToken()) {
      clearAuth()
      window.location.reload()
    }
    return Promise.reject(err)
  },
)

// ---------- Auth API ----------

export const sendOtp = (mobile: string) =>
  api.post('/auth/otp/send', { mobile }).then(r => r.data)

export const verifyOtp = (mobile: string, otp: string, full_name = '') =>
  api.post('/auth/otp/verify', { mobile, otp, full_name }).then(r => r.data)

export interface LocationInput {
  village: string
  block: string
  district: string
  state: string
}

export interface LoanPlan {
  project_cost: number
  margin_money: number
  max_loan_amount: number
  scheme: string
  interest_rate_pa: number
  tenure_years: number
  moratorium_months: number
  quarterly_emi: number
  total_interest: number
  total_repayment: number
  working_capital_estimate: number
  schedule: {
    quarter: number; opening_balance: number; interest_due: number
    principal_repaid: number; total_payment: number; closing_balance: number; phase: string
  }[]
  advice?: string | null
}

export interface FeasibilityReport {
  market_reach: {
    estimated_population_5km: number; estimated_population_10km: number
    target_customer_base: number; primary_distribution_channels: string[]
  }
  opportunity_analysis: string[]
  swot: { strengths: string[]; weaknesses: string[]; opportunities: string[]; threats: string[] }
  threats: string[]
  competitor_mapping: { estimated_competitors_in_block: number; density_assessment: string; notes: string }
  pricing: { suggested_price_range: string; predicted_local_market_value: string; rationale: string }
  summary: string
}

export const getFinancePlan = (marginCapital: number, monthlyOpCost?: number) =>
  api.post<LoanPlan>('/finance/plan', {
    margin_capital: marginCapital,
    monthly_operating_cost: monthlyOpCost ?? null,
  }).then(r => r.data)

export const getFeasibilityReport = (
  location: LocationInput, sector: string, marginCapital: number,
) =>
  api.post<FeasibilityReport>('/feasibility/report', {
    location, sector, margin_capital: marginCapital,
  }).then(r => r.data)

export const fetchStates = () => api.get<string[]>('/v1/location/states').then(r => r.data)
export const fetchDistricts = (state: string) =>
  api.get<string[]>('/v1/location/districts', { params: { state } }).then(r => r.data)
export const fetchBlocks = (state: string, district: string) =>
  api.get<string[]>('/v1/location/blocks', { params: { state, district } }).then(r => r.data)
export const fetchVillages = (state: string, district: string, block: string) =>
  api.get<string[]>('/v1/location/villages', { params: { state, district, block } }).then(r => r.data)

export const fetchMyReports = () =>
  api.get('/reports', { params: { limit: 10 } }).then(r => r.data)

export interface AnalysisRequest {
  village_id?: number | null
  lat?: number | null
  lon?: number | null
  category_slug: string

  is_woman?: boolean
  is_scst?: boolean
  previous_tarun_repaid?: boolean

  financing: {
    project_cost: number
    margin_pct: number
    interest_rate: number
    tenure_months: number
    moratorium_months: number
  }
}

export interface AnalysisStartResponse {
  analysis_id: string
  status: string
}

export interface AnalysisStatus {
  stage: string
  progress: number
}

export const createAnalysis = (body: AnalysisRequest) =>
  api.post<AnalysisStartResponse>('/analyses', body).then(r => r.data)

export const getAnalysisInsights = (analysisId: string) =>
  api.get(`/analyses/${analysisId}/insights`).then(r => r.data)
