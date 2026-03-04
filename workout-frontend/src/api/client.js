import axios from 'axios'
import { workoutStore } from '../store/workoutStore'

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Add Authorization header
client.interceptors.request.use(
  (config) => {
    const { token } = workoutStore.getState()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor: Handle 401 and refresh token
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response } = error
    if (response?.status === 401) {
      const { refreshToken } = workoutStore.getState()
      if (refreshToken) {
        try {
          const refreshResponse = await axios.post('/api/token/refresh/', {
            refresh: refreshToken,
          })
          const { access } = refreshResponse.data
          workoutStore.setState({ token: access })

          // Retry original request
          error.config.headers.Authorization = `Bearer ${access}`
          return client(error.config)
        } catch (refreshError) {
          // Refresh failed, logout
          workoutStore.setState({
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            user: null,
          })
          return Promise.reject(refreshError)
        }
      }
    }
    return Promise.reject(error)
  }
)

export default client
