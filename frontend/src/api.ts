export const API_URL = import.meta.env.VITE_API_URL ?? "/api";

export type User = {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: "admin" | "doctor";
  is_active: boolean;
  created_at: string;
  updated_at: string;
};
export type Patient = {
  id: string;
  first_name: string;
  last_name: string;
  birth_date: string;
  sex: string;
  created_at: string;
  updated_at: string;
};
export type ClinicalData = {
  id: string;
  patient_id: string;
  age: number | null;
  hypertension: boolean | null;
  heart_disease: boolean | null;
  ever_married: "Yes" | "No" | null;
  work_type:
    | "Private"
    | "Self-employed"
    | "children"
    | "Govt_job"
    | "Never_worked"
    | null;
  residence_type: "Urban" | "Rural" | null;
  avg_glucose_level: number | null;
  bmi: number | null;
  smoking_status: string | null;
  created_at: string;
  updated_at: string;
};
export type ImagingStudy = {
  id: string;
  patient_id: string;
  modality: string;
  original_filename: string;
  original_file_uri: string;
  sha256: string;
  file_size: number;
  status: string;
  created_at: string;
  metadata_json: Record<string, string>;
};
export type ModelResult = {
  status: string;
  model_version: string | null;
  error_message: string | null;
  risk_score?: number | null;
  risk_label?: string | null;
  lesion_detected?: boolean | null;
  lesion_volume_ml?: number | null;
  mask_uri?: string | null;
  preview_uri?: string | null;
};
export type Analysis = {
  id: string;
  patient_id: string;
  clinical_data_id: string | null;
  imaging_study_id: string | null;
  status: string;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
  tabular_result: ModelResult | null;
  imaging_result: ModelResult | null;
};
export type Validation = {
  id: string;
  analysis_id: string;
  doctor_id: string;
  validation_status: string;
  comment: string | null;
  validated_at: string;
};
export type Report = {
  id: string;
  analysis_id: string;
  status: string;
  llm_status: string;
  deterministic_report_uri: string;
  llm_enriched_report_uri: string | null;
  llm_approved_by: string | null;
  generated_at: string;
};
export type AuditEvent = {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details_json: Record<string, unknown>;
  created_at: string;
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function detailMessage(data: unknown): string {
  if (typeof data === "object" && data && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail
        .map((item) =>
          typeof item === "object" && item && "msg" in item
            ? String(item.msg)
            : String(item),
        )
        .join(" · ");
  }
  return "Une erreur est survenue.";
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem("access_token");
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    let data: unknown = null;
    try {
      data = await response.json();
    } catch {
      /* response without JSON */
    }
    if (response.status === 401) localStorage.removeItem("access_token");
    throw new ApiError(response.status, detailMessage(data));
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export function jsonBody(value: unknown): Pick<RequestInit, "body"> {
  return { body: JSON.stringify(value) };
}

export async function downloadExport(exportId: string): Promise<void> {
  const token = localStorage.getItem("access_token");
  const response = await fetch(`${API_URL}/exports/${exportId}/download`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok)
    throw new ApiError(response.status, "Téléchargement impossible.");
  const blob = await response.blob();
  const disposition = response.headers.get("content-disposition") ?? "";
  const filename = disposition.match(/filename="?([^";]+)"?/)?.[1] ?? "rapport";
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
