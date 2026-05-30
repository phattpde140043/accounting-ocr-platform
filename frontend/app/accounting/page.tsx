import { getAccountingDocuments } from "../lib/accounting-api";
import { CreateDocumentForm } from "./create-document-form";
import { ExportPanel } from "./export-panel";

export default async function AccountingPage() {
  const documents = await getAccountingDocuments();

  return (
    <div className="stack">
      <section className="page-header">
        <div>
          <h2>Accounting intake</h2>
          <p>
            Upload invoices, vouchers and warehouse documents, then route them
            through OCR, review and export workflows.
          </p>
        </div>
        <div className="actions">
          <a className="button" href="#">Upload document</a>
          <a className="button secondary" href="#">Create client company</a>
        </div>
      </section>
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Company</th>
              <th>Type</th>
              <th>Period</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr key={document.id}>
                <td>{document.company}</td>
                <td>{document.type}</td>
                <td>{document.period}</td>
                <td><span className="status">{document.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <ExportPanel documents={documents} />
      <CreateDocumentForm />
    </div>
  );
}
