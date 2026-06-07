# Frontend Design Skill

Guides design and UI work for the VN Real Estate Intelligence platform.
Invoke with `/frontend-design <subcommand>`.

## Stack
- **React 18** + **Vite** — component framework
- **Tailwind CSS** — utility-first styling (no custom CSS files)
- **Lucide React** — icons (`import { IconName } from 'lucide-react'`)
- **Recharts** — charts and data visualization
- **Zustand** — global auth state (`useAuthStore`)
- **React Router v6** — routing (`useNavigate`, `Link`)
- **Axios** — API calls via `frontend/src/services/api.js`

## Design System

### Colors (Tailwind classes)
| Role | Class |
|------|-------|
| Primary action | `bg-blue-600 hover:bg-blue-700 text-white` |
| Success / subscribed | `bg-green-600`, `text-green-700`, `bg-green-50` |
| Warning / hold | `bg-yellow-100 text-yellow-700` |
| Danger / avoid | `bg-red-100 text-red-700` |
| Card background | `bg-white border border-gray-100 shadow-sm rounded-xl` |
| Page background | `bg-gray-50` (set by Layout) |
| Muted text | `text-gray-400` |
| Body text | `text-gray-700` |
| Headings | `text-gray-900 font-bold` |

### Spacing & Layout
- Page content: `space-y-6` between sections
- Cards: `p-4` or `p-5` padding, `rounded-xl`, `shadow-sm`
- Card headers: `p-4 border-b border-gray-100` with icon + title
- Tables: `text-sm`, header row `bg-gray-50 text-xs text-gray-400 uppercase`
- Max content width for forms/detail pages: `max-w-2xl`

### Typography
- Page title: `text-2xl font-bold text-gray-900`
- Section title: `text-xl font-semibold text-gray-800`
- Card title: `font-semibold text-gray-800 text-sm`
- Description/sub: `text-sm text-gray-400`
- Labels: `text-sm font-medium text-gray-700`

### Icons
Always use Lucide React. Common icons in use:
`Home, TrendingUp, DollarSign, MapPin, Award, Bell, BellOff, Send,`
`Settings, LogOut, RefreshCw, ChevronDown, Search, Info, Building2,`
`CheckCircle, XCircle, Clock, BarChart2, MessageSquare`

### Buttons
```jsx
// Primary
<button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50">

// Secondary / outline
<button className="bg-white border border-gray-200 hover:border-blue-400 hover:text-blue-600 text-gray-600 px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-all">

// Danger
<button className="bg-white border border-gray-200 hover:border-red-300 hover:text-red-600 text-gray-500 px-4 py-2 rounded-lg text-sm font-medium transition-colors">
```

### Form inputs
```jsx
<input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
```

### Stat cards
```jsx
<div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
  <div className="w-8 h-8 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center mb-3">
    <Icon size={16} />
  </div>
  <div className="text-xl font-bold text-gray-900">{value}</div>
  <div className="text-xs font-medium text-gray-500 mt-0.5">{label}</div>
  <div className="text-xs text-gray-400 mt-1">{sub}</div>
</div>
```

### Tooltip pattern
```jsx
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
```

### Info / alert banners
```jsx
// Info (blue)
<div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-4">
  <div className="flex items-center gap-2 mb-2">
    <Info size={14} className="text-blue-500" />
    <span className="text-sm font-semibold text-blue-800">Title</span>
  </div>
  <p className="text-xs text-blue-700">Description</p>
</div>

// Success (green)
<div className="px-4 py-3 rounded-lg text-sm bg-green-50 text-green-700">{msg}</div>

// Error (red)
<div className="px-4 py-3 rounded-lg text-sm bg-red-50 text-red-700">{msg}</div>
```

---

## Subcommands

| Subcommand | Action |
|------------|--------|
| `new-page` | Scaffold a new page component with standard layout |
| `new-chart` | Add a Recharts chart to an existing page |
| `improve` | Improve the design of an existing page/component |
| `review` | Review a component for design consistency |

---

## When invoked: `new-page`

1. Ask: what is the page name and purpose?
2. Create `frontend/src/pages/<PageName>.jsx` using the standard template below
3. Add the route in `frontend/src/App.jsx`
4. Add a sidebar link in `frontend/src/components/Layout/Sidebar.jsx` with an appropriate Lucide icon

**Standard page template:**
```jsx
import { useEffect, useState } from 'react'
import { <Icon> } from 'lucide-react'

export default function <PageName>Page() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)

  useEffect(() => {
    // fetch data
    setLoading(false)
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Page Title</h1>
        <p className="text-gray-400 text-sm mt-1">Page description</p>
      </div>

      {/* Content cards */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-4 border-b border-gray-100 flex items-center gap-2">
          <Icon size={18} className="text-blue-500" />
          <h2 className="font-semibold text-gray-800">Section Title</h2>
        </div>
        <div className="p-4">
          {/* content */}
        </div>
      </div>
    </div>
  )
}
```

---

## When invoked: `new-chart`

1. Ask: what data to visualize, what chart type (line, bar, area, pie)?
2. Import from recharts: `import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'`
3. Wrap chart in `<ResponsiveContainer width="100%" height={300}>`
4. Use colors: primary `#3b82f6` (blue-500), secondary `#10b981` (green-500), accent `#f59e0b` (amber-500)
5. Format VND values: divide by 1_000_000, append "M"

---

## When invoked: `improve`

1. Read the target component file
2. Check against the design system above for inconsistencies
3. Improve: spacing, typography hierarchy, empty states, loading states, color usage, responsiveness
4. Add tooltips to any metric that needs explanation
5. Ensure mobile-friendly (use `grid-cols-1 md:grid-cols-2` etc.)

---

## When invoked: `review`

Read the component and report:
- Inconsistencies with the design system (colors, spacing, typography)
- Missing loading/empty states
- Missing error handling in UI
- Accessibility issues (missing labels, low contrast)
- Suggestions for improvement