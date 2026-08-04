let currentPayload = null;

async function fetchJson(url, options = undefined) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `HTTP ${res.status}`);
  }
  return await res.json();
}

function nodeById(id) {
  if (!currentPayload) return null;
  return currentPayload.nodes.find((n) => n.id === id) || null;
}

function renderDetail(id) {
  const target = document.getElementById("detail");
  const node = nodeById(id);
  if (!node) {
    target.textContent = "Select a record.";
    return;
  }
  const children = (currentPayload.children_map[id] || []).join(", ") || "(none)";
  const parents = (node.causes || []).join(", ") || "(none)";
  const auth = (node.authorization || []).join(" -> ") || "(none)";
  target.innerHTML = `
    <strong>${node.type}</strong><br/>
    <strong>ID:</strong> ${node.id}<br/>
    <strong>Subject:</strong> ${node.subject || "(none)"}<br/>
    <strong>Author:</strong> ${node.author}<br/>
    <strong>Created:</strong> ${node.timestamp}<br/>
    <strong>Schema:</strong> ${node.schema}<br/>
    <strong>Status:</strong> ${node.status}<br/>
    <hr/>
    <strong>Parents:</strong> ${parents}<br/>
    <strong>Children:</strong> ${children}<br/>
    <strong>Authorization:</strong> ${auth}
  `;
}

function renderGraph(payload) {
  const list = document.getElementById("graph-list");
  list.innerHTML = "";
  for (const node of payload.nodes) {
    const li = document.createElement("li");
    const btn = document.createElement("button");
    btn.textContent = `${node.type}  ${node.id}  (${node.status})`;
    btn.onclick = () => renderDetail(node.id);
    li.appendChild(btn);
    list.appendChild(li);
  }
  if (payload.nodes.length > 0) {
    renderDetail(payload.nodes[0].id);
  } else {
    renderDetail("");
  }
}

function renderTimeline(payload) {
  const list = document.getElementById("timeline");
  list.innerHTML = "";
  for (const node of payload.nodes) {
    const li = document.createElement("li");
    li.textContent = `${node.timestamp}  ${node.type}  ${node.id}`;
    list.appendChild(li);
  }
}

async function loadData() {
  const q = document.getElementById("search").value.trim();
  const payload = await fetchJson(`/api/records?search=${encodeURIComponent(q)}`);
  currentPayload = payload;
  renderGraph(payload);
  renderTimeline(payload);
}

async function loadHealth() {
  const health = await fetchJson("/api/health");
  const el = document.getElementById("health");
  el.innerHTML = `<span class="status-ok">${health.status}</span> • runtime ${health.runtime} • explorer 0.1.0`;
}

async function explainRecord() {
  const output = document.getElementById("explain-output");
  output.textContent = "";
  let parsed = null;
  try {
    parsed = JSON.parse(document.getElementById("record-json").value);
  } catch (err) {
    output.textContent = `Invalid JSON: ${String(err)}`;
    return;
  }
  try {
    const result = await fetchJson("/api/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ record: parsed }),
    });
    output.textContent = JSON.stringify(result, null, 2);
  } catch (err) {
    output.textContent = String(err);
  }
}

document.getElementById("search-btn").onclick = () => loadData().catch(console.error);
document.getElementById("reset-btn").onclick = () => {
  document.getElementById("search").value = "";
  loadData().catch(console.error);
};
document.getElementById("explain-btn").onclick = () => explainRecord().catch(console.error);

loadHealth().catch(console.error);
loadData().catch(console.error);

