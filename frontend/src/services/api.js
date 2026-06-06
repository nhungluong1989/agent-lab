import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (username, password) => {
    const form = new URLSearchParams({ username, password })
    return api.post('/auth/login', form, { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
  },
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  updateMe: (data) => api.patch('/auth/me', data),
}

export const analyticsApi = {
  getMarketSummary: () => api.get('/analytics/market-summary'),
  getAllDistricts: () => api.get('/analytics/districts'),
  getDistrictDetail: (code) => api.get(`/analytics/districts/${code}`),
  getTopOpportunities: (limit = 10, recommendation) =>
    api.get('/analytics/top-opportunities', { params: { limit, recommendation } }),
  compareDistricts: (codes) => api.get('/analytics/comparison', { params: { codes } }),
  triggerRefresh: () => api.post('/analytics/refresh'),
  getRefreshStatus: () => api.get('/analytics/refresh/status'),
}

export const listingsApi = {
  getListings: (params) => api.get('/listings/', { params }),
  getDistricts: () => api.get('/listings/districts'),
  getPriceTrend: (params) => api.get('/listings/price-trend', { params }),
  getSummary: () => api.get('/listings/summary'),
}

export const chatApi = {
  send: (messages) => api.post('/chat', { messages }),
}

export const notificationsApi = {
  getLogs: () => api.get('/notifications/logs'),
  sendTest: () => api.post('/notifications/test'),
}

export default api
