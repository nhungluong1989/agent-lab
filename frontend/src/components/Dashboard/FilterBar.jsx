const CURRENCIES = ['USD', 'EUR', 'JPY', 'GBP', 'CNY', 'AUD', 'SGD']
const TREND_DAYS = [7, 14, 30, 60, 90]

export default function FilterBar({ banks, filters, onChange }) {
  const toggleBank = (code) => {
    const next = filters.banks.includes(code)
      ? filters.banks.filter((b) => b !== code)
      : [...filters.banks, code]
    onChange({ ...filters, banks: next })
  }

  return (
    <div className="card flex flex-wrap gap-6 items-center">
      <div>
        <p className="text-xs text-gray-500 mb-2 font-medium">Filter Banks</p>
        <div className="flex flex-wrap gap-2">
          {banks.map((b) => (
            <button
              key={b.code}
              onClick={() => toggleBank(b.code)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                filters.banks.includes(b.code)
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
              }`}
            >
              {b.code}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-2 font-medium">Currency</p>
        <select
          className="input w-28 text-sm"
          value={filters.currency}
          onChange={(e) => onChange({ ...filters, currency: e.target.value })}
        >
          {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>

      <div>
        <p className="text-xs text-gray-500 mb-2 font-medium">Trend Period</p>
        <select
          className="input w-24 text-sm"
          value={filters.trendDays}
          onChange={(e) => onChange({ ...filters, trendDays: Number(e.target.value) })}
        >
          {TREND_DAYS.map((d) => <option key={d} value={d}>{d} days</option>)}
        </select>
      </div>
    </div>
  )
}
