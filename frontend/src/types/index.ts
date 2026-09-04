export interface ReviewRecord {
  review_id: string;
  review_text: string;
  rating: number;
  review_date: string;
  app_version: string;
  developer_reply: string;
  source: string;
  source_url: string;
  primary_theme?: string;
  secondary_theme?: string;
  sentiment?: string;
  severity?: string;
  issue_type?: string;
}

export interface FetchStats {
  total_initial: number;
  removed_empty: number;
  removed_duplicates: number;
  total_valid: number;
}

export interface FetchResponse {
  batch_id: string;
  stats: FetchStats;
  review_count: number;
  review_period_start: string;
  review_period_end: string;
  avg_rating: number;
}

export interface Theme {
  theme_name: string;
  description: string;
  review_count: number;
  percentage: number;
  negative_count: number;
  avg_rating: number;
  representative_review_ids: string[];
  trend: string;
  rank_score: number;
}

export interface OfficialSource {
  url: string;
  title: string;
  domain: string;
  extracted_info: string;
  date_checked: string;
}

export interface FeeIssue {
  fee_name: string;
  related_review_count: number;
  share_of_corpus: number;
  representative_complaints: string[];
  observed_misunderstanding: string;
  confidence: string;
  selection_reason: string;
}

export interface CustomerQuote {
  review_id: string;
  quote: string;
  date: string;
  rating: number;
  theme: string;
  source: string;
}

export interface ProductPulse {
  content: string;
  word_count: number;
  top_themes_summary: string;
  user_voice_quotes: CustomerQuote[];
  key_observation: string;
  product_actions: string[];
}

export interface FeeExplainer {
  fee_name: string;
  customer_confusion_summary: string;
  bullets: string[];
  sources: OfficialSource[];
  last_checked: string;
}

export interface AnalysisResults {
  themes: Theme[];
  fee_issue?: FeeIssue;
  quotes: CustomerQuote[];
  product_pulse?: ProductPulse;
  fee_explainer?: FeeExplainer;
}
