import { ArrowUpDown } from 'lucide-react'
import { useState } from 'react'

export default function ExchangeComparisonTable({ data, loading }) {
  const [sortBy, setSortBy] = useState('sell')
  const [asc, setAsc] = useState(true)

  if (loading) return <div className="h-20 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
  if (!data?.length) return <div className="h-20 flex items-center justify-center text-gray-400 text-sm">No data available.</div>

  const sorted = [...data].sort((a, b) => {
    const diff = (a[sortBy] ?? 0) - (b[sortBy] ?? 0)
    return asc ? diff : -diff
  })

  const handleSort = (col) => {
    if (sortBy === col) setAsc(!asc)
    else { setSortBy(col); setAsc(true) }
  }

  const best = Math.min(...data.map((d) => d.sell ?? Infinity))

  const Th = ({ col, label }) => (
    <th
      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase cursor-pointer
                 hover:text-gray-700 select-none"
      onClick={() => handleSort(col)}
    >
      <span className="flex items-center gap-1">
        {label}
        <ArrowUpDown size={12} className={sortBy === col ? 'text-blue-500' : 'text-gray-300'} />
      </span>
    </th>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-100">
          <tr>
            <Th col="bank_code" label="Bank" />
            <Th col="buy" label="Buy (Transfer)" />
            <Th col="sell" label="Sell" />
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50">
          {sorted.map((row) => (
            <tr key={row.bank_code} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-semibold text-gray-800">{row.bank_code}</td>
              <td className="px-4 py-3 text-gray-600">
                {row.buy?.toLocaleString('vi-VN') ?? '—'}
              </td>
              <td className="px-4 py-3 font-medium">
                <span className={row.sell === best ? 'text-green-600' : 'text-gray-800'}>
                  {row.sell?.toLocaleString('vi-VN') ?? '—'}
                </span>
              </td>
              <td className="px-4 py-3">
                {row.sell === best && (
                  <span className="badge bg-green-100 text-green-700">Lowest sell</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
