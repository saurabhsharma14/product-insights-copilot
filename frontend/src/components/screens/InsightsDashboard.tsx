import React from 'react';
import { useWorkflowStore } from '../../store/workflowStore';
import { TrendBadge } from '../common/TrendBadge';
import { MessageSquare, BarChart3, AlertCircle, Quote, Activity } from 'lucide-react';

export const InsightsDashboard: React.FC = () => {
  const { analysisResults, reviewCount } = useWorkflowStore();

  if (!analysisResults) {
    return (
      <div className="bg-white rounded-3xl p-12 text-center border border-gray-100 shadow-sm mt-8">
        <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-xl font-medium text-gray-900 mb-2">No Insights Available</h3>
        <p className="text-gray-500">Run an analysis pipeline to see data-driven findings and themes.</p>
      </div>
    );
  }

  const themes = analysisResults.themes || [];
  const fee_issue = analysisResults.fee_issue;
  const quotes = analysisResults.quotes || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Insights Dashboard</h2>
          <p className="text-sm text-gray-500 mt-1">Data-driven findings from {reviewCount} reviews.</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <MessageSquare size={16} />
            <span className="text-sm font-medium">Reviews Analyzed</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{reviewCount}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <BarChart3 size={16} />
            <span className="text-sm font-medium">Themes Found</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">{themes.length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <AlertCircle size={16} />
            <span className="text-sm font-medium">Top Issue</span>
          </div>
          <p className="text-lg font-bold text-gray-900 truncate" title={themes[0]?.theme_name}>
            {themes[0]?.theme_name || 'N/A'}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center gap-2 text-gray-500 mb-2">
            <AlertCircle size={16} />
            <span className="text-sm font-medium">Fee Confusion</span>
          </div>
          <p className="text-lg font-bold text-gray-900 truncate">
            {fee_issue ? fee_issue.fee_name : 'None Detected'}
          </p>
          {fee_issue && (
            <p className="text-xs text-gray-500 mt-1">Confidence: {fee_issue.confidence}</p>
          )}
        </div>
      </div>

      {/* Top 3 Themes Cards */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3">Top Themes</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {themes.slice(0, 3).map((theme, idx) => (
            <div key={idx} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex flex-col">
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-bold text-gray-900 text-base">{theme.theme_name}</h4>
                <TrendBadge trend={theme.trend} />
              </div>
              <p className="text-sm text-gray-600 mb-4 flex-grow">{theme.description}</p>
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-500 font-medium">{(theme.percentage || 0).toFixed(1)}% of reviews</span>
                <span className="text-gray-500 font-medium">Avg Rating: {(theme.avg_rating || 0).toFixed(1)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Customer Voice section */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Quote size={18} className="text-green-600" />
            Customer Voice
          </h3>
          <div className="space-y-4">
            {quotes.map((quote, idx) => (
              <div key={idx} className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm relative">
                <Quote size={24} className="text-gray-200 absolute top-2 right-2" />
                <p className="text-sm text-gray-800 italic mb-2 relative z-10">"{quote.quote}"</p>
                <div className="flex justify-between items-center text-xs text-gray-500 mt-3 pt-2 border-t border-gray-100">
                  <span>{quote.date ? new Date(quote.date).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' }) + ' IST' : 'N/A'}</span>
                  <span className="bg-gray-100 px-2 py-0.5 rounded">{quote.theme}</span>
                  <span className="text-yellow-500 font-bold">★ {quote.rating}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Fee Issue Detail Card */}
        {fee_issue && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <AlertCircle size={18} className="text-orange-500" />
              Fee Confusion Detail
            </h3>
            <div className="bg-white p-5 rounded-lg border border-orange-200 shadow-sm bg-orange-50/30">
              <h4 className="font-bold text-lg text-gray-900 mb-2">{fee_issue.fee_name}</h4>
              <p className="text-sm text-gray-700 mb-4">
                <strong>Observed Misunderstanding:</strong> {fee_issue.observed_misunderstanding}
              </p>
              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div className="bg-white p-2 rounded border border-gray-100">
                  <span className="block text-gray-500 text-xs">Related Reviews</span>
                  <span className="font-bold text-gray-900">{fee_issue.related_review_count}</span>
                </div>
                <div className="bg-white p-2 rounded border border-gray-100">
                  <span className="block text-gray-500 text-xs">Share of Corpus</span>
                  <span className="font-bold text-gray-900">{((fee_issue.share_of_corpus || 0) * 100).toFixed(1)}%</span>
                </div>
              </div>
              <div>
                <span className="block text-gray-800 text-sm font-semibold mb-2">Representative Complaints:</span>
                <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                  {(fee_issue.representative_complaints || []).map((c: string, i: number) => (
                    <li key={i}>{c}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
