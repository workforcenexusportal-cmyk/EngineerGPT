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

  const res = await fetch(`${API_V1}/test-report/analyze`, {
    method: "POST",
    headers: authHeader(token),
    body: form,
  });
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
