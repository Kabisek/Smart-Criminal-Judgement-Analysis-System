import { Platform } from 'react-native';
/**
 * API configuration for Smart Criminal Judgment Analysis System.
 * Point to your backend (e.g. FastAPI) when running locally or in production.
 */

const getApiBase = (): string => {
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8000`;
  }
  return 'http://127.0.0.1:8000';
};

export const API_BASE = getApiBase();
export const API_TRANSCRIBE = API_BASE + '/transcribe';
export const API_EXTRACT = API_BASE + '/extract';
export const API_ANALYZE = API_BASE + '/api/v1/analyze';
export const API_ARGUMENTS = API_BASE + '/api/v1/arguments';
export const API_HEALTH = API_BASE + '/health';
export const API_HISTORY_SAVE = API_BASE + '/api/v1/history/save';
export const API_HISTORY_LIST = API_BASE + '/api/v1/history/list';
export const API_HISTORY_FETCH = (id: string) => API_BASE + `/api/v1/history/${id}`;

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



export interface NormalizedAnalysisResponse {
  status: string;
  analyzed_case?: AnalyzedCase;
  arguments_report?: ArgumentsReport;
  
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
