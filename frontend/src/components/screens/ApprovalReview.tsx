import { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { Card, Badge } from '../common/UI';
import { Loader2, AlertTriangle, CheckCircle, FileText, Mail, ShieldAlert } from 'lucide-react';

interface ApprovalPreview {
  batch_id: string;
  approval_status: string;
  review_count: number;
  review_period: string;
  top_themes: string[];
  fee_issue: string | null;
  document_entry_preview: any;
  email_subject: string;
  email_body: string;
  gmail_authenticated: boolean;
  google_doc_configured: boolean;
}

interface ApprovalResult {
  batch_id: string;
  approval_status: string;
  approved_at: string | null;
  document_action: {
    action_name: string;
    status: string;
    message: string;
    timestamp: string;
  } | null;
  gmail_action: {
    action_name: string;
    status: string;
    message: string;
    timestamp: string;
  } | null;
}

export function ApprovalReview({ batchId }: { batchId: string }) {
  const [preview, setPreview] = useState<ApprovalPreview | null>(null);
  const [result, setResult] = useState<ApprovalResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isApproving, setIsApproving] = useState(false);

  useEffect(() => {
    const fetchPreview = async () => {
      try {
        setLoading(true);
        const [previewRes, statusRes] = await Promise.all([
          apiClient.get(`/approval/${batchId}/preview`),
          apiClient.get(`/approval/${batchId}/status`)
        ]);
        setPreview(previewRes.data);
        if (statusRes.data.approval_status === 'approved') {
          setResult(statusRes.data);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load approval preview');
      } finally {
        setLoading(false);
      }
    };
    if (batchId) {
      fetchPreview();
    }
  }, [batchId]);

  const handleApprove = async () => {
    try {
      setIsApproving(true);
      const res = await apiClient.post(`/approval/${batchId}/approve`);
      setResult(res.data);
      if (preview) {
        setPreview({ ...preview, approval_status: 'approved' });
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve');
    } finally {
      setIsApproving(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>;
  if (error) return <div className="p-6 bg-red-50 text-red-700 rounded-lg">{error}</div>;
  if (!preview) return null;

  const isApproved = preview.approval_status === 'approved';

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-3xl p-8 text-white shadow-lg">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-3">
          <ShieldAlert className="w-7 h-7 text-yellow-400" />
          Approval Gate
        </h2>
        <p className="text-slate-300">
          Review the generated outputs below. Explicit approval is required before the system executes any internal write actions.
        </p>
      </div>

      {!isApproved && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-start gap-3 shadow-sm">
          <AlertTriangle className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-amber-900">Action Required</h4>
            <p className="text-amber-800 text-sm mt-1">⚠️ No write action will occur until you approve. Please review the document entry and email draft previews.</p>
          </div>
        </div>
      )}

      {isApproved && result && (
        <div className="bg-green-50 border border-green-200 p-6 rounded-xl space-y-4 shadow-sm">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-8 h-8 text-green-500 shrink-0" />
            <div>
              <h4 className="text-lg font-bold text-green-900">Approved & Executed</h4>
              <p className="text-green-800 text-sm">The internal updates have been processed.</p>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div className={`p-4 rounded-lg border shadow-sm ${result.document_action?.status === 'success' ? 'bg-white border-green-200' : 'bg-red-50 border-red-200'}`}>
              <h5 className="font-semibold flex items-center gap-2 mb-1">
                <FileText className="w-4 h-4" /> Document Append
              </h5>
              <Badge variant={result.document_action?.status === 'success' ? 'success' : 'error'}>
                {result.document_action?.status.toUpperCase()}
              </Badge>
              <p className="text-xs text-gray-500 mt-2">{result.document_action?.message}</p>
            </div>
            
            <div className={`p-4 rounded-lg border shadow-sm ${result.gmail_action?.status === 'success' ? 'bg-white border-green-200' : 'bg-red-50 border-red-200'}`}>
              <h5 className="font-semibold flex items-center gap-2 mb-1">
                <Mail className="w-4 h-4" /> Gmail Draft Creation
              </h5>
              <Badge variant={result.gmail_action?.status === 'success' ? 'success' : 'error'}>
                {result.gmail_action?.status.toUpperCase()}
              </Badge>
              <p className="text-xs text-gray-500 mt-2">{result.gmail_action?.message}</p>
              {result.gmail_action?.status === 'success' && (
                <p className="text-xs font-semibold text-green-600 mt-2">Gmail draft created. No email has been sent.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Review Summary Card */}
      <Card className="border-gray-200 shadow-sm p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4 border-b pb-3">Review Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500 font-medium">Reviews Analyzed</p>
            <p className="text-xl font-bold text-gray-800">{preview.review_count}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Review Period</p>
            <p className="text-sm font-semibold text-gray-800 mt-1">{preview.review_period}</p>
          </div>
          <div className="col-span-2">
            <p className="text-sm text-gray-500 font-medium">Detected Friction</p>
            <p className="text-sm font-semibold text-gray-800 mt-1">{preview.fee_issue || 'None detected'}</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Document Preview */}
        <Card className="flex flex-col h-full border-gray-200 shadow-sm overflow-hidden p-0">
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center gap-2">
            <FileText className="w-5 h-5 text-gray-500" />
            <h3 className="font-bold text-gray-800">Document Update Preview</h3>
          </div>
          <div className="p-6 flex-1 bg-slate-900 text-green-400 font-mono text-sm overflow-x-auto">
            <pre>{JSON.stringify(preview.document_entry_preview, null, 2)}</pre>
          </div>
        </Card>

        {/* Gmail Draft Preview */}
        <Card className="flex flex-col h-full border-gray-200 shadow-sm overflow-hidden p-0">
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200 flex items-center gap-2">
            <Mail className="w-5 h-5 text-gray-500" />
            <h3 className="font-bold text-gray-800">Gmail Draft Preview</h3>
          </div>
          <div className="p-6 flex-1 bg-white">
            {!preview.gmail_authenticated && (
              <div className="bg-red-50 border border-red-200 p-4 rounded-xl mb-6 shadow-sm">
                <h4 className="text-red-900 font-semibold mb-1 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" /> Gmail Authentication Required
                </h4>
                <p className="text-sm text-red-800 mb-3">You must authenticate with Google to enable Gmail draft creation.</p>
                <a href={`${import.meta.env.VITE_API_URL || '/api'}/auth/google/login`} className="inline-block px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-bold hover:bg-red-700 transition-colors">
                  Connect Google Account
                </a>
              </div>
            )}
            <div className={`mb-4 pb-4 border-b border-gray-100 ${!preview.gmail_authenticated ? 'opacity-50' : ''}`}>
              <p className="text-sm text-gray-500 mb-1">Subject</p>
              <p className="font-semibold text-gray-900">{preview.email_subject}</p>
            </div>
            <div className={!preview.gmail_authenticated ? 'opacity-50' : ''}>
              <p className="text-sm text-gray-500 mb-2">Body</p>
              <div className="whitespace-pre-wrap text-sm text-gray-700 font-sans leading-relaxed p-4 bg-gray-50 rounded-lg border border-gray-100 h-64 overflow-y-auto">
                {preview.email_body}
              </div>
            </div>
          </div>
        </Card>
      </div>

      {!isApproved && (
        <div className="flex justify-end pt-4 pb-12">
          <button
            onClick={handleApprove}
            disabled={isApproving || !preview.gmail_authenticated}
            className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-3"
          >
            {isApproving ? <Loader2 className="w-6 h-6 animate-spin" /> : <CheckCircle className="w-6 h-6" />}
            {isApproving ? 'Approving & Executing...' : 'Approve & Create Internal Updates'}
          </button>
        </div>
      )}
    </div>
  );
}
