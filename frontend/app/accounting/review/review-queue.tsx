"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AccountingDocument,
  OcrField,
  OcrResult,
  getOcrResult
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
    return field.confidence < 0.75;
  }
  if (filter === "medium") {
    return field.confidence >= 0.75 && field.confidence < 0.9;
  }
  return field.confidence >= 0.9;
}

export function ReviewQueue({ initialDocuments }: ReviewQueueProps) {
  const [documents] = useState(initialDocuments);
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
                </div>
                {visibleFields.map((field) => (
                  <div className="field-preview-row" key={field.id}>
                    <span>
                      <strong>{field.key}</strong>
                      <small>{field.source}</small>
                    </span>
                    <span>{field.value ?? ""}</span>
                    <span className="muted">
                      {Math.round(field.confidence * 100)}%
                    </span>
                  </div>
                ))}
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
