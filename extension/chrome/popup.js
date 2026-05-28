const apiBaseUrl = document.getElementById("apiBaseUrl");
const documentId = document.getElementById("documentId");
const statusText = document.getElementById("status");

chrome.storage.sync.get(["apiBaseUrl", "documentId"], (values) => {
  if (values.apiBaseUrl) apiBaseUrl.value = values.apiBaseUrl;
  if (values.documentId) documentId.value = values.documentId;
});

document.getElementById("save").addEventListener("click", () => {
  chrome.storage.sync.set(
    {
      apiBaseUrl: apiBaseUrl.value,
      documentId: documentId.value
    },
    () => {
      statusText.textContent = "Saved";
    }
  );
});

