import { Platform } from 'react-native';
/**
 * API configuration for Smart Criminal Judgment Analysis System.
 * Point to your backend (e.g. FastAPI) when running locally or in production.
 */

const getApiBase = (): string => {
  // Force localhost for all platforms to avoid connection issues
  return 'http://127.0.0.1:8000';
};

export const API_BASE = getApiBase();
export const API_TRANSCRIBE = API_BASE + '/transcribe';
export const API_EXTRACT = API_BASE + '/extract';
export const API_ANALYZE = API_BASE + '/api/v1/analyze';
export const API_ARGUMENTS = API_BASE + '/api/v1/arguments';
export const API_HEALTH = API_BASE + '/health';
export const API_COMP4_CHAT = API_BASE + '/comp4/chat';
export const API_HISTORY_SAVE = API_BASE + '/api/v1/history/save';
export const API_HISTORY_LIST = API_BASE + '/api/v1/history/list';
export const API_HISTORY_FETCH = (id: string) => API_BASE + `/api/v1/history/${id}`;

// ── Component 3: Appeal Outcome Prediction ─────────────────────────────
export const API_APPEAL_PREDICT = API_BASE + '/api/v1/appeal/predict';
export const API_APPEAL_PREDICT_DETAILED = API_BASE + '/api/v1/appeal/predict/detailed';
export const API_APPEAL_LEARN_ANALYZE = API_BASE + '/api/v1/appeal/learn/analyze';
export const API_APPEAL_FIND_SIMILAR = API_BASE + '/api/v1/appeal/find/similar';
export const API_APPEAL_ANALYZE_BATCH = API_BASE + '/api/v1/appeal/analyze/batch';
export const API_APPEAL_MODEL_INFO = API_BASE + '/api/v1/appeal/model/info';
export const API_APPEAL_HEALTH = API_BASE + '/api/v1/appeal/health';
export const API_APPEAL_FAIRNESS_REPORT = API_BASE + '/api/v1/appeal/dashboard/fairness-report';


// ── Component-scoped history endpoints ───────────────────────────────
export const API_HIST_C1_SAVE = API_BASE + '/api/v1/history/comp1/save';
export const API_HIST_C1_LIST = API_BASE + '/api/v1/history/comp1/list';
export const API_HIST_C1_FETCH = (id: string) => API_BASE + `/api/v1/history/comp1/${id}`;

export const API_HIST_C2_SAVE = API_BASE + '/api/v1/history/comp2/save';
export const API_HIST_C2_LIST = API_BASE + '/api/v1/history/comp2/list';
export const API_HIST_C2_FETCH = (id: string) => API_BASE + `/api/v1/history/comp2/${id}`;

export interface HistorySummary {
  case_id: string;
  case_name: string;
  timestamp: string;
  subject: string;
  accused: string;
}

export interface HistoryRecord {
  case_id: string;
  case_name: string;
  component1_data: any;
  component2_data: any;
  metadata: {
    accused?: string;
    subject?: string;
    file_hash?: string;
  };
}

export async function saveToHistory(record: HistoryRecord): Promise<{ status: string, case_id: string }> {
  try {
    const res = await fetch(API_HISTORY_SAVE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
    });
    return res.json();
  } catch (err) {
    console.error('Save to history failed:', err);
    return { status: 'error', case_id: '' };
  }
}

export async function fetchHistoryList(): Promise<HistorySummary[]> {
  try {
    const res = await fetch(API_HISTORY_LIST);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('Fetch history list failed:', err);
    return [];
  }
}

export async function fetchHistoryDetail(caseId: string): Promise<any> {
  try {
    const res = await fetch(API_HISTORY_FETCH(caseId));
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error('Fetch history detail failed:', err);
    return null;
  }
}

// ── Component 1 history ──────────────────────────────────────────────

export interface Comp1HistoryRecord {
  case_id: string;
  case_name: string;
  payload: any; // Full analyzed_case + data + input_metadata
  subject?: string;
  accused?: string;
}

export async function saveComp1History(record: Comp1HistoryRecord): Promise<void> {
  try {
    await fetch(API_HIST_C1_SAVE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
    });
  } catch (err) {
    console.error('saveComp1History failed:', err);
  }
}

export async function fetchComp1List(): Promise<HistorySummary[]> {
  try {
    const res = await fetch(API_HIST_C1_LIST);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('fetchComp1List failed:', err);
    return [];
  }
}

export async function fetchComp1Detail(caseId: string): Promise<any> {
  try {
    const res = await fetch(API_HIST_C1_FETCH(caseId));
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error('fetchComp1Detail failed:', err);
    return null;
  }
}

// ── Component 2 history ──────────────────────────────────────────────

export interface Comp2HistoryRecord {
  case_id: string;
  case_name: string;
  payload: any; // Full arguments_report
  subject?: string;
  accused?: string;
}

export async function saveComp2History(record: Comp2HistoryRecord): Promise<void> {
  try {
    await fetch(API_HIST_C2_SAVE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
    });
  } catch (err) {
    console.error('saveComp2History failed:', err);
  }
}

export async function fetchComp2List(): Promise<HistorySummary[]> {
  try {
    const res = await fetch(API_HIST_C2_LIST);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('fetchComp2List failed:', err);
    return [];
  }
}

export async function fetchComp2Detail(caseId: string): Promise<any> {
  try {
    const res = await fetch(API_HIST_C2_FETCH(caseId));
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error('fetchComp2Detail failed:', err);
    return null;
  }
}

// ── Component 3: Appeal Outcome Prediction ─────────────────────────────

export interface AppealPredictionRequest {
  case_description: string;
  offence_type?: string;
  hc_sentence?: string;
  appeal_duration?: number;
}

export interface DetailedPredictionRequest {
  case_description: string;
  user_type?: 'general' | 'lawyer' | 'student';
  analysis_level?: 'basic' | 'standard' | 'detailed';
  include_precedents?: boolean;
  language?: 'en' | 'si' | 'ta';
}

export interface LearningRequest {
  case_description: string;
  learning_mode?: 'guided' | 'independent' | 'assessment';
  difficulty_level?: 'beginner' | 'intermediate' | 'advanced';
  include_feedback?: boolean;
}

export interface PredictionProbabilities {
  Appeal_Allowed: number;
  Appeal_Dismissed: number;
  Partly_Allowed: number;
}

export interface DetectedFeatures {
  grounds: string[];
  evidence: string[];
  offence: string[];
  other: string[];
}

export interface DetailedPredictionResponse {
  // Basic prediction
  prediction: string;
  confidence: number;
  probabilities: PredictionProbabilities;
  detected_features: DetectedFeatures;  // Add this missing field
  confidence_band?: string;
  manual_review_required?: boolean;
  reliability_note?: string;
  abstained?: boolean;
  review_priority?: string;
  top_outcomes?: Array<{ rank: number; outcome: string; probability: number }>;
  reason_trace?: string[];
  shap_summary?: Record<string, unknown>;
  confidence_interval?: {
    method?: string;
    lower_pct?: number | null;
    upper_pct?: number | null;
    half_width_pct?: number;
    top_two_margin?: number;
    qualitative_width?: string;
    summary_line?: string;
  };
  precedent_trend?: {
    direction?: string;
    summary?: string;
    precedents_considered?: number;
    year_span?: number[];
    by_year?: Array<{
      year: number;
      n: number;
      appeal_allowed_pct: number;
      appeal_dismissed_pct: number;
      partly_allowed_pct: number;
    }>;
  };
  governance_note?: string;
  context_analysis?: Record<string, unknown>;
  grounds_analysis?: Record<string, unknown>;
  evidence_analysis?: Record<string, unknown>;

  // Enhanced analysis
  legal_reasoning: string;
  key_factors: Array<{
    factor_name: string;
    importance: number;
    explanation: string;
    supporting_evidence: string[];
  }>;
  risk_assessment: string;
  strategy_recommendations: Array<{
    recommendation: string;
    priority: string;
    rationale: string;
    expected_impact: string;
  }>;

  // Similar cases
  similar_cases: Array<{
    case_id: string;
    similarity_score: number;
    case_summary: string;
    outcome: string;
    key_legal_points: string[];
    citation?: string;
    year?: number;
  }>;

  // Educational content
  legal_concepts: string[];
  methodology_explanation: string;

  // Metadata
  processing_time: number;
  model_version: string;
  feature_importance: Record<string, number>;
  analysis_timestamp: string;
}

export interface EducationalResponse {
  explanation_level: string;
  legal_concepts: string[];
  methodology_explanation: string;
  quiz_questions: string[];
  further_reading: string[];
  case_study: Record<string, any>;
  learning_objectives: string[];
  concept_mastery: Record<string, number>;
  next_topics: string[];
}

export interface SimilarCase {
  case_id: string;
  similarity: number;
  outcome: string;
  conviction_status: string;
  facts: string;
  offence: string;
  high_court: string;
  grounds: string;
}

export interface ModelMetadata {
  accuracy: number;
  model_name: string;
  training_date: string;
  training_samples: number;
  num_features: number;
}

export interface AppealPredictionResponse {
  status: string;
  prediction: string;
  confidence: number;
  probabilities: PredictionProbabilities;
  detected_features: DetectedFeatures;
  similar_cases: SimilarCase[];
  metadata: ModelMetadata;
  timestamp: string;
  governance_note?: string;
  confidence_interval?: DetailedPredictionResponse['confidence_interval'];
  precedent_trend?: DetailedPredictionResponse['precedent_trend'];
}

export interface Comp3HistoryRecord {
  case_id: string;
  case_name: string;
  payload: AppealPredictionResponse | DetailedPredictionResponse;
  user_type?: 'general' | 'lawyer' | 'student';
  analysis_level?: 'basic' | 'standard' | 'detailed';
  timestamp: string;
}

export interface Comp3HistoryMetadata {
  subject?: string;
  accused?: string;
}


// ── Component 3 API Functions ─────────────────────────────────────

export async function predictAppealOutcome(request: AppealPredictionRequest): Promise<AppealPredictionResponse | null> {
  try {
    const res = await fetch(API_APPEAL_PREDICT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      console.error('predictAppealOutcome failed:', res.status, res.statusText);
      return null;
    }

    return await res.json();
  } catch (err) {
    console.error('predictAppealOutcome failed:', err);
    return null;
  }
}

export async function predictAppealOutcomeDetailed(request: DetailedPredictionRequest): Promise<DetailedPredictionResponse | null> {
  try {
    const res = await fetch(API_APPEAL_PREDICT_DETAILED, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      console.error('predictAppealOutcomeDetailed failed:', res.status, res.statusText);
      return null;
    }

    return await res.json();
  } catch (err) {
    console.error('predictAppealOutcomeDetailed failed:', err);
    return null;
  }
}

export interface Comp3DashboardAnalytics {
  filters: {
    years: number[];
    offences: string[];
    courts: string[];
    regions: string[];
  };
  applied_filters: {
    year?: number | null;
    offence?: string | null;
    high_court?: string | null;
    region?: string | null;
  };
  kpis: {
    total_cases: number;
    allowed_rate: number;
    dismissed_rate: number;
    partly_rate: number;
  };
  outcome_distribution: Array<{ outcome: string; count: number }>;
  yearly_trend: Array<{ year: number; total: number; allowed: number; partly: number; dismissed: number }>;
  offence_distribution: Array<{ offence: string; total: number; allowed: number; partly: number; dismissed: number }>;
  court_distribution: Array<{ court: string; total: number; allowed: number; partly: number; dismissed: number }>;
  region_distribution: Array<{ region: string; total: number; allowed: number; partly: number; dismissed: number }>;
  appeal_type_distribution?: Array<{
    appeal_type: string;
    total: number;
    allowed: number;
    partly: number;
    dismissed: number;
  }>;
  table_rows: Array<{
    case_id: string;
    year?: number;
    offence: string;
    offence_raw?: string | null;
    court: string;
    court_raw?: string | null;
    region?: string;
    outcome: string;
    summary: string;
    summary_detail?: string;
    judgment_file_summary?: string;
    judgment_file_summary_detail?: string;
    appeal_analysis_summary?: string;
    appeal_analysis_summary_detail?: string;
  }>;
}

export async function getComp3DashboardAnalytics(params?: {
  year?: number;
  offence?: string;
  high_court?: string;
  region?: string;
}): Promise<Comp3DashboardAnalytics | null> {
  try {
    const qs = new URLSearchParams();
    if (params?.year != null) qs.set('year', String(params.year));
    if (params?.offence) qs.set('offence', params.offence);
    if (params?.high_court) qs.set('high_court', params.high_court);
    if (params?.region) qs.set('region', params.region);

    const url = `${API_APPEAL_PREDICT_DETAILED.replace('/predict/detailed', '/dashboard/analytics')}${qs.toString() ? `?${qs.toString()}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) {
      console.error('getComp3DashboardAnalytics failed:', res.status, res.statusText);
      return null;
    }
    const payload = await res.json();
    return payload?.analytics ?? null;
  } catch (err) {
    console.error('getComp3DashboardAnalytics failed:', err);
    return null;
  }
}

export interface Comp3FairnessReportPayload {
  generated_at?: string;
  dataset_rows?: number;
  min_slice_n?: number;
  overall?: Record<string, number | string>;
  by_offence?: Array<{
    slice_value: string;
    n: number;
    appeal_allowed_pct: number;
    partly_allowed_pct: number;
    appeal_dismissed_pct: number;
    low_sample: boolean;
  }>;
  by_court?: Array<{
    slice_value: string;
    n: number;
    appeal_allowed_pct: number;
    partly_allowed_pct: number;
    appeal_dismissed_pct: number;
    low_sample: boolean;
  }>;
  by_year?: Array<{
    year: number;
    n: number;
    appeal_allowed_pct: number;
    partly_allowed_pct: number;
    appeal_dismissed_pct: number;
    low_sample: boolean;
  }>;
  notes?: string[];
  error?: string;
}

export async function getComp3FairnessReport(minSliceN?: number): Promise<Comp3FairnessReportPayload | null> {
  try {
    const qs = new URLSearchParams();
    if (minSliceN != null) qs.set('min_slice_n', String(minSliceN));
    const url = `${API_APPEAL_FAIRNESS_REPORT}${qs.toString() ? `?${qs.toString()}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) {
      console.error('getComp3FairnessReport failed:', res.status, res.statusText);
      return null;
    }
    const payload = await res.json();
    return payload?.report ?? null;
  } catch (err) {
    console.error('getComp3FairnessReport failed:', err);
    return null;
  }
}

export async function analyzeCaseForLearning(request: LearningRequest): Promise<EducationalResponse | null> {
  try {
    const res = await fetch(API_APPEAL_LEARN_ANALYZE, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      console.error('analyzeCaseForLearning failed:', res.status, res.statusText);
      return null;
    }

    return await res.json();
  } catch (err) {
    console.error('analyzeCaseForLearning failed:', err);
    return null;
  }
}

export async function findSimilarCases(request: { case_description: string; max_results?: number; similarity_threshold?: number }): Promise<any> {
  try {
    const res = await fetch(API_APPEAL_FIND_SIMILAR, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      console.error('findSimilarCases failed:', res.status, res.statusText);
      return null;
    }

    return await res.json();
  } catch (err) {
    console.error('findSimilarCases failed:', err);
    return null;
  }
}

export async function getAppealModelInfo(): Promise<any> {
  try {
    const res = await fetch(API_APPEAL_MODEL_INFO);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error('getAppealModelInfo failed:', err);
    return null;
  }
}

export async function saveComp3History(record: Comp3HistoryRecord): Promise<void> {
  try {
    await fetch(API_BASE + '/api/v1/history/comp3/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record),
    });
  } catch (err) {
    console.error('saveComp3History failed:', err);
  }
}

export async function fetchComp3List(): Promise<HistorySummary[]> {
  try {
    const res = await fetch(API_BASE + '/api/v1/history/comp3/list');
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('fetchComp3List failed:', err);
    return [];
  }
}

export async function fetchComp3Detail(caseId: string): Promise<any> {
  try {
    const res = await fetch(API_BASE + `/api/v1/history/comp3/${caseId}`);
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error('fetchComp3Detail failed:', err);
    return null;
  }
}


export interface AnalysisRequest {
  english_transcript: string;
  original_transcript?: string;
  detected_lang?: string;
}

export interface LegalResource {
  id: string;
  title: string;
  section?: string;
  type?: string;
  excerpt?: string;
  side?: string;
  similarity?: number;
}

export interface AnalysisResponse {
  status: string;
  input_metadata: {
    language: string;
    original_text: string;
    analyzed_text: string;
  };
  data: {
    summary: string;
    structured_data: {
      prosecution_resources?: LegalResource[];
      binding_precedents?: LegalResource[];
      procedural_resources?: LegalResource[];
      defense_resources?: LegalResource[];
      recent_judgments?: LegalResource[];
      entities?: any[];
      statutory_provisions?: LegalResource[];
    };
    graph_data?: any;
  };
}

export async function transcribeAudio(uri: string, language: string = 'auto'): Promise<{
  english_transcript: string,
  original_transcript?: string,
  detected_lang: string
}> {
  const formData = new FormData();

  if (Platform.OS === 'web') {
    // For web, we need to fetch the blob from the URI first
    const response = await fetch(uri);
    const blob = await response.blob();
    formData.append('audio', blob, 'audio.m4a');
  } else {
    // @ts-ignore
    formData.append('audio', {
      uri,
      name: 'audio.m4a',
      type: 'audio/m4a',
    });
  }

  formData.append('language', language);

  const res = await fetch(API_TRANSCRIBE, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}

export async function extractResources(data: AnalysisRequest): Promise<NormalizedAnalysisResponse> {
  const res = await fetch(API_EXTRACT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  return normalizeUnifiedResponse(json);
}

export async function analyzeDocument(fileUri: string, fileName: string): Promise<NormalizedAnalysisResponse> {
  const fd1 = new FormData();
  const fd2 = new FormData();

  if (Platform.OS === 'web') {
    const response = await fetch(fileUri);
    const blob = await response.blob();
    fd1.append('file', blob, fileName);
    fd2.append('file', blob, fileName);
  } else {
    const fileObj = {
      uri: fileUri,
      name: fileName,
      type: 'application/octet-stream',
    } as any;
    fd1.append('file', fileObj);
    fd2.append('file', fileObj);
  }

  const [res1, res2] = await Promise.all([
    fetch(API_ANALYZE, { method: 'POST', body: fd1 }),
    fetch(API_ARGUMENTS, { method: 'POST', body: fd2 }),
  ]);

  const [json1, json2] = await Promise.all([
    res1.json(),
    res2.json(),
  ]);

  return normalizeUnifiedResponse(json1, json2);
}

export async function uploadAndAnalyze(file: File): Promise<NormalizedAnalysisResponse> {
  const fd1 = new FormData();
  fd1.append('file', file);
  const fd2 = new FormData();
  fd2.append('file', file);
  const [analysisRes, argsRes] = await Promise.all([
    fetch(API_ANALYZE, { method: 'POST', body: fd1 }).then((r) => r.json()),
    fetch(API_ARGUMENTS, { method: 'POST', body: fd2 }).then((r) => r.json()),
  ]);

  return normalizeUnifiedResponse(analysisRes, argsRes);
}

/**
 * Call only the /analyze endpoint (case analysis + bounding-box data).
 */
export async function analyzeCaseOnly(fileUri: string, fileName: string): Promise<NormalizedAnalysisResponse> {
  const fd = new FormData();
  if (Platform.OS === 'web') {
    const response = await fetch(fileUri);
    const blob = await response.blob();
    fd.append('file', blob, fileName);
  } else {
    fd.append('file', { uri: fileUri, name: fileName, type: 'application/octet-stream' } as any);
  }
  const res = await fetch(API_ANALYZE, { method: 'POST', body: fd });
  if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
  const json = await res.json();
  return normalizeUnifiedResponse(json);
}

/**
 * Call only the /arguments endpoint (argument generation + adversarial).
 */
export async function generateArgumentsOnly(fileUri: string, fileName: string): Promise<NormalizedAnalysisResponse> {
  const fd = new FormData();
  if (Platform.OS === 'web') {
    const response = await fetch(fileUri);
    const blob = await response.blob();
    fd.append('file', blob, fileName);
  } else {
    fd.append('file', { uri: fileUri, name: fileName, type: 'application/octet-stream' } as any);
  }
  const res = await fetch(API_ARGUMENTS, { method: 'POST', body: fd });
  if (!res.ok) throw new Error(`Argument generation failed (${res.status})`);
  const json = await res.json();
  return normalizeUnifiedResponse(json);
}

/**
 * Generate arguments from raw text (text-input flow).
 */
export async function generateArgumentsFromText(text: string): Promise<NormalizedAnalysisResponse> {
  const res = await fetch(API_BASE + '/api/v1/arguments/text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Argument generation failed (${res.status})`);
  const json = await res.json();
  return normalizeUnifiedResponse(json);
}

/**
 * Analyze case from raw text (text-input flow).
 */
export async function analyzeCaseFromText(text: string): Promise<NormalizedAnalysisResponse> {
  const res = await fetch(API_BASE + '/api/v1/analyze/text', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Analysis failed (${res.status})`);
  const json = await res.json();
  return normalizeUnifiedResponse(json);
}

// --- NORMALIZATION LAYER ---

export interface SourceSpanData {
  field_id: string;
  page: number;
  start_char: number;
  end_char: number;
  matched_text: string;
}

export interface PageTextData {
  page_num: number;
  text: string;
}

export interface NormalizedAnalysisResponse {
  status: string;
  analyzed_case?: AnalyzedCase;
  arguments_report?: ArgumentsReport;
  document_text?: PageTextData[];
  source_spans?: SourceSpanData[];
  // Legacy support for Component 1
  input_metadata?: AnalysisResponse['input_metadata'];
  data?: AnalysisResponse['data'];
}

export function normalizeUnifiedResponse(item1: any, item2?: any): NormalizedAnalysisResponse {
  const normalized: NormalizedAnalysisResponse = {
    status: item1.status || 'success',
  };

  // Case 1: Unified Analysis (AnalyzeCaseResponse)
  if (item1.analyzed_case) {
    normalized.analyzed_case = item1.analyzed_case;
    normalized.data = {
      summary: item1.analyzed_case.incident_timeline?.what_happened || '',
      structured_data: {
        prosecution_resources: item1.analyzed_case.argument_synthesis?.prosecution_logic?.map((s: string) => ({ title: s })),
        defense_resources: item1.analyzed_case.argument_synthesis?.defense_logic?.map((s: string) => ({ title: s })),
      }
    };
  }

  // Bounding-box data from the /analyze endpoint
  if (item1.document_text) {
    normalized.document_text = item1.document_text;
  }
  if (item1.source_spans) {
    normalized.source_spans = item1.source_spans;
  }

  // Case 2: Arguments Report (ArgumentsResponse)
  const argsData = item2 || item1;
  if (argsData.arguments_report) {
    normalized.arguments_report = argsData.arguments_report;
  }

  // Case 3: Legacy Component 1 (AnalysisResponse)
  if (item1.input_metadata && item1.data) {
    normalized.input_metadata = item1.input_metadata;
    normalized.data = item1.data;
  }

  return normalized;
}

export interface SimilarCase {
  case_id?: string;
  id?: string;
  similarity?: number;
  similarity_score?: number;
}

export interface ArgumentItem {
  perspective?: string;
  title?: string;
  content?: string;
  strength_score?: number;
  supporting_cases?: string[];
  judge_names?: string[];
  judge_statements?: string[];
  legal_principles?: string[];
  penal_codes?: string[];
  argument_points?: string[];
  model_extracted_points?: string[];
}

export interface CounterArgument {
  strategy?: string;
  counter_content?: string;
  rebuttal?: string;
  strength_score?: number;
  weak_points?: string[];
}

export interface EnhancedArgument {
  original?: Partial<ArgumentItem>;
  counter_arguments?: CounterArgument[];
}

export interface SimulationSummary {
  total_arguments_tested?: number;
  total_counter_arguments?: number;
  most_common_counter_strategy?: string;
}

export interface AdversarialResults {
  enhanced_arguments?: EnhancedArgument[];
  simulation_summary?: SimulationSummary;
  strategic_recommendations?: string[];
}

export interface ArgumentsReport {
  case_id?: string;
  cluster_id?: number;
  similar_cases?: SimilarCase[];
  arguments?: ArgumentItem[];
  adversarial_results?: AdversarialResults;
}

export interface CaseHeader {
  file_number?: string;
  date_of_analysis?: string;
  subject?: string;
}

export interface IncidentTimeline {
  what_happened?: string;
  where_it_happened?: string;
}

export interface ArgumentSynthesis {
  prosecution_logic?: string[];
  defense_logic?: string[];
}

export interface AnalyzedCase {
  case_header?: CaseHeader;
  incident_timeline?: IncidentTimeline;
  argument_synthesis?: ArgumentSynthesis;
  // Backend wraps the parsed case inside analyzed_case_file
  analyzed_case_file?: {
    case_header?: CaseHeader;
    incident_timeline?: IncidentTimeline;
    argument_synthesis?: ArgumentSynthesis;
    parties_and_roles?: {
      accused?: string;
      complainant?: string;
    };
    final_judicial_opinion?: string;
  };
  // Allow arbitrary extra fields from backend
  [key: string]: any;
}

// ── Component 4 chat ──────────────────────────────────────────────────

export interface Comp4ChatRequest {
  message: string;
  session_id?: string;
}

export interface Comp4ChatData {
  Section?: string;
  Simple_Explanation?: string;
  Example?: string;
  Punishment?: string;
  Next_Steps?: string[];
}

export interface Comp4ChatResponse {
  english_data: Comp4ChatData;
  tamil_data?: Comp4ChatData;
  sinhala_data?: Comp4ChatData;
  detected_lang: string;
  cached: boolean;
  elapsed_ms?: number;
}

export async function chatWithComp4(data: Comp4ChatRequest): Promise<Comp4ChatResponse> {
  const res = await fetch(API_COMP4_CHAT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error('Failed to fetch from comp4 API');
  }
  return res.json();
}