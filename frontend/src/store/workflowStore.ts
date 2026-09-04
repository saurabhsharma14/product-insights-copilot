import { create } from 'zustand';
import type { AnalysisResults } from '../types';

interface WorkflowState {
  currentStep: number;
  batchId: string | null;
  fetchStatus: 'idle' | 'loading' | 'success' | 'error';
  fetchError: string | null;
  reviewCount: number;
  reviewPeriod: { start: string; end: string } | null;
  avgRating: number;
  analysisResults: AnalysisResults | null;
  
  setStep: (step: number) => void;
  setBatchId: (id: string) => void;
  setFetchStatus: (status: 'idle' | 'loading' | 'success' | 'error', error?: string) => void;
  setFetchResults: (count: number, start: string, end: string, rating: number) => void;
  setReviewCount: (count: number) => void;
  setAnalysisResults: (results: AnalysisResults) => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  currentStep: 1,
  batchId: null,
  fetchStatus: 'idle',
  fetchError: null,
  reviewCount: 0,
  reviewPeriod: null,
  avgRating: 0,
  analysisResults: null,
  
  setStep: (step) => set({ currentStep: step }),
  setBatchId: (id) => set({ batchId: id }),
  setFetchStatus: (status, error = undefined) => set({ fetchStatus: status, fetchError: error ?? null }),
  setFetchResults: (count, start, end, rating) => set({ 
    reviewCount: count, 
    reviewPeriod: { start, end }, 
    avgRating: rating 
  }),
  setReviewCount: (count) => set({ reviewCount: count }),
  setAnalysisResults: (results) => set({ analysisResults: results }),
}));
