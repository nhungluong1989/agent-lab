import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

export default function DepositRatesChart({ data, loading }) {
  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400 text-sm">Loading...</div>
  if (!data?.data?.length) return <div className="h-64 flex items-center justify-center text-gray-400 text-sm">No data available. Try refreshing.</div>

  const { data: chartData, banks } = data

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="term_label" tick={{ fontSize: 12 }} />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `${v}%`}
          domain={['auto', 'auto']}
        />
        <Tooltip formatter={(v) => [`${v?.toFixed(2)}%`, '']} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {banks.map((bank, i) => (
          <Line
            key={bank}
            type="monotone"
            dataKey={bank}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
