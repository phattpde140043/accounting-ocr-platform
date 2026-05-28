import { getReviewQueueDocuments } from "../../lib/accounting-api";
import { ReviewQueue } from "./review-queue";

export default async function AccountingReviewPage() {
  try {
    const documents = await getReviewQueueDocuments({ limit: 50, offset: 0 });

    return (
      <div className="stack">
        <section className="page-header">
          <div>
            <h2>Review queue</h2>
            <p>
              Work through documents that need human validation before approval
              and export.
            </p>
          </div>
          <div className="actions">
            <a className="button secondary" href="/accounting">
              Intake
            </a>
          </div>
        </section>
        <ReviewQueue initialDocuments={documents} />
      </div>
    );
  } catch {
    return (
      <div className="stack">
        <section className="page-header">
          <div>
            <h2>Review queue</h2>
            <p>
              Work through documents that need human validation before approval
              and export.
            </p>
          </div>
        </section>
        <section className="panel empty-state">
          <h3>Queue unavailable</h3>
          <p className="muted">
            The API could not load documents for review. Check the backend
            service and try again.
          </p>
        </section>
      </div>
    );
  }
}
