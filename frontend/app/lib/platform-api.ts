import { apiGet } from "./api-client";

type ListResponse<T> = {
  items: T[];
};

export type AuditEvent = {
  id: string;
  actor_user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  correlation_id: string | null;
  created_at: string;
};

export async function getAuditEvents(): Promise<AuditEvent[]> {
  try {
    const response = await apiGet<ListResponse<AuditEvent>>(
      "/admin/audit-events?limit=20&offset=0"
    );
    return response.items;
  } catch {
    return [];
  }
}
