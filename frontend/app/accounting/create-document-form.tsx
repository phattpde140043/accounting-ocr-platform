"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { uploadAccountingDocument } from "../lib/accounting-api";

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const ALLOWED_FILE_TYPES = new Set([
  "application/pdf",
  "image/png",
  "image/jpeg"
]);

export function CreateDocumentForm() {
  const router = useRouter();
  const [status, setStatus] = useState("");
  const [selectedFile, setSelectedFile] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const file = form.get("file");
    if (!(file instanceof File)) {
      setStatus("Choose a PDF, JPG or PNG file");
      return;
    }
    const validationError = validateUploadFile(file);
    if (validationError) {
      setStatus(validationError);
      return;
    }
    setIsUploading(true);
    setStatus("Uploading...");
    try {
      await uploadAccountingDocument({
        file,
        clientCompanyId: String(form.get("client_company_id")),
        accountingPeriod: String(form.get("accounting_period")),
        documentType: String(form.get("document_type")),
        category: String(form.get("category"))
      });
      setStatus("Document uploaded");
      formElement.reset();
      setSelectedFile("");
      router.refresh();
    } catch {
      setStatus("Could not upload document");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <form className="panel form-grid" onSubmit={submit}>
      <h3>Upload document</h3>
      <input name="client_company_id" placeholder="client_acme" required />
      <input name="accounting_period" placeholder="2026-05" required />
      <input name="document_type" defaultValue="invoice" required />
      <input name="category" defaultValue="sales" required />
      <input
        name="file"
        type="file"
        accept="application/pdf,image/png,image/jpeg"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0];
          setSelectedFile(file ? `${file.name} (${formatBytes(file.size)})` : "");
          setStatus(file ? validateUploadFile(file) : "");
        }}
        required
      />
      {selectedFile ? <p className="muted">{selectedFile}</p> : null}
      <button className="button" type="submit" disabled={isUploading}>
        {isUploading ? "Uploading..." : "Upload"}
      </button>
      <p className="muted">{status}</p>
    </form>
  );
}

function validateUploadFile(file: File): string {
  if (!ALLOWED_FILE_TYPES.has(file.type)) {
    return "Only PDF, JPG and PNG files are supported";
  }
  if (file.size > MAX_UPLOAD_BYTES) {
    return "File must be 10 MB or smaller";
  }
  return "";
}

function formatBytes(size: number): string {
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}
