import client from './client';

export const authAPI = {
  login: (username, password) =>
    client.post('/auth/login/', { username, password }),

  refresh: (refreshToken) =>
    client.post('/auth/refresh/', { refresh: refreshToken }),

  me: () => client.get('/user/me/'),

  profile: () => client.get('/user/profile/'),

  updateProfile: (data) =>
    client.put('/user/profile/', data),
};
