import axios from 'axios';
import type { FetchResponse } from '../types';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
});

export const api = {
  getConfig: async () => {
    const { data } = await apiClient.get('/config');
    return data;
  },
  fetchReviews: async (): Promise<FetchResponse> => {
    const { data } = await apiClient.post<FetchResponse>('/reviews/fetch');
    return data;
  }
};
