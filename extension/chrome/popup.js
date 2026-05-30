const apiBaseUrl = document.getElementById("apiBaseUrl");
const documentId = document.getElementById("documentId");
const accessToken = document.getElementById("accessToken");
const statusText = document.getElementById("status");

chrome.storage.local.get(["apiBaseUrl", "documentId", "accessToken"], (values) => {
  if (values.apiBaseUrl) apiBaseUrl.value = values.apiBaseUrl;
  if (values.documentId) documentId.value = values.documentId;
  if (values.accessToken) accessToken.value = values.accessToken;
});

document.getElementById("save").addEventListener("click", () => {
  chrome.storage.local.set(
    {
      apiBaseUrl: apiBaseUrl.value,
      documentId: documentId.value,
      accessToken: accessToken.value
    },
    () => {
      statusText.textContent = "Saved";
    }
  );
});

document.getElementById("activate").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) {
    statusText.textContent = "No active page";
    return;
  }
  try {
    await chrome.scripting.insertCSS({
      target: { tabId: tab.id },
      files: ["content-style.css"]
    });
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content-script.js"]
    });
    statusText.textContent = "Active: use Alt + drag";
  } catch (error) {
    statusText.textContent = `Activation failed: ${String(error)}`;
  }
});
