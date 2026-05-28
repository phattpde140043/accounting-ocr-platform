export default function AiPage() {
  return (
    <div className="stack">
      <section className="page-header">
        <div>
          <h2>OCR workflows</h2>
          <p>
            OCR is modeled as a provider-backed workflow with audit, background
            processing, review fields and export-ready structured data.
          </p>
        </div>
        <div className="actions">
          <a className="button" href="/accounting">Review documents</a>
          <a className="button secondary" href="#">Open region OCR</a>
        </div>
      </section>
      <section className="grid two">
        <article className="panel">
          <h3>Provider pipeline</h3>
          <p className="muted">
            Phase 3 adds OCR providers, async jobs, review fields, corrections
            and export batches.
          </p>
        </article>
        <article className="panel">
          <h3>Region OCR extension</h3>
          <p className="muted">
            The Chrome extension can capture user-selected regions and submit
            bounding boxes to the backend region OCR endpoint.
          </p>
        </article>
      </section>
    </div>
  );
}
