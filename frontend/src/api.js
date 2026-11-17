// Every backend call goes through this file.
// Success:  { success: true,  data: ..., request_id }
// Failure:  { success: false, error: { code, message, details }, request_id }
import axios from 'axios'

const TOKEN_KEY = 'clinical-ai-token'
let token = sessionStorage.getItem(TOKEN_KEY)
let onUnauthorized = () => {}

export const api = axios.create({ baseURL: '/api', timeout: 180_000 })

api.interceptors.request.use((config) => {
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const body = err.response?.data
    const e = new Error(body?.error?.message || (err.code === 'ECONNABORTED' ? 'Request timed out' : err.message))
    e.code = body?.error?.code || 'NETWORK_ERROR'
    e.status = err.response?.status
    e.requestId = body?.request_id
    if (e.status === 401 && token) onUnauthorized()
    return Promise.reject(e)
  },
)

export function setToken(t) {
  token = t
  if (t) sessionStorage.setItem(TOKEN_KEY, t)
  else sessionStorage.removeItem(TOKEN_KEY)
}
export const hasToken = () => Boolean(token)
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

export const getHealth = () => api.get('/health').then((r) => r.data.data)

export async function login(username, password) {
  const r = await api.post('/auth/login', { username, password })
  setToken(r.data.data.access_token)
  return r.data.data
}

export function extractPdf(file, onUploadProgress) {
  const form = new FormData()
  form.append('file', file)
  return api
    .post('/extract', form, {
      onUploadProgress: (e) => onUploadProgress?.(Math.round((100 * e.loaded) / (e.total || file.size || 1))),
    })
    .then((r) => r.data.data)
}

export const listExtractions = () => api.get('/extractions').then((r) => r.data.data)
export const getExtraction = (id) => api.get(`/extractions/${id}`).then((r) => r.data.data)
