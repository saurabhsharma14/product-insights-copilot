import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { useWorkflowStore } from '../../store/workflowStore';
import { InsightsDashboard } from './InsightsDashboard';
import { GeneratedOutputs } from './GeneratedOutputs';

import { ApprovalReview } from './ApprovalReview';

export function RunDetails() {
  const { batchId } = useParams<{ batchId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { setAnalysisResults, setBatchId, setReviewCount } = useWorkflowStore();

  useEffect(() => {
    if (!batchId) return;
    
    const fetchRunData = async () => {
      try {
        setLoading(true);
        // We'll set the batch ID in the store so child components can use it
        setBatchId(batchId);
        
        // Fetch the outputs and analysis results
        const response = await apiClient.get(`/analysis/results/${batchId}`);
        setAnalysisResults(response.data);
        
        if (response.data.review_count !== undefined) {
          setReviewCount(response.data.review_count);
        }
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || 'Failed to load run details');
      } finally {
        setLoading(false);
      }
    };

    fetchRunData();
  }, [batchId, setAnalysisResults, setBatchId, setReviewCount]);

  if (loading) {
    return <div className="text-center py-20">Loading analysis data...</div>;
  }

  if (error) {
    return <div className="text-center py-20 text-red-600">{error}</div>;
  }



  return (
    <div className="max-w-6xl mx-auto space-y-12 pb-24 animate-fade-in">
      <button 
        onClick={() => navigate('/')}
        className="text-sm text-gray-500 hover:text-gray-900 mb-4 inline-block"
      >
        &larr; Back to Dashboard
      </button>
      
      <InsightsDashboard />
      <hr className="border-gray-200" />
      <GeneratedOutputs />
      <hr className="border-gray-200" />
      
      {batchId && <ApprovalReview batchId={batchId} />}
    </div>
  );
}
