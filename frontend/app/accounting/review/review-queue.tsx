"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AccountingDocument,
  OcrField,
  OcrResult,
  approveOcrResult,
  getOcrResult,
  updateOcrField
} from "../../lib/accounting-api";

type ReviewQueueProps = {
  initialDocuments: AccountingDocument[];
};

type ConfidenceFilter = "all" | "low" | "medium" | "high";

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    year: "numeric"
  }).format(new Date(value));
}

function matchesFieldConfidence(
  field: OcrField,
  filter: ConfidenceFilter
): boolean {
  if (filter === "all") {
    return true;
  }

  if (filter === "low") {
    return field.confidence < 0.7;
  }
  if (filter === "medium") {
    return field.confidence >= 0.7 && field.confidence < 0.95;
  }
  return field.confidence >= 0.95;
}

export function ReviewQueue({ initialDocuments }: ReviewQueueProps) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [selectedDocumentId, setSelectedDocumentId] = useState(
    initialDocuments[0]?.id ?? ""
  );
  const [clientFilter, setClientFilter] = useState("");
  const [periodFilter, setPeriodFilter] = useState("");
  const [confidenceFilter, setConfidenceFilter] =
    useState<ConfidenceFilter>("all");
  const [ocrResult, setOcrResult] = useState<OcrResult | null>(null);
  const [isLoadingResult, setIsLoadingResult] = useState(false);
  const [resultError, setResultError] = useState("");
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});
  const [savingFieldIds, setSavingFieldIds] = useState<string[]>([]);
  const [actionMessage, setActionMessage] = useState("");
  const [isApproving, setIsApproving] = useState(false);

  useEffect(() => {
    if (!selectedDocumentId) {
      setOcrResult(null);
      return;
    }

    let isCurrent = true;
    setIsLoadingResult(true);
    setResultError("");

    getOcrResult(selectedDocumentId)
      .then((result) => {
        if (isCurrent) {
          setOcrResult(result);
          setDraftValues(
            Object.fromEntries(
              result.field_items.map((field) => [field.id, field.value ?? ""])
            )
          );
        }
      })
      .catch(() => {
        if (isCurrent) {
          setOcrResult(null);
          setResultError("OCR result is not available for this document yet.");
        }
      })
      .finally(() => {
        if (isCurrent) {
          setIsLoadingResult(false);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [selectedDocumentId]);

  const filteredDocuments = useMemo(
    () =>
      documents.filter((document) => {
        const matchesClient =
          clientFilter.trim() === "" ||
          document.client_company_id
            .toLowerCase()
            .includes(clientFilter.trim().toLowerCase());
        const matchesPeriod =
          periodFilter.trim() === "" ||
          document.accounting_period
            .toLowerCase()
            .includes(periodFilter.trim().toLowerCase());

        return (
          matchesClient &&
          matchesPeriod
        );
      }),
    [clientFilter, documents, periodFilter]
  );

  const selectedDocument = documents.find(
    (document) => document.id === selectedDocumentId
  );
  const visibleFields =
    ocrResult?.field_items.filter((field) =>
      matchesFieldConfidence(field, confidenceFilter)
    ) ?? [];

  async function saveField(field: OcrField) {
    if (!ocrResult?.result_id) {
      return;
    }
    setSavingFieldIds((current) => [...current, field.id]);
    setActionMessage("");
    try {
      const updated = await updateOcrField({
        resultId: ocrResult.result_id,
        fieldId: field.id,
        value: draftValues[field.id] ?? "",
        version: field.version
      });
      setOcrResult((current) =>
        current
          ? {
              ...current,
              field_items: current.field_items.map((item) =>
                item.id === field.id
                  ? {
                      ...item,
                      value: updated.field_value,
                      source: updated.source,
                      version: updated.version
                    }
                  : item
              )
            }
          : current
      );
      setActionMessage(`${field.key} saved.`);
    } catch {
      setActionMessage(`${field.key} could not be saved. Your edit is preserved.`);
    } finally {
      setSavingFieldIds((current) => current.filter((id) => id !== field.id));
    }
  }

  async function approveResult() {
    if (!ocrResult?.result_id || savingFieldIds.length > 0) {
      return;
    }
    setIsApproving(true);
    setActionMessage("");
    try {
      await approveOcrResult(ocrResult.result_id);
      const remainingDocuments = documents.filter(
        (document) => document.id !== selectedDocumentId
      );
      setDocuments(remainingDocuments);
      setSelectedDocumentId(remainingDocuments[0]?.id ?? "");
      setActionMessage("Document approved and removed from the review queue.");
    } catch {
      setActionMessage("Approval failed. Review required fields and try again.");
    } finally {
      setIsApproving(false);
    }
  }

  return (
    <section className="review-workbench">
      <div className="panel review-queue-panel">
        <div className="toolbar">
          <label>
            Client
            <input
              value={clientFilter}
              onChange={(event) => setClientFilter(event.target.value)}
              placeholder="Client ID"
            />
          </label>
          <label>
            Period
            <input
              value={periodFilter}
              onChange={(event) => setPeriodFilter(event.target.value)}
              placeholder="2026-05"
            />
          </label>
          <label>
            Field confidence
            <select
              value={confidenceFilter}
              onChange={(event) =>
                setConfidenceFilter(event.target.value as ConfidenceFilter)
              }
            >
              <option value="all">All</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
        </div>

        {filteredDocuments.length === 0 ? (
          <div className="empty-state">
            <h3>No documents waiting</h3>
            <p className="muted">
              There are no tenant-visible documents matching the current queue
              filters.
            </p>
          </div>
        ) : (
          <div className="queue-list" aria-label="Documents needing review">
            {filteredDocuments.map((document) => (
              <button
                className={
                  document.id === selectedDocumentId
                    ? "queue-row active"
                    : "queue-row"
                }
                key={document.id}
                onClick={() => setSelectedDocumentId(document.id)}
                type="button"
              >
                <span>
                  <strong>{document.file_name}</strong>
                  <small>{document.client_company_id}</small>
                </span>
                <span>
                  <strong>{document.accounting_period}</strong>
                  <small>{formatDate(document.created_at)}</small>
                </span>
                <span className="status">{document.status}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="panel review-detail-panel">
        {selectedDocument ? (
          <>
            <div className="detail-heading">
              <div>
                <h3>{selectedDocument.file_name}</h3>
                <p className="muted">
                  {selectedDocument.document_type} -{" "}
                  {selectedDocument.accounting_period}
                </p>
              </div>
              <span className="status">{selectedDocument.ocr_status}</span>
            </div>

            {isLoadingResult ? (
              <p className="muted">Loading OCR result...</p>
            ) : resultError ? (
              <div className="empty-state compact">
                <h3>OCR result missing</h3>
                <p className="muted">{resultError}</p>
              </div>
            ) : ocrResult ? (
              <div className="field-preview-list">
                <div className="detail-metrics">
                  <span>
                    Confidence
                    <strong>{Math.round(ocrResult.confidence * 100)}%</strong>
                  </span>
                  <span>
                    Fields
                    <strong>{visibleFields.length}</strong>
                  </span>
                  <span>
                    Route
                    <strong>{ocrResult.review_route}</strong>
                  </span>
                </div>
                {visibleFields.map((field) => (
                  <div className="field-preview-row" key={field.id}>
                    <span>
                      <strong>{field.key}</strong>
                      <small>{field.source} - v{field.version}</small>
                    </span>
                    <input
                      aria-label={`${field.key} value`}
                      onChange={(event) =>
                        setDraftValues((current) => ({
                          ...current,
                          [field.id]: event.target.value
                        }))
                      }
                      value={draftValues[field.id] ?? ""}
                    />
                    <span className="muted">
                      {Math.round(field.confidence * 100)}%
                    </span>
                    <button
                      className="button secondary compact-button"
                      disabled={savingFieldIds.includes(field.id)}
                      onClick={() => saveField(field)}
                      type="button"
                    >
                      {savingFieldIds.includes(field.id) ? "Saving..." : "Save"}
                    </button>
                  </div>
                ))}
                <div className="review-actions">
                  <button
                    className="button"
                    disabled={isApproving || savingFieldIds.length > 0}
                    onClick={approveResult}
                    type="button"
                  >
                    {isApproving ? "Approving..." : "Approve document"}
                  </button>
                  {actionMessage && <p className="muted">{actionMessage}</p>}
                </div>
              </div>
            ) : (
              <p className="muted">Select a document to load OCR details.</p>
            )}
          </>
        ) : (
          <div className="empty-state">
            <h3>No document selected</h3>
            <p className="muted">
              Choose a row from the queue to inspect its OCR details.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
