import { useEffect, useState, useRef } from 'react'
import { analyticsApi, listingsApi } from '../services/api'
import { TrendingUp, Home, DollarSign, MapPin, Award, RefreshCw, Building2, Info } from 'lucide-react'

const REC_COLORS = {
  strong_buy: 'bg-green-100 text-green-800 border border-green-200',
  buy: 'bg-blue-100 text-blue-800 border border-blue-200',
  hold: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  avoid: 'bg-red-100 text-red-800 border border-red-200',
}
const REC_LABELS = {
  strong_buy: 'Strong Buy',
  buy: 'Buy',
  hold: 'Hold',
  avoid: 'Avoid',
}
const PROP_TYPE_LABELS = {
  apartment: 'Apartment',
  house: 'House',
  villa: 'Villa',
  land: 'Land',
  room: 'Room',
}

const METRIC_TOOLTIPS = {
  score: 'Overall investment score (0–100) weighted across: Capital Appreciation (30%), Rental Income (25%), Growth Potential (20%), Market Liquidity (15%), and Risk (10%). Higher = better investment opportunity.',
  signal: 'Buy/sell recommendation based on the overall score. Strong Buy ≥70, Buy ≥55, Hold ≥40, Avoid <40.',
  price: 'Average sale price per m² from active listings in the past 30 days (in millions VND).',
  yield: 'Estimated annual rental yield = (avg monthly rent × 12) ÷ estimated property value × 100. Typical range: 3–8%. Higher yield means better rental income return.',
  appreciation: 'Estimated 1-year capital appreciation based on infrastructure development score. This is a model estimate, not a historical figure.',
}

function Tooltip({ text }) {
  return (
    <span className="relative group inline-flex items-center ml-1 cursor-pointer">
      <Info size={12} className="text-gray-300 hover:text-gray-500 transition-colors" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 leading-relaxed opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 shadow-xl">
        {text}
        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
      </span>
    </span>
  )
}

function ScoreBar({ value, color = 'bg-blue-500' }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${value || 0}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-600 w-8 text-right">{value?.toFixed(0) ?? '—'}</span>
    </div>
  )
}

function ScoreBadge({ value }) {
  const color = value >= 70 ? 'bg-green-500' : value >= 55 ? 'bg-blue-500' : value >= 40 ? 'bg-yellow-400' : 'bg-gray-400'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${value || 0}%` }} />
      </div>
      <span className="text-xs font-semibold text-gray-700 w-8 text-right">{value?.toFixed(0) ?? '—'}</span>
    </div>
  )
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [listingSummary, setListingSummary] = useState(null)
  const [topDistricts, setTopDistricts] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshMsg, setRefreshMsg] = useState(null)
  const pollRef = useRef(null)

  const loadData = () => {
    setLoading(true)
    Promise.all([
      analyticsApi.getMarketSummary(),
      listingsApi.getSummary(),
      analyticsApi.getTopOpportunities(10),
    ]).then(([mkt, lst, top]) => {
      setSummary(mkt.data)
      setListingSummary(lst.data)
      setTopDistricts(top.data)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { loadData() }, [])

  const triggerRefresh = async () => {
    try {
      setRefreshing(true)
      setRefreshMsg('Crawling latest data from Chotot...')
      await analyticsApi.triggerRefresh()
      pollRef.current = setInterval(async () => {
        const { data } = await analyticsApi.getRefreshStatus()
        if (!data.running) {
          clearInterval(pollRef.current)
          setRefreshing(false)
          setRefreshMsg('Data updated!')
          loadData()
          setTimeout(() => setRefreshMsg(null), 4000)
        }
      }, 3000)
    } catch (err) {
      setRefreshing(false)
      setRefreshMsg(err.response?.data?.detail === 'Crawl already in progress'
        ? 'Crawl already running, please wait...'
        : 'Failed to start crawl.')
      setTimeout(() => setRefreshMsg(null), 4000)
    }
  }

  useEffect(() => () => clearInterval(pollRef.current), [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-gray-400 text-sm">Loading market data...</p>
      </div>
    </div>
  )

  const fmtM = (n) => n ? `${(n / 1_000_000).toFixed(0)}M` : '—'
  const fmtRent = (n) => n ? `${(n / 1_000_000).toFixed(1)}M` : '—'
  const saleTypes = ['apartment', 'house', 'villa', 'land']
  const rentTypes = ['apartment', 'house', 'room']

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Vietnam Real Estate Intelligence</h1>
          <p className="text-gray-400 text-sm mt-1">
            Live data from{' '}
            <span className="text-gray-600 font-medium">{listingSummary?.total_listings?.toLocaleString() ?? '…'}</span>
            {' '}active listings across all 63 provinces · Updated daily at 07:00 ICT
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <button
            onClick={triggerRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 bg-white border border-gray-200 hover:border-blue-400 hover:text-blue-600 text-gray-600 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all disabled:opacity-50"
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            {refreshing ? 'Refreshing…' : 'Refresh Now'}
          </button>
          {refreshMsg && (
            <span className={`text-xs ${refreshMsg === 'Data updated!' ? 'text-green-600' : 'text-gray-400'}`}>
              {refreshMsg}
            </span>
          )}
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            icon: Home, color: 'text-blue-600', bg: 'bg-blue-50',
            label: 'Total Listings',
            value: listingSummary?.total_listings?.toLocaleString() ?? '—',
            sub: `${listingSummary?.sale_listings?.toLocaleString() ?? 0} for sale · ${listingSummary?.rent_listings?.toLocaleString() ?? 0} for rent`,
          },
          {
            icon: MapPin, color: 'text-orange-600', bg: 'bg-orange-50',
            label: 'Provinces Scored',
            value: summary?.districts_scored ?? '—',
            sub: `out of 63 provinces nationwide`,
          },
          {
            icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-50',
            label: 'Strong Buy Signals',
            value: summary?.recommendation_breakdown?.strong_buy ?? '—',
            sub: `${summary?.recommendation_breakdown?.buy ?? 0} Buy · ${summary?.recommendation_breakdown?.hold ?? 0} Hold · ${summary?.recommendation_breakdown?.avoid ?? 0} Avoid`,
          },
          {
            icon: Award, color: 'text-purple-600', bg: 'bg-purple-50',
            label: 'Data Source',
            value: 'Chotot.com',
            sub: 'Vietnam\'s largest real estate classifieds',
          },
        ].map(({ icon: Icon, color, bg, label, value, sub }) => (
          <div key={label} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className={`w-8 h-8 ${bg} ${color} rounded-lg flex items-center justify-center mb-3`}>
              <Icon size={16} />
            </div>
            <div className="text-xl font-bold text-gray-900">{value}</div>
            <div className="text-xs font-medium text-gray-500 mt-0.5">{label}</div>
            <div className="text-xs text-gray-400 mt-1 leading-relaxed">{sub}</div>
          </div>
        ))}
      </div>

      {/* Price breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <DollarSign size={16} className="text-purple-500" />
              <h2 className="font-semibold text-gray-800 text-sm">Avg Sale Price / m²</h2>
              <Tooltip text="Average price per square meter for sale listings in the past 30 days, grouped by property type. Based on active listings on Chotot.com." />
            </div>
            <p className="text-xs text-gray-400 mt-1">From active sale listings · past 30 days</p>
          </div>
          <div className="divide-y divide-gray-50">
            {saleTypes.map(pt => {
              const val = summary?.sale_price_by_type?.[pt]
              return (
                <div key={pt} className="px-4 py-3 flex items-center justify-between">
                  <span className="text-sm text-gray-600">{PROP_TYPE_LABELS[pt]}</span>
                  <div className="text-right">
                    <span className="text-sm font-bold text-gray-900">{fmtM(val)}</span>
                    {val && <span className="text-xs text-gray-400"> /m²</span>}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center gap-2">
              <Building2 size={16} className="text-green-500" />
              <h2 className="font-semibold text-gray-800 text-sm">Avg Rental / Month</h2>
              <Tooltip text="Average monthly rental price by property type. Based on active rental listings on Chotot.com in the past 30 days." />
            </div>
            <p className="text-xs text-gray-400 mt-1">From active rental listings · past 30 days</p>
          </div>
          <div className="divide-y divide-gray-50">
            {rentTypes.map(pt => {
              const val = summary?.rent_by_type?.[pt]
              return (
                <div key={pt} className="px-4 py-3 flex items-center justify-between">
                  <span className="text-sm text-gray-600">{PROP_TYPE_LABELS[pt]}</span>
                  <div className="text-right">
                    <span className="text-sm font-bold text-gray-900">{fmtRent(val)}</span>
                    {val && <span className="text-xs text-gray-400"> /tháng</span>}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Score legend */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4">
        <div className="flex items-center gap-2 mb-3">
          <Info size={14} className="text-blue-500" />
          <span className="text-sm font-semibold text-blue-800">How to read the investment table</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-blue-700">
          <div>
            <span className="font-semibold block mb-0.5">Score (0–100)</span>
            Weighted composite: Capital Appreciation 30%, Rental Income 25%, Growth 20%, Liquidity 15%, Risk 10%
          </div>
          <div>
            <span className="font-semibold block mb-0.5">Signal</span>
            Strong Buy ≥70 · Buy ≥55 · Hold ≥40 · Avoid &lt;40
          </div>
          <div>
            <span className="font-semibold block mb-0.5">Yield (%)</span>
            Annual rental return = (monthly rent × 12) ÷ property value. Healthy range: 4–7%
          </div>
          <div>
            <span className="font-semibold block mb-0.5">Appreciation (%)</span>
            Estimated 1-year capital gain based on infrastructure & development score. Model estimate only.
          </div>
        </div>
      </div>

      {/* Top opportunities table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Award size={18} className="text-yellow-500" />
            <h2 className="font-semibold text-gray-800">Top 10 Investment Opportunities</h2>
          </div>
          <span className="text-xs text-gray-400">Ranked by overall investment score</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 uppercase border-b border-gray-100 bg-gray-50">
                <th className="px-4 py-3 text-left w-10">#</th>
                <th className="px-4 py-3 text-left">Province / City</th>
                <th className="px-4 py-3 text-left w-40">
                  <span className="flex items-center gap-1">
                    Score <Tooltip text={METRIC_TOOLTIPS.score} />
                  </span>
                </th>
                <th className="px-4 py-3 text-left">
                  <span className="flex items-center gap-1">
                    Signal <Tooltip text={METRIC_TOOLTIPS.signal} />
                  </span>
                </th>
                <th className="px-4 py-3 text-right">
                  <span className="flex items-center justify-end gap-1">
                    Price/m² <Tooltip text={METRIC_TOOLTIPS.price} />
                  </span>
                </th>
                <th className="px-4 py-3 text-right">
                  <span className="flex items-center justify-end gap-1">
                    Yield <Tooltip text={METRIC_TOOLTIPS.yield} />
                  </span>
                </th>
                <th className="px-4 py-3 text-right">
                  <span className="flex items-center justify-end gap-1">
                    1Y Est. <Tooltip text={METRIC_TOOLTIPS.appreciation} />
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {topDistricts.map((d, i) => (
                <tr key={d.code} className={`border-b border-gray-50 hover:bg-gray-50 transition-colors ${i === 0 ? 'bg-yellow-50/40' : ''}`}>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-bold ${i === 0 ? 'text-yellow-500' : i === 1 ? 'text-gray-400' : i === 2 ? 'text-orange-400' : 'text-gray-200'}`}>
                      #{d.rank}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-gray-800">{d.name}</div>
                    <div className="text-xs text-gray-400 capitalize mt-0.5">{d.district_type}</div>
                  </td>
                  <td className="px-4 py-3 w-40">
                    <ScoreBadge value={d.overall_score} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${REC_COLORS[d.recommendation]}`}>
                      {REC_LABELS[d.recommendation]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-medium text-gray-700">
                      {d.avg_sale_price_per_m2 ? `${(d.avg_sale_price_per_m2 / 1_000_000).toFixed(0)}M` : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className={`font-semibold ${d.estimated_rental_yield >= 5 ? 'text-green-600' : d.estimated_rental_yield >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
                      {d.estimated_rental_yield ? `${d.estimated_rental_yield.toFixed(1)}%` : '—'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-semibold text-blue-600">
                      {d.estimated_appreciation_1y != null ? `+${d.estimated_appreciation_1y.toFixed(1)}%` : '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 text-xs text-gray-400 rounded-b-xl">
          * Yield and appreciation are model-based estimates. Always conduct independent due diligence before investing.
        </div>
      </div>
    </div>
  )
}
