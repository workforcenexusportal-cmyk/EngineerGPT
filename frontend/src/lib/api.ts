/** Typed API client for the EngineerGPT backend. */

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

export interface ColumnStat {
  name: string;
  count: number;
  mean: number | null;
  std: number | null;
  minimum: number | null;
  maximum: number | null;
  missing: number;
}

export interface Anomaly {
  column: string;
  description: string;
  severity: "low" | "medium" | "high";
  sample_indices: number[];
}

export interface ChartArtifact {
  title: string;
  kind: string;
  image_base64: string;
}

export interface Finding {
  statement: string;
  confidence: number;
  citation: string;
}

export interface TestReport {
  report_id: string | null;
  title: string;
  row_count: number;
  column_count: number;
  executive_summary: string;
  statistics: ColumnStat[];
  findings: Finding[];
  anomalies: Anomaly[];
  charts: ChartArtifact[];
  conclusions: string[];
  recommendations: string[];
  generated_by: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function authHeader(token?: string): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseError(res: Response): Promise<never> {
  let detail = res.statusText;
  try {
    const body = await res.json();
    detail = body.detail ?? detail;
  } catch {
    /* non-JSON error body */
  }
  throw new ApiError(detail, res.status);
}

/** Analyze a CSV/XLSX file and return a structured test report. */
export async function analyzeTestReport(
  file: File,
  title: string,
  token?: string,
): Promise<TestReport> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);

  // FIX: surface network failures as typed errors instead of unhandled rejections.
  let res: Response;
  try {
    res = await fetch(`${API_V1}/test-report/analyze`, {
    method: "POST",
    headers: authHeader(token),
    body: form,
    });
  } catch (error) {
    throw new ApiError(error instanceof Error ? error.message : "Network request failed", 0);
  }
  if (!res.ok) return parseError(res);
  return (await res.json()) as TestReport;
}

/** Trigger a PDF export and return the blob for download. */
export async function exportTestReportPdf(
  file: File,
  title: string,
  token?: string,
): Promise<Blob> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);

  const res = await fetch(`${API_V1}/test-report/export/pdf`, {
    method: "POST",
    headers: authHeader(token),
    body: form,
  });
  if (!res.ok) return parseError(res);
  return res.blob();
}

// ---------------------------------------------------------------------------
// Authentication
// ---------------------------------------------------------------------------
export interface AuthUser {
  sub: string;
  role: "admin" | "manager" | "engineer" | "viewer";
  org_id: string | null;
}

/** Exchange email + password for a bearer token (OAuth2 password grant). */
export async function login(email: string, password: string): Promise<string> {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const res = await fetch(`${API_V1}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) return parseError(res);
  const body = (await res.json()) as { access_token: string };
  return body.access_token;
}

/** Fetch the current user described by the token. */
export async function getMe(token: string): Promise<AuthUser> {
  const res = await fetch(`${API_V1}/auth/me`, { headers: authHeader(token) });
  if (!res.ok) return parseError(res);
  return (await res.json()) as AuthUser;
}

// ---------------------------------------------------------------------------
// Knowledge Hub (documents + RAG search)
// ---------------------------------------------------------------------------
export interface DocumentSummary {
  id: string;
  filename: string;
  extension: string;
  mime: string;
  size_bytes: number;
  status: string;
  chunk_count: number;
  created_at: string;
}

export interface Citation {
  source: string;
  locator: string | null;
  excerpt: string | null;
}

export interface AIInsight {
  statement: string;
  confidence: number;
  citations: Citation[];
}

export interface AgentResult {
  module: string;
  summary: string;
  insights: AIInsight[];
  generated_by: string;
}

/** List ingested documents in the current org's corpus. */
export async function listDocuments(token: string): Promise<DocumentSummary[]> {
  const res = await fetch(`${API_V1}/knowledge/documents`, {
    headers: authHeader(token),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as DocumentSummary[];
}

/** Upload + ingest a document (extract → chunk → embed → persist). */
export async function uploadDocument(
  file: File,
  token: string,
): Promise<DocumentSummary> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_V1}/knowledge/documents`, {
    method: "POST",
    headers: authHeader(token),
    body: form,
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as DocumentSummary;
}

/** Delete a document and its chunks. */
export async function deleteDocument(id: string, token: string): Promise<void> {
  const res = await fetch(`${API_V1}/knowledge/documents/${id}`, {
    method: "DELETE",
    headers: authHeader(token),
  });
  if (!res.ok) return parseError(res);
}

/** Run a grounded RAG query over the ingested corpus. */
export async function searchKnowledge(
  query: string,
  topK: number,
  token: string,
): Promise<AgentResult> {
  const res = await fetch(`${API_V1}/knowledge/search`, {
    method: "POST",
    headers: { ...authHeader(token), "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as AgentResult;
}

// ---------------------------------------------------------------------------
// Text-analysis agent modules
// ---------------------------------------------------------------------------
async function postAgent(
  path: string,
  body: unknown,
  token: string,
): Promise<AgentResult> {
  const res = await fetch(`${API_V1}${path}`, {
    method: "POST",
    headers: { ...authHeader(token), "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as AgentResult;
}

export function analyzeFailure(
  body: { dtc_codes: string[]; sensor_data: Record<string, number>; logs: string },
  token: string,
): Promise<AgentResult> {
  return postAgent("/failure-analysis/analyze", body, token);
}

export function reviewRequirements(
  requirements: string,
  token: string,
): Promise<AgentResult> {
  return postAgent("/requirements/review", { requirements }, token);
}

export function prepareMeeting(
  body: { topic: string; context: string; open_issues: string[] },
  token: string,
): Promise<AgentResult> {
  return postAgent("/meeting-prep/prepare", body, token);
}

export function reviewDesign(
  body: { design: string; specifications: string },
  token: string,
): Promise<AgentResult> {
  return postAgent("/design-review/review", body, token);
}
