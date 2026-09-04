import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { Card, Badge } from '../common/UI';
import { Activity, MessageSquare, AlertCircle, TrendingUp, Lightbulb, CheckCircle, RefreshCw, AlertTriangle } from 'lucide-react';

interface AnalysisRun {
  batch_id: string;
  status: 'running' | 'pending_approval' | 'completed' | 'failed' | 'approved' | 'rejected';
  review_count: number | null;
  review_period_start: string | null;
  review_period_end: string | null;
  avg_rating: number | null;
  created_at: string;
}

interface AnalysisResults {
  themes: any[];
  fee_issue: any;
  product_pulse: any;
  fee_explainer: any;
  quotes: any[];
}

export function Dashboard() {
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [latestResults, setLatestResults] = useState<AnalysisResults | null>(null);
  const [latestRun, setLatestRun] = useState<AnalysisRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchRunsAndLatest = async () => {
    try {
      const response = await apiClient.get('/analysis/runs');
      const allRuns: AnalysisRun[] = response.data;
      setRuns(allRuns);

      const latestCompleted = allRuns.find((r) => r.status === 'completed');
      if (latestCompleted) {
        setLatestRun(latestCompleted);
        const res = await apiClient.get(`/analysis/results/${latestCompleted.batch_id}`);
        setLatestResults(res.data);
      }
    } catch (err: any) {
      console.error('Failed to fetch dashboard data', err);
      setError(err?.response?.data?.detail || err.message || 'Failed to fetch dashboard data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRunsAndLatest();
    const interval = setInterval(fetchRunsAndLatest, 10000);
    return () => clearInterval(interval);
  }, []);



  const getTrendColor = (trend: string) => {
    if (!trend) return 'text-gray-500 bg-gray-500/10 border-gray-500/20';
    if (trend.toLowerCase().includes('spiking')) return 'text-rose-500 bg-rose-500/10 border-rose-500/20';
    if (trend.toLowerCase().includes('decreasing')) return 'text-green-500 bg-green-500/10 border-green-500/20';
    return 'text-amber-500 bg-amber-500/10 border-amber-500/20';
  };

  return (
    <div className="max-w-7xl mx-auto space-y-10 animate-fade-in pb-16">
      
      {/* Header Section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-white/40 backdrop-blur-xl border border-white/60 p-6 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.04)]">
        <div>
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-blue-700 to-indigo-700 bg-clip-text text-transparent tracking-tight">Intelligence Dashboard</h1>
          <p className="mt-2 text-gray-500 font-medium">Autonomous Daily Product Pulse & Review Analysis (Runs at 11:00 AM IST)</p>
        </div>
        <div className="mt-4 md:mt-0 text-right">
          {latestRun?.review_period_start && latestRun?.review_period_end && (
            <div className="inline-block px-4 py-2 bg-indigo-50 border border-indigo-100 rounded-2xl text-left">
              <p className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-0.5">Analysis Date Range</p>
              <p className="text-indigo-900 font-medium text-sm">
                {new Date(latestRun.review_period_start).toLocaleDateString()} — {new Date(latestRun.review_period_end).toLocaleDateString()}
              </p>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-xl shadow-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-red-800">Error Loading Data</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {latestRun && latestRun.status === 'completed' && latestRun.review_count !== null && latestRun.review_count < 10 && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-xl shadow-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-amber-800">Low Review Volume</h3>
            <p className="text-sm text-amber-700 mt-1">
              Only {latestRun.review_count} reviews were analyzed in the selected period. Analysis and trends may lack statistical significance.
            </p>
          </div>
        </div>
      )}

      {loading && !latestResults ? (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : latestResults ? (
        <div className="space-y-8">
          
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white/60 backdrop-blur-lg border border-white/60 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <Activity className="w-16 h-16" />
              </div>
              <p className="text-sm font-medium text-gray-500 mb-1">Total Reviews</p>
              <h3 className="text-4xl font-bold text-gray-900">{latestRun?.review_count || 0}</h3>
              <p className="text-xs font-semibold text-green-600 mt-2 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> Processed
              </p>
            </div>
            
            <div className="bg-white/60 backdrop-blur-lg border border-white/60 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-10">
                <MessageSquare className="w-16 h-16" />
              </div>
              <p className="text-sm font-medium text-gray-500 mb-1">Avg Rating</p>
              <h3 className="text-4xl font-bold text-gray-900">{latestRun?.avg_rating?.toFixed(1) || '0.0'}</h3>
              <p className="text-xs font-medium text-gray-500 mt-2">from 5.0 scale</p>
            </div>

            {latestResults.fee_issue && (
              <div className="md:col-span-2 bg-gradient-to-br from-rose-50 to-red-50/20 border border-rose-100 p-6 rounded-3xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-rose-100 text-rose-600 rounded-2xl">
                    <AlertCircle className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                      Top Friction: {latestResults.fee_issue.fee_name}
                      <span className="px-2 py-0.5 text-xs font-bold bg-rose-600 text-white rounded-full">Confidence: {latestResults.fee_issue.confidence}</span>
                    </h3>
                    <p className="text-gray-700 mt-2 leading-relaxed">{latestResults.fee_issue.observed_misunderstanding}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Product Pulse */}
            {latestResults.product_pulse && (
              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-600 to-blue-800 px-6 py-5">
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Activity className="w-5 h-5" /> Product Pulse
                  </h2>
                  <p className="text-blue-100 text-sm mt-1">Weekly Product Pulse</p>
                </div>
                <div className="p-6">
                  <p className="text-gray-700 text-lg mb-6 leading-relaxed">{latestResults.product_pulse.top_themes_summary}</p>
                  <h4 className="font-semibold text-gray-900 mb-4 uppercase tracking-wider text-sm">Key Actions</h4>
                  <ul className="space-y-3">
                    {latestResults.product_pulse.product_actions?.map((finding: string, i: number) => (
                      <li key={i} className="flex gap-3 text-gray-700 items-start">
                        <CheckCircle className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
                        <span className="leading-relaxed">{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Fee Explainer */}
            {latestResults.fee_explainer && (
              <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
                <div className="bg-gradient-to-r from-indigo-600 to-purple-800 px-6 py-5">
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <Lightbulb className="w-5 h-5" /> Recommended Solution
                  </h2>
                  <p className="text-indigo-100 text-sm mt-1">Resolution for Fee Confusion</p>
                </div>
                <div className="p-6 flex-1">
                  <div className="bg-indigo-50/50 rounded-2xl p-5 border border-indigo-100/50 mb-6">
                    <h4 className="font-semibold text-indigo-900 mb-2">Customer Communication</h4>
                    <p className="text-gray-700 italic leading-relaxed">"{latestResults.fee_explainer.customer_confusion_summary}"</p>
                  </div>
                  
                  <h4 className="font-semibold text-gray-900 mb-4 uppercase tracking-wider text-sm">Suggested Explainer Bullets</h4>
                  <ul className="space-y-3">
                    {latestResults.fee_explainer.bullets?.map((change: string, i: number) => (
                      <li key={i} className="flex gap-3 text-gray-700 items-start">
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-2.5 shrink-0" />
                        <span className="leading-relaxed">{change}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Top Themes */}
          {latestResults.themes && latestResults.themes.length > 0 && (
            <div className="bg-white rounded-3xl shadow-sm border border-gray-100 p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                Top Identified Themes
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {latestResults.themes.map((theme: any, i: number) => (
                  <div key={i} className="group p-5 rounded-2xl border border-gray-100 bg-gray-50/30 hover:bg-white hover:shadow-xl hover:shadow-gray-200/50 transition-all cursor-default">
                    <div className="flex justify-between items-start mb-3">
                      <h4 className="font-bold text-gray-900">{theme.theme_name}</h4>
                      <span className={`px-2.5 py-1 text-xs font-semibold rounded-lg border ${getTrendColor(theme.trend)}`}>
                        {theme.trend?.toUpperCase() || 'N/A'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed mb-4">{theme.description}</p>
                    <div className="flex items-center justify-between mt-auto">
                      <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Mentions</span>
                      <span className="px-3 py-1 bg-gray-200/50 text-gray-700 text-sm font-bold rounded-lg">{theme.review_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      ) : (
        <div className="bg-white rounded-3xl p-12 text-center border border-gray-100 shadow-sm">
          <Activity className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">No Analysis Results Found</h3>
          <p className="text-gray-500">Run an analysis to see insights, themes, and product pulse metrics.</p>
        </div>
      )}

      {/* Historical Runs Table */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 px-2">Historical Pipeline Runs</h2>
        <Card className="overflow-hidden p-0 border border-gray-100 shadow-sm rounded-3xl">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-100">
              <thead className="bg-gray-50/80">
                <tr>
                  <th className="px-6 py-5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Run Date</th>
                  <th className="px-6 py-5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Reviews</th>
                  <th className="px-6 py-5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Avg Rating</th>
                  <th className="px-6 py-5 text-right text-xs font-bold text-gray-500 uppercase tracking-wider">Action</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-50">
                {loading && runs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-400">Loading analysis runs...</td>
                  </tr>
                ) : runs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center text-gray-500">No autonomous runs have been executed yet.</td>
                  </tr>
                ) : (
                  runs.map((run) => (
                    <tr 
                      key={run.batch_id} 
                      className="hover:bg-blue-50/30 transition-colors cursor-pointer group"
                      onClick={() => navigate(`/run/${run.batch_id}`)}
                    >
                      <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-900 font-medium">
                        {new Date(run.created_at.endsWith('Z') ? run.created_at : run.created_at + 'Z').toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })} IST
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap">
                        <Badge variant={
                          run.status === 'completed' ? 'success' :
                          run.status === 'failed' ? 'error' :
                          run.status === 'running' ? 'warning' : 'neutral'
                        }>
                          {run.status.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-600 font-medium">
                        {run.review_count !== null ? run.review_count.toLocaleString() : '-'}
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap text-sm text-gray-600 font-medium">
                        {run.avg_rating !== null ? run.avg_rating.toFixed(2) : '-'}
                      </td>
                      <td className="px-6 py-5 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-blue-600 font-semibold hover:text-blue-800 transition-colors flex items-center justify-end gap-1 w-full">
                          View Analysis <TrendingUp className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}
