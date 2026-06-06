import { useEffect, useState } from 'react'
import { listingsApi } from '../services/api'
import { ExternalLink, Home, Building2, Trees } from 'lucide-react'

const TYPE_ICONS = { apartment: Building2, house: Home, land: Trees, villa: Home }
const TYPE_COLORS = { apartment: 'bg-blue-50 text-blue-700', house: 'bg-green-50 text-green-700', land: 'bg-yellow-50 text-yellow-700', villa: 'bg-purple-50 text-purple-700' }

function fmt(n) { return n ? `${(n / 1_000_000_000).toFixed(2)} tỷ` : '—' }
function fmtM(n) { return n ? `${(n / 1_000_000).toFixed(0)}M/m²` : '—' }

export default function ListingsPage() {
  const [listings, setListings] = useState([])
  const [districts, setDistricts] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ listing_type: 'sale', district_code: '', property_type: '' })
  const [page, setPage] = useState(0)
  const LIMIT = 50

  useEffect(() => {
    listingsApi.getDistricts().then(r => setDistricts(r.data))
  }, [])

  useEffect(() => {
    setLoading(true)
    const params = { ...filters, limit: LIMIT, offset: page * LIMIT }
    Object.keys(params).forEach(k => { if (!params[k]) delete params[k] })
    listingsApi.getListings(params)
      .then(r => { setListings(r.data.listings); setTotal(r.data.total) })
      .finally(() => setLoading(false))
  }, [filters, page])

  const set = (k, v) => { setFilters(f => ({ ...f, [k]: v })); setPage(0) }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Property Listings</h1>
        <span className="text-sm text-gray-400">{total.toLocaleString()} results</span>
      </div>

      <div className="flex gap-2 flex-wrap">
        <select className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
          value={filters.listing_type} onChange={e => set('listing_type', e.target.value)}>
          <option value="sale">For Sale</option>
          <option value="rent">For Rent</option>
        </select>
        <select className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
          value={filters.district_code} onChange={e => set('district_code', e.target.value)}>
          <option value="">All Districts</option>
          {districts.map(d => <option key={d.code} value={d.code}>{d.name}</option>)}
        </select>
        <select className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
          value={filters.property_type} onChange={e => set('property_type', e.target.value)}>
          <option value="">All Types</option>
          <option value="apartment">Apartment</option>
          <option value="house">House</option>
          <option value="land">Land</option>
          <option value="villa">Villa</option>
        </select>
      </div>

      {loading ? (
        <div className="text-gray-400 text-center py-12">Loading listings...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {listings.map(l => {
            const Icon = TYPE_ICONS[l.property_type] || Home
            return (
              <div key={l.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:border-gray-200 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium capitalize ${TYPE_COLORS[l.property_type] || 'bg-gray-100 text-gray-600'}`}>
                    <Icon size={10} className="inline mr-1" />{l.property_type}
                  </span>
                  {l.url && (
                    <a href={l.url} target="_blank" rel="noopener noreferrer" className="text-gray-300 hover:text-blue-500">
                      <ExternalLink size={14} />
                    </a>
                  )}
                </div>

                <div className="text-sm font-medium text-gray-800 line-clamp-2 mb-2">{l.title}</div>

                <div className="text-xs text-gray-400 mb-2">
                  {[l.ward_name, l.district_name].filter(Boolean).join(', ')}
                </div>

                <div className="flex items-end justify-between">
                  <div>
                    <div className="text-lg font-bold text-gray-900">
                      {l.listing_type === 'rent'
                        ? l.price ? `${(l.price / 1_000_000).toFixed(1)}M/tháng` : '—'
                        : fmt(l.price)
                      }
                    </div>
                    {l.price_per_m2 && <div className="text-xs text-gray-400">{fmtM(l.price_per_m2)}</div>}
                  </div>
                  <div className="text-right text-xs text-gray-400">
                    {l.area_m2 && <div>{l.area_m2}m²</div>}
                    {l.bedrooms && <div>{l.bedrooms} PN</div>}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {total > LIMIT && (
        <div className="flex justify-center gap-2 pt-2">
          <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
            className="px-4 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50">Previous</button>
          <span className="px-4 py-1.5 text-sm text-gray-500">Page {page + 1} of {Math.ceil(total / LIMIT)}</span>
          <button disabled={(page + 1) * LIMIT >= total} onClick={() => setPage(p => p + 1)}
            className="px-4 py-1.5 text-sm border rounded-lg disabled:opacity-40 hover:bg-gray-50">Next</button>
        </div>
      )}
    </div>
  )
}
