import client from './client';

export const exerciseAPI = {
  list: () => client.get('/exercises/'),

  get: (id) => client.get(`/exercises/${id}/`),

  progressions: () => client.get('/progressions/'),

  userProgressions: () =>
    client.get('/user/progressions/'),

  checkUpgrades: () =>
    client.get('/user/check-upgrades/'),

  upgradeProgression: (data) =>
    client.post('/user/upgrade-progression/', data),
};
