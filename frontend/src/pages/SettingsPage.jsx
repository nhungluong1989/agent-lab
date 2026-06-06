import { useState, useEffect } from 'react'
import { authApi } from '../services/api'
import useAuthStore from '../store/authStore'

export default function SettingsPage() {
  const { user, setUser } = useAuthStore()
  const [form, setForm] = useState({ full_name: '', email: '', role: 'investor', email_notifications: true })
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)

  useEffect(() => {
    authApi.me().then(r => {
      setForm({
        full_name: r.data.full_name || '',
        email: r.data.email || '',
        role: r.data.role || 'investor',
        email_notifications: r.data.email_notifications ?? true,
      })
    })
  }, [])

  const save = async () => {
    setSaving(true)
    setMsg(null)
    try {
      const r = await authApi.updateMe(form)
      setUser(r.data)
      setMsg({ type: 'success', text: 'Settings saved.' })
    } catch {
      setMsg({ type: 'error', text: 'Failed to save.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-lg space-y-6">
      <h1 className="text-xl font-bold text-gray-900">Settings</h1>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 space-y-4">
        <h2 className="font-semibold text-gray-700">Profile</h2>

        {[['Full Name', 'full_name', 'text'], ['Email', 'email', 'email']].map(([label, key, type]) => (
          <div key={key}>
            <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
            <input type={type} value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
          </div>
        ))}

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Investor Role</label>
          <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:border-blue-400">
            <option value="buyer">Buyer</option>
            <option value="seller">Seller</option>
          </select>
        </div>

        <label className="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" checked={form.email_notifications}
            onChange={e => setForm(f => ({ ...f, email_notifications: e.target.checked }))}
            className="w-4 h-4 rounded" />
          <span className="text-sm text-gray-700">Daily market summary emails</span>
        </label>
      </div>

      {msg && (
        <div className={`text-sm px-4 py-2 rounded-lg ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
        </div>
      )}

      <button onClick={save} disabled={saving}
        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors">
        {saving ? 'Saving…' : 'Save Settings'}
      </button>
    </div>
  )
}
