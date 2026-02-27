import client from './client';

export const workoutAPI = {
  list: () => client.get('/workouts/'),

  get: (id) => client.get(`/workouts/${id}/`),

  create: (data) => client.post('/workouts/', data),

  update: (id, data) =>
    client.put(`/workouts/${id}/`, data),

  delete: (id) => client.delete(`/workouts/${id}/`),

  current: () => client.get('/workouts/current/'),

  complete: (id) =>
    client.post(`/workouts/${id}/complete/`),

  getWarmup: (id) =>
    client.get(`/workouts/${id}/warmup/`),

  updateWarmup: (id, data) =>
    client.put(`/workouts/${id}/warmup/`, data),

  lastPerformance: () => client.get('/workouts/last_performance/'),
};
