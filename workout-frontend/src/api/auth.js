import client from './client'

export const login = async (username, password) => {
  const response = await client.post('/token/', { username, password })
  const { access, refresh } = response.data
  return { access, refresh }
}

export const refreshToken = async (refreshToken) => {
  const response = await client.post('/token/refresh/', { refresh: refreshToken })
  const { access } = response.data
  return { access }
}
