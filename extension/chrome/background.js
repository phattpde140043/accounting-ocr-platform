chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type !== "OPSBRIDGE_REGION_SELECTED") return;

  chrome.storage.local.get(["apiBaseUrl", "documentId", "accessToken"], async (values) => {
    const apiBaseUrl = values.apiBaseUrl || "http://localhost:8000/api/v1";
    const documentId = values.documentId;
    if (!documentId) {
      sendResponse({ ok: false, error: "Missing documentId" });
      return;
    }
    if (!values.accessToken) {
      sendResponse({ ok: false, error: "Missing access token" });
      return;
    }

    try {
      const response = await fetch(
        `${apiBaseUrl}/accounting/documents/${documentId}/region-ocr`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${values.accessToken}`
          },
          body: JSON.stringify({ regions: [message.region] })
        }
      );
      sendResponse({ ok: response.ok, result: await response.json() });
    } catch (error) {
      sendResponse({ ok: false, error: String(error) });
    }
  });

  return true;
});
