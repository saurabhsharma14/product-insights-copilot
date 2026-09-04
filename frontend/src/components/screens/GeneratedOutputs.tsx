import React from 'react';
import { useWorkflowStore } from '../../store/workflowStore';
import { EditableTextArea } from '../common/EditableTextArea';
import { FileText, CheckCircle } from 'lucide-react';
import axios from 'axios';

export const GeneratedOutputs: React.FC = () => {
  const { analysisResults, batchId, setAnalysisResults } = useWorkflowStore();

  if (!analysisResults || !analysisResults.product_pulse) {
    return (
      <div className="flex justify-center items-center h-64 text-gray-500">
        Outputs not generated yet.
      </div>
    );
  }

  const { product_pulse, fee_explainer } = analysisResults;

  const handlePulseSave = async (newContent: string) => {
    try {
      await axios.put(`${import.meta.env.VITE_API_URL || '/api'}/outputs/${batchId}/pulse`, {
        content: newContent
      });
      // Update local state
      const updatedResults = { ...analysisResults };
      if (updatedResults.product_pulse) {
        updatedResults.product_pulse.content = newContent;
        updatedResults.product_pulse.word_count = newContent.trim().split(/\\s+/).length;
        setAnalysisResults(updatedResults);
      }
    } catch (error) {
      console.error('Failed to save pulse:', error);
      alert('Failed to save changes to Product Pulse.');
    }
  };

  const handleExplainerSave = async (newContent: string) => {
    if (!fee_explainer) return;
    
    // Simplistic parsing of bullets for this example
    const lines = newContent.split('\\n').filter(l => l.trim().length > 0);
    const customer_confusion_summary = lines[0] || fee_explainer.customer_confusion_summary;
    const bullets = lines.slice(1).map(l => l.replace(/^[-*•\\d.]\\s*/, ''));

    try {
      await axios.put(`${import.meta.env.VITE_API_URL || '/api'}/outputs/${batchId}/explainer`, {
        customer_confusion_summary,
        bullets
      });
      // Update local state
      const updatedResults = { ...analysisResults };
      if (updatedResults.fee_explainer) {
        updatedResults.fee_explainer.customer_confusion_summary = customer_confusion_summary;
        updatedResults.fee_explainer.bullets = bullets;
        setAnalysisResults(updatedResults);
      }
    } catch (error) {
      console.error('Failed to save explainer:', error);
      alert('Failed to save changes to Fee Explainer.');
    }
  };

  // Format initial explainer content for editing
  const explainerInitialContent = fee_explainer ? 
    `${fee_explainer.customer_confusion_summary}\n\n${(fee_explainer.bullets || []).map((b: string) => '• ' + b).join('\n')}` : '';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Generated Outputs</h2>
          <p className="text-sm text-gray-500 mt-1">Review and edit the AI-generated communications.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[600px]">
        {/* Product Pulse */}
        <div className="h-full">
          <EditableTextArea
            title="Weekly Product Pulse"
            initialValue={product_pulse.content || (product_pulse as any).summary || ''}
            onSave={handlePulseSave}
            maxWords={250}
          />
        </div>

        {/* Fee Explainer */}
        <div className="h-full flex flex-col gap-4">
          {fee_explainer ? (
            <>
              <div className="flex-grow">
                <EditableTextArea
                  title={`Fee Explainer: ${fee_explainer.fee_name}`}
                  initialValue={explainerInitialContent}
                  onSave={handleExplainerSave}
                  maxWords={undefined} // Not strictly max words, max 6 bullets
                />
              </div>
              
              {/* Official Sources Panel */}
              <div className="bg-blue-50/50 rounded-lg border border-blue-100 p-4">
                <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center gap-2">
                  <CheckCircle size={16} />
                  Verified Official Sources
                </h4>
                <ul className="space-y-2 text-sm">
                  {(fee_explainer.sources || []).map((source: any, idx: number) => (
                    <li key={idx} className="flex flex-col">
                      <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">
                        {source.title}
                      </a>
                      <span className="text-xs text-gray-500">Domain: {source.domain} • Last checked: {new Date(source.date_checked).toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : (
            <div className="flex-grow bg-gray-50 rounded-lg border border-gray-200 flex flex-col justify-center items-center text-gray-500 p-6 text-center">
              <FileText size={48} className="text-gray-300 mb-4" />
              <p className="font-medium text-gray-700 mb-1">No Fee Explainer Generated</p>
              <p className="text-sm">No significant fee confusion was detected in this review batch.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
