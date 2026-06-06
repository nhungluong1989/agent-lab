import { useEffect, useState } from 'react'
import { Bell, Send, CheckCircle, XCircle, Clock } from 'lucide-react'
import { notificationsApi } from '../services/api'

export default function NotificationsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [msg, setMsg] = useState(null)

  const fetchLogs = () => {
    setLoading(true)
    notificationsApi.getLogs()
      .then(r => setLogs(r.data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchLogs() }, [])

  const sendTest = async () => {
    setSending(true)
    setMsg(null)
    try {
      await notificationsApi.sendTest()
      setMsg({ type: 'success', text: 'Test email triggered — check your inbox in ~30 seconds.' })
      setTimeout(fetchLogs, 5000)
    } catch (err) {
      const detail = err.response?.data?.detail || 'Failed to send test email.'
      setMsg({ type: 'error', text: detail })
    } finally {
      setSending(false)
    }
  }

  const fmtDate = (s) => {
    const d = new Date(s + 'Z')
    return d.toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour12: false })
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
          <Bell size={20} className="text-blue-500" /> Email Notifications
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Daily market insight emails sent to your registered address at <span className="font-medium text-gray-600">07:00 Vietnam time</span>
        </p>
      </div>

      {/* Test button */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 flex items-center justify-between">
        <div>
          <div className="font-medium text-gray-800">Send a test email now</div>
          <div className="text-xs text-gray-400 mt-0.5">Triggers an immediate insight email to your account's registered address</div>
        </div>
        <button
          onClick={sendTest}
          disabled={sending}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
        >
          <Send size={14} />
          {sending ? 'Sending…' : 'Send Test'}
        </button>
      </div>

      {msg && (
        <div className={`px-4 py-3 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
        </div>
      )}

      {/* Log history */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <span className="font-semibold text-gray-700 text-sm">Recent emails</span>
          <button onClick={fetchLogs} className="text-xs text-blue-500 hover:underline">Refresh</button>
        </div>

        {loading ? (
          <div className="text-center text-gray-400 py-10 text-sm">Loading...</div>
        ) : logs.length === 0 ? (
          <div className="text-center text-gray-400 py-10 text-sm">No emails sent yet</div>
        ) : (
          <ul className="divide-y divide-gray-50">
            {logs.map(log => (
              <li key={log.id} className="px-5 py-3 flex items-start gap-3">
                <div className="mt-0.5 shrink-0">
                  {log.status === 'sent'
                    ? <CheckCircle size={16} className="text-green-500" />
                    : log.status === 'failed'
                    ? <XCircle size={16} className="text-red-400" />
                    : <Clock size={16} className="text-gray-300" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-gray-700 truncate">{log.subject}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{fmtDate(log.sent_at)}</div>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${
                  log.status === 'sent' ? 'bg-green-50 text-green-700' :
                  log.status === 'failed' ? 'bg-red-50 text-red-600' : 'bg-gray-50 text-gray-500'
                }`}>
                  {log.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
