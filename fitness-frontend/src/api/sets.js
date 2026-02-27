import client from './client';

export const setAPI = {
  create: (data) => {
    // POST to /workouts/{workout_id}/add_set/
    const workoutId = data.workout;
    return client.post(`/workouts/${workoutId}/add_set/`, data);
  },

  update: (id, data) => {
    // PUT to /workouts/{workout_id}/add_set/
    const workoutId = data.workout;
    return client.put(`/workouts/${workoutId}/add_set/`, data);
  },

  delete: (id) => client.delete(`/workouts/sets/${id}/`),
};
