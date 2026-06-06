import { useNavigate } from 'react-router-dom'
import { LogOut, User } from 'lucide-react'
import useAuthStore from '../../store/authStore'

const ROLE_STYLES = {
  buyer:    { color: 'bg-blue-100 text-blue-700',   icon: '🏠', label: 'Buyer' },
  seller:   { color: 'bg-green-100 text-green-700', icon: '🏢', label: 'Seller' },
  investor: { color: 'bg-purple-100 text-purple-700', icon: '📈', label: 'Investor' },
  analyst:  { color: 'bg-orange-100 text-orange-700', icon: '🔍', label: 'Analyst' },
}

export default function Navbar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const role = ROLE_STYLES[user?.role?.toLowerCase()] || { color: 'bg-gray-100 text-gray-600', icon: '👤', label: user?.role || 'User' }

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
      <div className="text-sm font-medium text-gray-600">
        Vietnam Real Estate <span className="text-blue-600 font-semibold">Market Intelligence</span> Platform
      </div>
      <div className="flex items-center gap-3">
        {user && (
          <>
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center">
                <User size={14} className="text-blue-600" />
              </div>
              <span className="text-sm font-medium text-gray-700">{user.username}</span>
              <span className={`badge ${role.color}`}>
                {role.icon} {role.label}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors rounded"
              title="Logout"
            >
              <LogOut size={16} />
            </button>
          </>
        )}
      </div>
    </header>
  )
}
