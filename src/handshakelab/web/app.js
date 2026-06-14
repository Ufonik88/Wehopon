let selected = null;
let currentJobId = null;

const $ = (id) => document.getElementById(id);

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

async function init() {
  try {
    const health = await api("/api/health");
    const pill = $("healthStatus");
    pill.textContent = health.doctor_ok ? "Ready" : "Setup needed";
    pill.className = "status-pill " + (health.doctor_ok ? "ok" : "warn");

    const aiStatus = $("aiStatus");
    aiStatus.textContent = health.ai_available
      ? "(API key detected)"
      : "(optional — set HANDSHAKELAB_AI_API_KEY)";

    const ifaces = await api("/api/interfaces");
    const sel = $("ifaceSelect");
    sel.innerHTML = "";
    (ifaces.interfaces || []).forEach((iface) => {
      const opt = document.createElement("option");
      opt.value = iface;
      opt.textContent = iface;
      if (iface === ifaces.default) opt.selected = true;
      sel.appendChild(opt);
    });
    if (!sel.options.length) {
      const opt = document.createElement("option");
      opt.value = "wlan0";
      opt.textContent = "wlan0 (default)";
      sel.appendChild(opt);
    }
  } catch (e) {
    $("healthStatus").textContent = "Server error";
    console.error(e);
  }
}

$("scanBtn").addEventListener("click", async () => {
  const btn = $("scanBtn");
  const iface = $("ifaceSelect").value;
  btn.disabled = true;
  btn.textContent = "Scanning…";
  $("scanHint").textContent = "Scanning — this may take 10–30 seconds…";

  try {
    const data = await api("/api/scan", {
      method: "POST",
      body: JSON.stringify({ iface }),
    });
    renderNetworks(data.networks || []);
    $("scanHint").textContent = `Found ${data.count} network(s) on ${iface}.`;
  } catch (e) {
    $("scanHint").textContent = "Scan failed: " + e.message;
  } finally {
    btn.disabled = false;
    btn.textContent = "Scan";
  }
});

function renderNetworks(networks) {
  const list = $("networkList");
  list.classList.remove("empty");
  list.innerHTML = "";

  if (!networks.length) {
    list.classList.add("empty");
    list.innerHTML = '<p class="placeholder">No networks found.</p>';
    return;
  }

  networks.forEach((n) => {
    const el = document.createElement("div");
    el.className = "net-item";
    el.innerHTML = `
      <div class="net-ssid">${escapeHtml(n.ssid)}</div>
      <div class="net-meta">${n.bssid} · ch ${n.channel ?? "?"} · ${n.rssi ?? "?"} dBm · ${escapeHtml(n.security || "")}</div>
    `;
    el.addEventListener("click", () => selectNetwork(n, el));
    list.appendChild(el);
  });
}

function selectNetwork(n, el) {
  selected = n;
  document.querySelectorAll(".net-item").forEach((i) => i.classList.remove("selected"));
  el.classList.add("selected");
  $("actionCard").hidden = false;
  $("selectedTarget").innerHTML = `
    <strong>${escapeHtml(n.ssid)}</strong><br/>
    <span style="color:var(--muted)">${n.bssid} · channel ${n.channel ?? "auto"}</span>
  `;
  updateStartBtn();
}

function updateStartBtn() {
  $("startBtn").disabled = !($("ackCheck").checked && selected);
}

$("ackCheck").addEventListener("change", updateStartBtn);

$("startBtn").addEventListener("click", async () => {
  if (!selected) return;
  $("startBtn").disabled = true;
  $("progressCard").hidden = false;
  $("resultCard").hidden = true;
  $("logBox").textContent = "";
  setProgress(0, "starting", "Launching auto-crack pipeline…");

  try {
    const job = await api("/api/autocrack", {
      method: "POST",
      body: JSON.stringify({
        iface: $("ifaceSelect").value,
        ssid: selected.ssid,
        bssid: selected.bssid,
        channel: selected.channel,
        ack_authorized: $("ackCheck").checked,
        use_ai: $("aiCheck").checked,
      }),
    });
    currentJobId = job.id;
    watchJob(job.id);
  } catch (e) {
    setProgress(0, "error", e.message);
    $("startBtn").disabled = false;
  }
});

function watchJob(jobId) {
  const es = new EventSource(`/api/job/${jobId}/events`);
  es.onmessage = (ev) => {
    const job = JSON.parse(ev.data);
    setProgress(job.percent, job.stage, job.message);

    if (job.new_logs && job.new_logs.length) {
      const box = $("logBox");
      box.textContent += job.new_logs.join("\n") + "\n";
      box.scrollTop = box.scrollHeight;
    }

    if (job.status === "success" && job.password) {
      showResult(job.password, job.method);
      es.close();
      $("startBtn").disabled = false;
    } else if (job.status === "failed") {
      $("passwordBox").textContent = "Not recovered";
      $("passwordBox").style.color = "var(--danger)";
      $("resultCard").hidden = false;
      $("resultMeta").textContent = job.error || job.message;
      es.close();
      $("startBtn").disabled = false;
    }
  };
  es.onerror = () => es.close();
}

function setProgress(pct, stage, msg) {
  $("progressFill").style.width = pct + "%";
  $("progressStage").textContent = stage;
  $("progressMsg").textContent = msg;
}

function showResult(password, method) {
  $("resultCard").hidden = false;
  $("passwordBox").textContent = password;
  $("passwordBox").style.color = "var(--accent)";
  $("resultMeta").textContent = method ? `Recovered via ${method}` : "";
}

$("copyBtn").addEventListener("click", () => {
  const text = $("passwordBox").textContent;
  if (text && text !== "—" && text !== "Not recovered") {
    navigator.clipboard.writeText(text);
    $("copyBtn").textContent = "Copied!";
    setTimeout(() => ($("copyBtn").textContent = "Copy password"), 1500);
  }
});

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

init();