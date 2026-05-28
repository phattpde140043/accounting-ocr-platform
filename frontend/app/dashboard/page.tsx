import { metrics } from "../lib/demo-data";

export default function DashboardPage() {
  return (
    <div className="stack">
      <section className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>
            Role-specific metrics will be served by `/api/v1/dashboard/summary`.
            This screen anchors the future admin, employee and customer dashboards.
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

