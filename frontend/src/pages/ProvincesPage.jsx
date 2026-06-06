import { useEffect, useState } from 'react'
import { analyticsApi } from '../services/api'

const REC_COLORS = { strong_buy: 'bg-green-100 text-green-800', buy: 'bg-blue-100 text-blue-800', hold: 'bg-yellow-100 text-yellow-700', avoid: 'bg-red-100 text-red-800' }
const REC_LABELS = { strong_buy: 'Strong Buy', buy: 'Buy', hold: 'Hold', avoid: 'Avoid' }

function ScoreCircle({ value, size = 48 }) {
  const color = value >= 70 ? '#22c55e' : value >= 55 ? '#3b82f6' : value >= 40 ? '#f59e0b' : '#ef4444'
  const r = 18, circ = 2 * Math.PI * r
  const dash = ((value || 0) / 100) * circ
  return (
    <svg width={size} height={size} viewBox="0 0 44 44">
      <circle cx="22" cy="22" r={r} fill="none" stroke="#f1f5f9" strokeWidth="4" />
      <circle cx="22" cy="22" r={r} fill="none" stroke={color} strokeWidth="4"
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        transform="rotate(-90 22 22)" />
      <text x="22" y="26" textAnchor="middle" fontSize="9" fontWeight="bold" fill={color}>
        {value?.toFixed(0) ?? '—'}
      </text>
    </svg>
  )
}

export default function ProvincesPage() {
  const [provinces, setProvinces] = useState([])
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sort, setSort] = useState('overall_score')
  const [filter, setFilter] = useState('')

  useEffect(() => {
    analyticsApi.getAllDistricts().then(r => setProvinces(r.data)).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!selected) return
    analyticsApi.getDistrictDetail(selected).then(r => setDetail(r.data))
  }, [selected])

  const provinceOptions = [...provinces].sort((a, b) => a.name.localeCompare(b.name, 'vi'))

  const sorted = [...provinces]
    .filter(d => !filter || String(d.code) === filter)
    .sort((a, b) => (b[sort] || 0) - (a[sort] || 0))

  const fmtM = (n) => n ? `${(n / 1_000_000).toFixed(0)}M` : '—'
  const fmtRent = (n) => n ? `${(n / 1_000_000).toFixed(1)}M` : '—'

  return (
    <div className="flex gap-4 h-full">
      {/* Province list */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-gray-900">Provinces</h1>
          <div className="flex gap-2">
            <select
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white min-w-[180px]"
              value={filter}
              onChange={e => {
                setFilter(e.target.value)
                if (e.target.value) setSelected(Number(e.target.value))
              }}
            >
              <option value="">Search province...</option>
              {provinceOptions.map(p => (
                <option key={p.code} value={p.code}>{p.name}</option>
              ))}
            </select>
            <select
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
              value={sort}
              onChange={e => setSort(e.target.value)}
            >
              <option value="overall_score">Overall Score</option>
              <option value="capital_appreciation_score">Capital Appreciation</option>
              <option value="rental_income_score">Rental Income</option>
              <option value="avg_sale_price_per_m2">Price/m²</option>
              <option value="supply_count">Listings</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div className="text-gray-400 text-center py-12">Loading...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {sorted.map(d => (
              <div key={d.code}
                onClick={() => {
                  setSelected(d.code === selected ? null : d.code)
                  setFilter(d.code === selected ? '' : String(d.code))
                }}
                className={`bg-white rounded-xl p-4 shadow-sm border cursor-pointer transition-all ${d.code === selected ? 'border-blue-400 shadow-blue-100' : 'border-gray-100 hover:border-gray-200'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-semibold text-gray-800">{d.name}</div>
                    <div className="text-xs text-gray-400 capitalize mb-2">{d.district_type}</div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-gray-600">
                      <div>Price/m²: <span className="font-medium">{fmtM(d.avg_sale_price_per_m2)}</span></div>
                      <div>Yield: <span className="font-medium text-green-600">{d.estimated_rental_yield ? `${d.estimated_rental_yield.toFixed(1)}%` : '—'}</span></div>
                      <div>Listings: <span className="font-medium">{d.supply_count ?? '—'}</span></div>
                      <div>Apprec.: <span className="font-medium text-blue-600">{d.estimated_appreciation_1y != null ? `+${d.estimated_appreciation_1y.toFixed(1)}%` : '—'}</span></div>
                    </div>
                  </div>
                  <div className="flex flex-col items-center gap-1 ml-3">
                    <ScoreCircle value={d.overall_score} />
                    {d.recommendation && (
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${REC_COLORS[d.recommendation]}`}>
                        {REC_LABELS[d.recommendation]}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selected && detail && (
        <div className="w-80 shrink-0 bg-white rounded-xl shadow-sm border border-gray-100 p-5 h-fit sticky top-4 space-y-4 overflow-y-auto max-h-screen">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-gray-800">{detail.name}</h2>
            <button onClick={() => { setSelected(null); setFilter('') }} className="text-gray-400 hover:text-gray-600 text-lg leading-none">×</button>
          </div>

          {detail.score && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Investment Scores</div>
              {[
                ['Overall', detail.score.overall_score, 'bg-blue-500'],
                ['Capital Appreciation', detail.score.capital_appreciation_score, 'bg-purple-500'],
                ['Rental Income', detail.score.rental_income_score, 'bg-green-500'],
                ['Growth', detail.score.growth_score, 'bg-teal-500'],
                ['Liquidity', detail.score.liquidity_score, 'bg-orange-400'],
                ['Risk', detail.score.risk_score, 'bg-red-400'],
              ].map(([label, val, color]) => (
                <div key={label}>
                  <div className="flex justify-between text-xs text-gray-600 mb-0.5">
                    <span>{label}</span><span className="font-medium">{val?.toFixed(0) ?? '—'}</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full">
                    <div className={`${color} h-1.5 rounded-full`} style={{ width: `${val || 0}%` }} />
                  </div>
                </div>
              ))}

              <div className="pt-2 grid grid-cols-3 gap-2 text-center">
                {[['Short', detail.score.short_term_score], ['Medium', detail.score.medium_term_score], ['Long', detail.score.long_term_score]].map(([t, v]) => (
                  <div key={t} className="bg-gray-50 rounded-lg p-2">
                    <div className="text-xs text-gray-400">{t} term</div>
                    <div className="font-bold text-gray-800">{v?.toFixed(0) ?? '—'}</div>
                  </div>
                ))}
              </div>

              {detail.score.strengths?.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-green-600 mb-1">Strengths</div>
                  {detail.score.strengths.map((s, i) => <div key={i} className="text-xs text-gray-600 flex gap-1"><span className="text-green-500">✓</span>{s}</div>)}
                </div>
              )}
              {detail.score.risks?.length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-red-500 mb-1">Risks</div>
                  {detail.score.risks.map((r, i) => <div key={i} className="text-xs text-gray-600 flex gap-1"><span className="text-red-400">!</span>{r}</div>)}
                </div>
              )}
            </div>
          )}

          {detail.metrics && (
            <div className="space-y-2 border-t pt-4">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Market Metrics</div>
              {[
                ['Avg Sale Price/m²', fmtM(detail.metrics.avg_sale_price_per_m2)],
                ['Avg Rental/month', fmtRent(detail.metrics.avg_rental_monthly)],
                ['Rental Yield', detail.metrics.rental_yield ? `${detail.metrics.rental_yield.toFixed(1)}%` : '—'],
                ['Price/Income Ratio', detail.metrics.price_to_income_ratio ? `${detail.metrics.price_to_income_ratio}x` : '—'],
                ['Sale Listings', detail.metrics.supply_count ?? '—'],
                ['Rental Listings', detail.metrics.rental_count ?? '—'],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between text-xs">
                  <span className="text-gray-500">{k}</span>
                  <span className="font-medium text-gray-800">{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
