import client from './client';

export const setAPI = {
  create: (data) => client.post('/sets/', data),

  update: (id, data) =>
    client.put(`/sets/${id}/`, data),

  delete: (id) => client.delete(`/sets/${id}/`),
};
