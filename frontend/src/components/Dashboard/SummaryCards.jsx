import { TrendingUp, DollarSign, Building2, Clock } from 'lucide-react'

export default function SummaryCards({ summary }) {
  const cards = [
    {
      icon: TrendingUp,
      color: 'text-green-600',
      bg: 'bg-green-50',
      label: 'Best 12M Deposit Rate',
      value: summary?.best_12m_deposit?.rate
        ? `${summary.best_12m_deposit.rate.toFixed(2)}%/yr`
        : '—',
      sub: summary?.best_12m_deposit?.bank ? `by ${summary.best_12m_deposit.bank}` : '',
    },
    {
      icon: DollarSign,
      color: 'text-blue-600',
      bg: 'bg-blue-50',
      label: 'USD/VND (VCB Sell)',
      value: summary?.usd_vnd_sell?.rate
        ? summary.usd_vnd_sell.rate.toLocaleString('vi-VN')
        : '—',
      sub: 'Latest rate',
    },
    {
      icon: Building2,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
      label: 'Banks Tracked',
      value: summary?.banks_tracked ?? '—',
      sub: 'Vietnamese banks',
    },
    {
      icon: Clock,
      color: 'text-orange-600',
      bg: 'bg-orange-50',
      label: 'Last Data Crawl',
      value: summary?.last_crawl
        ? new Date(summary.last_crawl + 'Z').toLocaleDateString()
        : '—',
      sub: summary?.last_crawl
        ? new Date(summary.last_crawl + 'Z').toLocaleTimeString()
        : 'Not yet',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map(({ icon: Icon, color, bg, label, value, sub }) => (
        <div key={label} className="card flex items-start gap-4">
          <div className={`${bg} p-2.5 rounded-lg shrink-0`}>
            <Icon size={20} className={color} />
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-0.5">{label}</p>
            <p className="text-xl font-bold text-gray-900">{value}</p>
            {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}
