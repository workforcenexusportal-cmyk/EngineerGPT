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
// Authentication & tenancy
// ---------------------------------------------------------------------------
export type Role = "admin" | "manager" | "engineer" | "viewer";

/** Token claims returned by /auth/me. */
export interface AuthUser {
  sub: string;
  role: Role;
  org_id: string | null;
  is_superuser: boolean;
}

/** Rich user profile returned inside auth/context responses. */
export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  org_id: string | null;
  is_superuser: boolean;
}

export interface AuthSession {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface PlanInfo {
  key: string;
  label: string;
  price_usd_month: number;
  monthly_analyses: number;
  max_documents: number;
  max_members: number;
  features: string[];
}

export interface OrgInfo {
  id: string;
  name: string;
  slug: string;
  plan: string;
  subscription_status: string | null;
}

export interface UsageInfo {
  analyses_this_month: number;
  documents: number;
}

export interface SessionContext {
  user: UserProfile;
  organization: OrgInfo | null;
  plan: PlanInfo;
  usage: UsageInfo;
}

/** Exchange email + password for a bearer token + user (OAuth2 password grant). */
export async function login(email: string, password: string): Promise<AuthSession> {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);

  const res = await fetch(`${API_V1}/auth/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as AuthSession;
}

/** Self-serve signup: provisions a new organization and signs the user in. */
export async function register(input: {
  email: string;
  password: string;
  full_name?: string;
  company_name?: string;
}): Promise<AuthSession> {
  const res = await fetch(`${API_V1}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as AuthSession;
}

/** Fetch the current user described by the token. */
export async function getMe(token: string): Promise<AuthUser> {
  const res = await fetch(`${API_V1}/auth/me`, { headers: authHeader(token) });
  if (!res.ok) return parseError(res);
  return (await res.json()) as AuthUser;
}

/** Fetch identity, organization, plan, and live usage for the app shell. */
export async function getContext(token: string): Promise<SessionContext> {
  const res = await fetch(`${API_V1}/auth/context`, { headers: authHeader(token) });
  if (!res.ok) return parseError(res);
  return (await res.json()) as SessionContext;
}

// ---------------------------------------------------------------------------
// History (saved analyses)
// ---------------------------------------------------------------------------
export interface HistoryItem {
  id: string;
  module: string;
  title: string;
  generated_by: string;
  created_at: string;
}

export interface HistoryDetail extends HistoryItem {
  request: Record<string, unknown>;
  result: AgentResult;
}

export async function listHistory(
  token: string,
  opts: { module?: string; limit?: number } = {},
): Promise<HistoryItem[]> {
  const params = new URLSearchParams();
  if (opts.module) params.append("module", opts.module);
  if (opts.limit) params.append("limit", String(opts.limit));
  const qs = params.toString();
  const res = await fetch(`${API_V1}/history${qs ? `?${qs}` : ""}`, {
    headers: authHeader(token),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as HistoryItem[];
}

export async function getHistory(id: string, token: string): Promise<HistoryDetail> {
  const res = await fetch(`${API_V1}/history/${id}`, { headers: authHeader(token) });
  if (!res.ok) return parseError(res);
  return (await res.json()) as HistoryDetail;
}

export async function deleteHistory(id: string, token: string): Promise<void> {
  const res = await fetch(`${API_V1}/history/${id}`, {
    method: "DELETE",
    headers: authHeader(token),
  });
  if (!res.ok) return parseError(res);
}

// ---------------------------------------------------------------------------
// Billing (Stripe)
// ---------------------------------------------------------------------------
export interface PlanCatalogItem extends PlanInfo {
  purchasable: boolean;
}

export async function listPlans(): Promise<PlanCatalogItem[]> {
  const res = await fetch(`${API_V1}/billing/plans`);
  if (!res.ok) return parseError(res);
  return (await res.json()) as PlanCatalogItem[];
}

/** Start a Stripe Checkout session; returns the URL to redirect the user to. */
export async function createCheckout(plan: string, token: string): Promise<string> {
  const res = await fetch(`${API_V1}/billing/checkout`, {
    method: "POST",
    headers: { ...authHeader(token), "Content-Type": "application/json" },
    body: JSON.stringify({ plan }),
  });
  if (!res.ok) return parseError(res);
  return ((await res.json()) as { url: string }).url;
}

/** Open the Stripe customer portal; returns the URL to redirect to. */
export async function openBillingPortal(token: string): Promise<string> {
  const res = await fetch(`${API_V1}/billing/portal`, {
    method: "POST",
    headers: authHeader(token),
  });
  if (!res.ok) return parseError(res);
  return ((await res.json()) as { url: string }).url;
}

// ---------------------------------------------------------------------------
// Admin (platform superuser)
// ---------------------------------------------------------------------------
export interface PlatformStats {
  organizations: number;
  users: number;
  documents: number;
  analyses_total: number;
  analyses_this_month: number;
}

export interface OrgRow {
  id: string;
  name: string;
  slug: string;
  plan: string;
  subscription_status: string | null;
  members: number;
  documents: number;
  created_at: string;
}

export interface UserRow {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  org_id: string | null;
  is_superuser: boolean;
  created_at: string;
}

export async function getPlatformStats(token: string): Promise<PlatformStats> {
  const res = await fetch(`${API_V1}/admin/stats`, { headers: authHeader(token) });
  if (!res.ok) return parseError(res);
  return (await res.json()) as PlatformStats;
}

export async function listOrganizations(token: string): Promise<OrgRow[]> {
  const res = await fetch(`${API_V1}/admin/organizations`, {
    headers: authHeader(token),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as OrgRow[];
}

export async function listUsers(token: string): Promise<UserRow[]> {
  const res = await fetch(`${API_V1}/admin/users`, { headers: authHeader(token) });
  if (!res.ok) return parseError(res);
  return (await res.json()) as UserRow[];
}

export async function setOrgPlan(
  orgId: string,
  plan: string,
  token: string,
): Promise<OrgRow> {
  const res = await fetch(`${API_V1}/admin/organizations/${orgId}/plan`, {
    method: "POST",
    headers: { ...authHeader(token), "Content-Type": "application/json" },
    body: JSON.stringify({ plan }),
  });
  if (!res.ok) return parseError(res);
  return (await res.json()) as OrgRow;
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
