import { metrics as fallbackMetrics } from "./demo-data";
import { apiGet } from "./api-client";

export type DashboardMetric = {
  label: string;
  value: number;
};

type DashboardSummary = {
  role: string;
  cards: DashboardMetric[];
};

export async function getDashboardMetrics(): Promise<DashboardMetric[]> {
  try {
    const summary = await apiGet<DashboardSummary>("/dashboard/summary");
    return summary.cards;
  } catch {
    return fallbackMetrics;
  }
}
