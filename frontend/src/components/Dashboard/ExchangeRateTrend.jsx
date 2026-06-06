import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'
import { format, parseISO } from 'date-fns'

export default function ExchangeRateTrend({ data, loading }) {
  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
  if (!data?.length) return <div className="h-64 flex items-center justify-center text-gray-400 text-sm">No trend data. Run a crawl first.</div>

  const formatDate = (d) => {
    try { return format(parseISO(d), 'dd/MM') } catch { return d }
  }

  const minY = Math.min(...data.map((d) => d.buy)) * 0.999
  const maxY = Math.max(...data.map((d) => d.sell)) * 1.001

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
        <defs>
          <linearGradient id="sellGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fontSize: 11 }} />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={(v) => v.toLocaleString('vi-VN')}
          domain={[minY, maxY]}
          width={70}
        />
        <Tooltip
          formatter={(v, name) => [v.toLocaleString('vi-VN') + ' VND', name]}
          labelFormatter={(l) => { try { return format(parseISO(l), 'dd MMM yyyy') } catch { return l } }}
        />
        <Area type="monotone" dataKey="sell" stroke="#3b82f6" fill="url(#sellGrad)"
          strokeWidth={2} name="Sell" dot={false} />
        <Area type="monotone" dataKey="buy" stroke="#10b981" fill="none"
          strokeWidth={1.5} strokeDasharray="4 2" name="Buy" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}
