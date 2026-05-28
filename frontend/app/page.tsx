import { adminTasks, metrics } from "./lib/demo-data";

export default function Home() {
  return (
    <div className="stack">
      <section className="page-header">
        <div>
          <h2>Document intake backbone for accounting service teams</h2>
          <p>
            A document-first SaaS skeleton with Google SSO, RBAC, accounting
            document intake, OCR review, export batches and audit history.
          </p>
        </div>
        <div className="actions">
          <a className="button" href="/accounting">Open intake</a>
          <a className="button secondary" href="/ai">Open OCR workflows</a>
        </div>
      </section>

      <section className="grid">
        {metrics.slice(0, 3).map((metric) => (
          <article className="card" key={metric.label}>
            <h3>{metric.label}</h3>
            <p className="metric">{metric.value}</p>
          </article>
        ))}
      </section>

      <section className="grid two">
        <article className="panel">
          <h3>Backend spine</h3>
          <p className="muted">
            FastAPI routers isolate platform, accounting intake, OCR jobs,
            dashboard metrics and admin workflows behind explicit services.
          </p>
        </article>
        <article className="panel">
          <h3>Platform work ahead</h3>
          <ul>
            {adminTasks.map((task) => (
              <li key={task}>{task}</li>
            ))}
          </ul>
        </article>
      </section>
    </div>
  );
}
