import { NavLink } from 'react-router-dom'
import { LayoutDashboard, MapPin, List, BarChart3, MessageSquare, Bell, Settings, Building2 } from 'lucide-react'

const links = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/provinces', icon: MapPin, label: 'Provinces' },
  { to: '/listings', icon: List, label: 'Listings' },
  { to: '/opportunities', icon: BarChart3, label: 'Opportunities' },
  { to: '/chat', icon: MessageSquare, label: 'AI Advisor' },
  { to: '/notifications', icon: Bell, label: 'Notifications' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 bg-gray-900 text-white flex flex-col shrink-0">
      <div className="p-5 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Building2 className="text-blue-400" size={22} />
          <div>
            <div className="font-bold text-sm leading-tight">VN Real Estate</div>
            <div className="text-gray-400 text-xs">Investment Intelligence</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-700 text-xs text-gray-500">
        Data: Chotot · Updated daily
      </div>
    </aside>
  )
}
