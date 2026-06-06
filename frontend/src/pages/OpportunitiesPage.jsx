import { useEffect, useState } from 'react'
import { analyticsApi } from '../services/api'
import { TrendingUp, Shield, Star, Clock } from 'lucide-react'

const REC_COLORS = { strong_buy: 'bg-green-500', buy: 'bg-blue-500', hold: 'bg-yellow-400', avoid: 'bg-red-400' }
const REC_TEXT = { strong_buy: 'text-green-700 bg-green-50', buy: 'text-blue-700 bg-blue-50', hold: 'text-yellow-700 bg-yellow-50', avoid: 'text-red-700 bg-red-50' }
const REC_LABELS = { strong_buy: 'STRONG BUY', buy: 'BUY', hold: 'HOLD', avoid: 'AVOID' }

function MiniBar({ value, max = 100, color = 'bg-blue-500' }) {
  return (
    <div className="h-1.5 bg-gray-100 rounded-full w-full">
      <div className={`${color} h-1.5 rounded-full`} style={{ width: `${(value / max) * 100}%` }} />
    </div>
  )
}

export default function OpportunitiesPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    const rec = filter === 'all' ? undefined : filter
    analyticsApi.getTopOpportunities(20, rec)
      .then(r => setItems(r.data))
      .finally(() => setLoading(false))
  }, [filter])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Investment Opportunities</h1>
          <p className="text-gray-400 text-sm">Ranked by overall investment score across all HCMC districts</p>
        </div>
        <div className="flex gap-1">
          {['all', 'strong_buy', 'buy', 'hold'].map(f => (
            <button key={f} onClick={() => { setFilter(f); setLoading(true) }}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'}`}>
              {f === 'all' ? 'All' : REC_LABELS[f]}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">Loading opportunities...</div>
      ) : (
        <div className="space-y-3">
          {items.map((d) => (
            <div key={d.code} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <div className="flex items-start gap-4">
                {/* Rank + score */}
                <div className="flex flex-col items-center shrink-0 w-14">
                  <div className="text-2xl font-black text-gray-200">#{d.rank}</div>
                  <div className={`w-12 h-12 rounded-full ${REC_COLORS[d.recommendation]} flex items-center justify-center`}>
                    <span className="text-white font-bold text-sm">{d.overall_score?.toFixed(0)}</span>
                  </div>
                </div>

                {/* Main info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-gray-900">{d.name}</h3>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded ${REC_TEXT[d.recommendation]}`}>
                      {REC_LABELS[d.recommendation]}
                    </span>
                    <span className="text-xs text-gray-400 capitalize">{d.district_type}</span>
                  </div>

                  {/* Score breakdown */}
                  <div className="grid grid-cols-3 gap-3 my-3">
                    <div>
                      <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                        <TrendingUp size={11} /> Capital
                      </div>
                      <MiniBar value={d.capital_appreciation_score} color="bg-purple-500" />
                      <div className="text-xs font-medium text-gray-700 mt-0.5">{d.capital_appreciation_score?.toFixed(0)}/100</div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                        <Star size={11} /> Rental
                      </div>
                      <MiniBar value={d.rental_income_score} color="bg-green-500" />
                      <div className="text-xs font-medium text-gray-700 mt-0.5">{d.rental_income_score?.toFixed(0)}/100</div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                        <Shield size={11} /> Risk
                      </div>
                      <MiniBar value={d.risk_score} color="bg-red-400" />
                      <div className="text-xs font-medium text-gray-700 mt-0.5">{d.risk_score?.toFixed(0)}/100</div>
                    </div>
                  </div>

                  {/* Key numbers */}
                  <div className="flex gap-4 text-xs text-gray-600">
                    <div>Price/m²: <span className="font-medium text-gray-800">
                      {d.avg_sale_price_per_m2 ? `${(d.avg_sale_price_per_m2 / 1_000_000).toFixed(0)}M` : '—'}
                    </span></div>
                    <div>Rental yield: <span className="font-medium text-green-700">
                      {d.estimated_rental_yield ? `${d.estimated_rental_yield.toFixed(1)}%` : '—'}
                    </span></div>
                    <div>1Y appreciation: <span className="font-medium text-blue-700">
                      {d.estimated_appreciation_1y != null ? `+${d.estimated_appreciation_1y.toFixed(1)}%` : '—'}
                    </span></div>
                  </div>

                  {/* Strengths */}
                  {d.strengths?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {d.strengths.map((s, i) => (
                        <span key={i} className="text-xs bg-gray-50 text-gray-500 px-2 py-0.5 rounded-full">{s}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
