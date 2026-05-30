import { getDashboardMetrics } from "../lib/dashboard-api";

export default async function DashboardPage() {
  const metrics = await getDashboardMetrics();

  return (
    <div className="stack">
      <section className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>
            Tenant-scoped operational signals for OCR throughput, review workload,
            exports and audit activity.
          </p>
        </div>
      </section>
      <section className="grid">
        {metrics.map((metric) => (
          <article className="card" key={metric.label}>
            <h3>{metric.label}</h3>
            <p className="metric">{metric.value}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
