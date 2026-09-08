import MarketMap from './pages/MarketMap'
import { useEffect, useState } from 'react'
import {
  fetchBlocks,
  fetchDistricts,
  fetchStates,
  fetchVillages,
  getStoredUser,
  getToken,
  clearAuth,
  api,
  createAnalysis,
  getAnalysisInsights,
  fetchMyReports,
} from './api'
import { DashboardPayload } from './dashboardApi'
import Shell from './components/Shell'
import Welcome from './pages/Welcome'
import Login from './pages/Login'
import Home from './pages/Home'
import NewAnalysis from './pages/NewAnalysis'
import Schemes from './pages/Schemes'
import Reports from './pages/Reports'
import Advisor from './pages/Advisor'
import Profile from './pages/Profile'
import Admin from './pages/Admin'

export type Page =
  | 'home'
  | 'new'
  | 'market'
  | 'schemes'
  | 'reports'
  | 'advisor'
  | 'profile'
  | 'admin'

interface ApplicantProfile {
  isWoman: boolean
  isSCST: boolean
  previousTarunRepaid: boolean
}

export default function App() {
  const [entered, setEntered] = useState(() => !!getToken())
  const [user, setUser] = useState(getStoredUser())
  const [isAdmin, setIsAdmin] = useState(false)
  const [page, setPage] = useState<Page>('home')

  const [states, setStates] = useState<string[]>([])
  const [districts, setDistricts] = useState<string[]>([])
  const [blocks, setBlocks] = useState<string[]>([])
  const [villages, setVillages] = useState<string[]>([])

  const [loc, setLoc] = useState({
    state: '',
    district: '',
    block: '',
    village: '',
  })

  const [sector, setSector] = useState('dairy')
  const [margin, setMargin] = useState(100000)

  const [payload, setPayload] =
    useState<DashboardPayload | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (entered && getToken()) {
      fetchStates()
        .then(setStates)
        .catch(() => [])

      api
        .get('/users/me')
        .then(r => setIsAdmin(r.data.role === 'admin'))
        .catch(() => {})
    }
  }, [entered])

  useEffect(() => {
    if (!entered || !getToken()) return

    async function restoreLatestAnalysis() {
      try {
        const reports = await fetchMyReports()

        if (!reports?.length) return

        const latest = reports[0]

        const fullReport = await api.get(
          `/reports/${latest.id}`,
        )

        const content = fullReport.data.content
        const insights = content?.insights ?? {}
        const request = content?.request ?? {}

        setPayload({
          report_id: latest.id,

          context: {
            location: 'Saved analysis',
            sector: request.category_slug ?? 'dairy',
            margin_capital:
              request.financing?.project_cost
                ? request.financing.project_cost / 10
                : 100000,
          },

          sections: {
            analysis: {
              data: insights,
            },
          },
        })
      } catch {
        // No saved analysis to restore.
      }
    }

    restoreLatestAnalysis()
  }, [entered])

  async function runAnalysis(
    profile?: ApplicantProfile,
  ) {
    setLoading(true)
    setError('')
    setPage('new')

    try {
      // Resolve the selected village into its seeded ID and coordinates.
      const locationProfile = await api
        .get('/v1/location/profile', {
          params: {
            state: loc.state,
            district: loc.district,
            block: loc.block,
            village: loc.village,
          },
        })
        .then(r => r.data)

      if (!locationProfile.village_id) {
        throw new Error(
          'Please select a valid village before running the analysis.',
        )
      }

      // Start the asynchronous analysis pipeline.
      //
      // The applicant profile is now passed to the backend
      // for personalized government-scheme matching.
      const started = await createAnalysis({
        village_id: locationProfile.village_id,
        lat: locationProfile.latitude,
        lon: locationProfile.longitude,
        category_slug: sector,

        // Personalized scheme inputs
        is_woman: profile?.isWoman ?? false,
        is_scst: profile?.isSCST ?? false,
        previous_tarun_repaid:
          profile?.previousTarunRepaid ?? false,

        financing: {
          project_cost: margin * 10,
          margin_pct: 10,
          interest_rate: 9.5,
          tenure_months: 60,
          moratorium_months: 0,
        },
      })

      const analysisId = started.analysis_id

      // Wait for the backend analysis pipeline to finish.
      await new Promise<void>((resolve, reject) => {
        const token = getToken()

        const source = new EventSource(
          `/api/analyses/${analysisId}/status?token=${encodeURIComponent(
            token ?? '',
          )}`,
        )

        source.addEventListener('stage', event => {
          try {
            const data = JSON.parse(
              (event as MessageEvent).data,
            )

            if (data.stage === 'done') {
              source.close()
              resolve()
            }
          } catch {
            source.close()

            reject(
              new Error(
                'Invalid analysis progress response',
              ),
            )
          }
        })

        source.onerror = () => {
          source.close()

          reject(
            new Error(
              'Analysis progress connection failed',
            ),
          )
        }
      })

      // Fetch the completed analysis result.
      const insights = await getAnalysisInsights(
        analysisId,
      )

      // Temporarily adapt the new analysis response
      // to the existing DashboardPayload expected by
      // the current UI.
      setPayload({
        report_id: insights.report_id ?? analysisId,

        context: {
          location: loc,
          sector,
          margin_capital: margin,
          village_id: locationProfile.village_id,
          latitude: locationProfile.latitude,
          longitude: locationProfile.longitude,
        },

        sections: {
          analysis: {
            data: insights,
          },
        },
      })

      setPage('home')
    } catch (e: any) {
      setError(
        e?.response?.data?.detail ??
          e?.message ??
          'Analysis failed',
      )
    } finally {
      setLoading(false)
    }
  }

  if (!entered) {
    return (
      <Welcome
        onStart={() => setEntered(true)}
      />
    )
  }

  if (!user || !getToken()) {
    return (
      <Login
        onDone={u => {
          setUser(u)

          api
            .get('/users/me')
            .then(r =>
              setIsAdmin(r.data.role === 'admin'),
            )
            .catch(() => {})
        }}
      />
    )
  }

  return (
    <Shell
      page={page}
      onNavigate={setPage}
      userName={user.full_name || 'U'}
      isAdmin={isAdmin}
      onSignOut={() => {
        clearAuth()
        setUser(null)
        setIsAdmin(false)
      }}
    >
      {/* =====================================================
          HOME
         ===================================================== */}
      {page === 'home' && (
        <Home
          payload={payload}
          loading={loading}
          error={error}
          states={states}
          districts={districts}
          blocks={blocks}
          villages={villages}
          loc={loc}
          setLoc={setLoc}

          onStates={async s => {
            setLoc({
              ...loc,
              state: s,
              district: '',
              block: '',
              village: '',
            })

            setDistricts(
              await fetchDistricts(s).catch(
                () => [],
              ),
            )
          }}

          onDistricts={async d => {
            setLoc({
              ...loc,
              district: d,
              block: '',
              village: '',
            })

            setBlocks(
              await fetchBlocks(
                loc.state,
                d,
              ).catch(() => []),
            )
          }}

          onBlocks={async b => {
            setLoc({
              ...loc,
              block: b,
              village: '',
            })

            setVillages(
              await fetchVillages(
                loc.state,
                loc.district,
                b,
              ).catch(() => []),
            )
          }}

          sector={sector}
          setSector={setSector}
          margin={margin}
          setMargin={setMargin}
          onRun={runAnalysis}
          onNavigate={setPage}
          userName={user.full_name}
        />
      )}

      {/* =====================================================
          NEW ANALYSIS
         ===================================================== */}
      {page === 'new' && (
        <NewAnalysis
          states={states}
          districts={districts}
          blocks={blocks}
          villages={villages}

          loc={loc}
          setLoc={setLoc}

          onStates={async s => {
            setLoc({
              ...loc,
              state: s,
              district: '',
              block: '',
              village: '',
            })

            setDistricts(
              await fetchDistricts(s).catch(
                () => [],
              ),
            )
          }}

          onDistricts={async d => {
            setLoc({
              ...loc,
              district: d,
              block: '',
              village: '',
            })

            setBlocks(
              await fetchBlocks(
                loc.state,
                d,
              ).catch(() => []),
            )
          }}

          onBlocks={async b => {
            setLoc({
              ...loc,
              block: b,
              village: '',
            })

            setVillages(
              await fetchVillages(
                loc.state,
                loc.district,
                b,
              ).catch(() => []),
            )
          }}

          sector={sector}
          setSector={setSector}

          margin={margin}
          setMargin={setMargin}

          // NewAnalysis now passes the applicant profile here.
          onRun={runAnalysis}

          loading={loading}
          error={error}
          payload={payload}
        />
      )}

      {/* =====================================================
          MARKET MAP
         ===================================================== */}
      {page === 'market' && (
        <MarketMap payload={payload} />
      )}

      {/* =====================================================
          OTHER PAGES
         ===================================================== */}

      {page === 'schemes' && (
        <Schemes />
      )}

      {page === 'reports' && (
        <Reports payload={payload} />
      )}

      {page === 'advisor' && (
        <Advisor payload={payload} />
      )}

      {page === 'profile' && (
        <Profile onNavigate={setPage} />
      )}

      {page === 'admin' && (
        <Admin />
      )}
    </Shell>
  )
}