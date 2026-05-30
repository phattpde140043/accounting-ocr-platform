if (!window.__opsbridgeRegionOcrActive) {
  window.__opsbridgeRegionOcrActive = true;
  let startPoint = null;
  let activeBox = null;
  const MAX_REGION_DIMENSION = 5000;
  const MIN_REGION_DIMENSION = 4;

function createBox() {
  const box = document.createElement("div");
  box.className = "opsbridge-region-box";
  document.body.appendChild(box);
  return box;
}

document.addEventListener("mousedown", (event) => {
  if (!event.altKey) return;
  startPoint = { x: event.clientX, y: event.clientY };
  activeBox = createBox();
});

document.addEventListener("mousemove", (event) => {
  if (!startPoint || !activeBox) return;
  const x = Math.min(startPoint.x, event.clientX);
  const y = Math.min(startPoint.y, event.clientY);
  const width = Math.abs(event.clientX - startPoint.x);
  const height = Math.abs(event.clientY - startPoint.y);
  Object.assign(activeBox.style, {
    left: `${x}px`,
    top: `${y}px`,
    width: `${width}px`,
    height: `${height}px`
  });
});

document.addEventListener("mouseup", (event) => {
  if (!startPoint || !activeBox) return;
  const region = {
    page: 1,
    x: Math.min(startPoint.x, event.clientX),
    y: Math.min(startPoint.y, event.clientY),
    width: Math.abs(event.clientX - startPoint.x),
    height: Math.abs(event.clientY - startPoint.y)
  };
  if (
    region.width < MIN_REGION_DIMENSION ||
    region.height < MIN_REGION_DIMENSION ||
    region.width > MAX_REGION_DIMENSION ||
    region.height > MAX_REGION_DIMENSION
  ) {
    showStatus("Select a region between 4 and 5000 pixels.", true);
  } else {
    chrome.runtime.sendMessage(
      { type: "OPSBRIDGE_REGION_SELECTED", region },
      (response) => {
        if (chrome.runtime.lastError) {
          showStatus(chrome.runtime.lastError.message, true);
          return;
        }
        showStatus(
          response?.ok ? "Region OCR completed." : response?.error || "Region OCR failed.",
          !response?.ok
        );
      }
    );
  }
  setTimeout(() => activeBox?.remove(), 600);
  startPoint = null;
  activeBox = null;
});

function showStatus(message, isError) {
  const status = document.createElement("div");
  status.className = "opsbridge-region-status";
  status.textContent = message;
  status.dataset.error = String(isError);
  document.body.appendChild(status);
  setTimeout(() => status.remove(), 4000);
}
}
