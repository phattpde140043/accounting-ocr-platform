"use client";

import { useMemo, useState } from "react";
import {
  AccountingDocumentRow,
  createExportBatch,
  downloadExportBatch,
  ExportFormat
} from "../lib/accounting-api";

type ExportPanelProps = {
  documents: AccountingDocumentRow[];
};

export function ExportPanel({ documents }: ExportPanelProps) {
  const approvedDocuments = useMemo(
    () => documents.filter((document) => document.status === "approved"),
    [documents]
  );
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [format, setFormat] = useState<ExportFormat>("json");
  const [message, setMessage] = useState("");
  const [isExporting, setIsExporting] = useState(false);

  function toggleDocument(documentId: string) {
    setSelectedIds((current) =>
      current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId]
    );
  }

  async function exportDocuments() {
    if (selectedIds.length === 0) {
      return;
    }

    setIsExporting(true);
    setMessage("");
    try {
      const batch = await createExportBatch(selectedIds, format);
      const artifact = await downloadExportBatch(batch.id);
      const url = window.URL.createObjectURL(artifact.blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = artifact.fileName;
      anchor.click();
      window.URL.revokeObjectURL(url);
      setMessage(`Downloaded ${artifact.fileName}`);
    } catch {
      setMessage("Export could not be generated. Check the API service and retry.");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <section className="panel export-panel">
      <div className="panel-heading">
        <div>
          <h3>Export approved documents</h3>
          <p className="muted">
            Select validated records and generate an accounting-ready artifact.
          </p>
        </div>
        <label>
          Template
          <select
            value={format}
            onChange={(event) => setFormat(event.target.value as ExportFormat)}
          >
            <option value="json">JSON</option>
            <option value="misa">MISA CSV</option>
            <option value="fast">FAST CSV</option>
          </select>
        </label>
      </div>
      {approvedDocuments.length === 0 ? (
        <p className="muted">No approved documents are ready for export.</p>
      ) : (
        <div className="export-document-list">
          {approvedDocuments.map((document) => (
            <label className="export-document-row" key={document.id}>
              <input
                type="checkbox"
                checked={selectedIds.includes(document.id)}
                onChange={() => toggleDocument(document.id)}
              />
              <span>
                <strong>{document.company}</strong>
                <small>{document.type} · {document.period}</small>
              </span>
            </label>
          ))}
        </div>
      )}
      <div className="review-actions">
        <button
          className="button"
          disabled={selectedIds.length === 0 || isExporting}
          onClick={exportDocuments}
          type="button"
        >
          {isExporting ? "Generating..." : "Download export"}
        </button>
        {message ? <p className="muted">{message}</p> : null}
      </div>
    </section>
  );
}
