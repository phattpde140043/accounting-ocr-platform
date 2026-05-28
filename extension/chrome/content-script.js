let startPoint = null;
let activeBox = null;

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
  chrome.runtime.sendMessage({ type: "OPSBRIDGE_REGION_SELECTED", region });
  setTimeout(() => activeBox?.remove(), 600);
  startPoint = null;
  activeBox = null;
});

