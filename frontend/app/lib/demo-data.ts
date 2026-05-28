export const metrics = [
  { label: "Documents", value: 24 },
  { label: "OCR Queue", value: 7 },
  { label: "Needs Review", value: 9 },
  { label: "Export Batches", value: 5 },
  { label: "Audit Events", value: 52 }
];

export const documents = [
  {
    id: "doc_001",
    company: "Cong ty TNHH Acme Viet Nam",
    type: "Invoice",
    status: "needs_review",
    period: "2026-05"
  },
  {
    id: "doc_002",
    company: "Minh Long Trading",
    type: "Payment Voucher",
    status: "uploaded",
    period: "2026-05"
  }
];

export const adminTasks = [
  "Google SSO and tenant resolution",
  "RBAC permission matrix",
  "Audit log and access history",
  "User invitation and password reset flow"
];
