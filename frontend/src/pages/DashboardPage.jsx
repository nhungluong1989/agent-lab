import { useEffect, useState, useRef } from 'react'
import { analyticsApi, listingsApi } from '../services/api'
import { TrendingUp, Home, DollarSign, MapPin, Award, RefreshCw, Building2 } from 'lucide-react'

const REC_COLORS = {
  strong_buy: 'bg-green-100 text-green-800',
  buy: 'bg-blue-100 text-blue-800',
  hold: 'bg-yellow-100 text-yellow-700',
  avoid: 'bg-red-100 text-red-800',
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

function ScoreBar({ value, color = 'bg-blue-500' }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${value || 0}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-8 text-right">{value?.toFixed(0) ?? '—'}</span>
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
    <div className="flex items-center justify-center h-64 text-gray-400">Loading market data...</div>
  )

  const fmtM = (n) => n ? `${(n / 1_000_000).toFixed(0)}M` : '—'
  const fmtRent = (n) => n ? `${(n / 1_000_000).toFixed(1)}M` : '—'

  const saleTypes = ['apartment', 'house', 'villa', 'land']
  const rentTypes = ['apartment', 'house', 'room']

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Vietnam Real Estate Intelligence</h1>
          <p className="text-gray-500 text-sm mt-1">
            Live data from {listingSummary?.total_listings?.toLocaleString() ?? '…'} active listings across all 63 provinces
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

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 text-blue-600 mb-2">
            <Home size={18} />
            <span className="text-xs font-medium uppercase tracking-wide">Total Listings</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{listingSummary?.total_listings?.toLocaleString() ?? '—'}</div>
          <div className="text-xs text-gray-400 mt-1">
            {listingSummary?.sale_listings?.toLocaleString() ?? 0} sale · {listingSummary?.rent_listings?.toLocaleString() ?? 0} rent
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="flex items-center gap-2 text-orange-600 mb-2">
            <MapPin size={18} />
            <span className="text-xs font-medium uppercase tracking-wide">Provinces Scored</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{summary?.districts_scored ?? '—'}</div>
          <div className="text-xs text-gray-400 mt-1">
            {summary?.recommendation_breakdown?.strong_buy ?? 0} strong buy · {summary?.recommendation_breakdown?.buy ?? 0} buy
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 col-span-2 md:col-span-1">
          <div className="flex items-center gap-2 text-purple-600 mb-2">
            <TrendingUp size={18} />
            <span className="text-xs font-medium uppercase tracking-wide">Market Signal</span>
          </div>
          <div className="flex gap-2 flex-wrap mt-1">
            {Object.entries(summary?.recommendation_breakdown ?? {}).map(([rec, count]) => (
              <span key={rec} className={`px-2 py-0.5 rounded-full text-xs font-medium ${REC_COLORS[rec]}`}>
                {REC_LABELS[rec]}: {count}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Price breakdown by property type */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100 flex items-center gap-2">
            <DollarSign size={18} className="text-purple-500" />
            <h2 className="font-semibold text-gray-800 text-sm">Avg Sale Price / m²</h2>
          </div>
          <div className="divide-y divide-gray-50">
            {saleTypes.map(pt => (
              <div key={pt} className="px-4 py-3 flex items-center justify-between">
                <span className="text-sm text-gray-600 capitalize">{PROP_TYPE_LABELS[pt]}</span>
                <span className="text-sm font-semibold text-gray-900">
                  {fmtM(summary?.sale_price_by_type?.[pt])}
                  {summary?.sale_price_by_type?.[pt] ? <span className="text-xs text-gray-400 font-normal"> /m²</span> : ''}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100 flex items-center gap-2">
            <Building2 size={18} className="text-green-500" />
            <h2 className="font-semibold text-gray-800 text-sm">Avg Rental / Month</h2>
          </div>
          <div className="divide-y divide-gray-50">
            {rentTypes.map(pt => (
              <div key={pt} className="px-4 py-3 flex items-center justify-between">
                <span className="text-sm text-gray-600 capitalize">{PROP_TYPE_LABELS[pt]}</span>
                <span className="text-sm font-semibold text-gray-900">
                  {fmtRent(summary?.rent_by_type?.[pt])}
                  {summary?.rent_by_type?.[pt] ? <span className="text-xs text-gray-400 font-normal"> /tháng</span> : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top opportunities table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-4 border-b border-gray-100 flex items-center gap-2">
          <Award size={18} className="text-yellow-500" />
          <h2 className="font-semibold text-gray-800">Top 10 Investment Opportunities</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 uppercase border-b border-gray-50 bg-gray-50">
                <th className="px-4 py-3 text-left w-12">#</th>
                <th className="px-4 py-3 text-left">Province / City</th>
                <th className="px-4 py-3 text-left w-36">Score</th>
                <th className="px-4 py-3 text-left">Signal</th>
                <th className="px-4 py-3 text-right">Price/m²</th>
                <th className="px-4 py-3 text-right">Yield</th>
                <th className="px-4 py-3 text-right">Appreciation</th>
              </tr>
            </thead>
            <tbody>
              {topDistricts.map((d) => (
                <tr key={d.code} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-bold text-gray-300">#{d.rank}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-800">{d.name}</div>
                    <div className="text-xs text-gray-400 capitalize">{d.district_type}</div>
                  </td>
                  <td className="px-4 py-3 w-36">
                    <ScoreBar value={d.overall_score} color={d.overall_score >= 70 ? 'bg-green-500' : d.overall_score >= 50 ? 'bg-blue-500' : 'bg-gray-400'} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${REC_COLORS[d.recommendation]}`}>
                      {REC_LABELS[d.recommendation]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {d.avg_sale_price_per_m2 ? `${(d.avg_sale_price_per_m2 / 1_000_000).toFixed(0)}M` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right text-green-600 font-medium">
                    {d.estimated_rental_yield ? `${d.estimated_rental_yield.toFixed(1)}%` : '—'}
                  </td>
                  <td className="px-4 py-3 text-right text-blue-600 font-medium">
                    {d.estimated_appreciation_1y != null ? `+${d.estimated_appreciation_1y.toFixed(1)}%` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
