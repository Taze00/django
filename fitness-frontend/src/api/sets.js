import client from './client';

export const setAPI = {
  create: (data) => {
    // POST to /workouts/{workout_id}/add_set/
    const workoutId = data.workout;
    return client.post(`/workouts/${workoutId}/add_set/`, data);
  },

  update: (id, data) => {
    // POST to /workouts/{workout_id}/add_set/ (backend uses update_or_create, no PUT needed)
    const workoutId = data.workout;
    return client.post(`/workouts/${workoutId}/add_set/`, data);
  },

  delete: (id) => client.delete(`/workouts/sets/${id}/`),
};
