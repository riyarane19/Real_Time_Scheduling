/*
  Real-Time Scheduler Visualizer (vanilla JS)
  Backend: FastAPI (default: http://localhost:8000)
*/

const BACKEND_URL = "http://localhost:8000";
let lastInput = null;
let lastOutput = null;


const el = {
  pdfBtn: document.getElementById("pdfBtn"),
  backendStatus: document.getElementById("backendStatus"),
  taskTbody: document.getElementById("taskTbody"),
  addTaskBtn: document.getElementById("addTaskBtn"),
  runBtn: document.getElementById("runBtn"),
  algoSelect: document.getElementById("algoSelect"),
  simTime: document.getElementById("simTime"),
  gantt: document.getElementById("gantt"),
  metrics: document.getElementById("metrics"),
  runMsg: document.getElementById("runMsg"),
};

let taskIdSeq = 1;

function hashToHue(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h % 360;
}

function taskColor(name) {
  const hue = hashToHue(name || "task");
  return `hsl(${hue} 75% 52%)`;
}

function setBackendStatus(ok, text) {
  el.backendStatus.classList.toggle("ok", !!ok);
  el.backendStatus.classList.toggle("bad", !ok);
  el.backendStatus.querySelector(".status-text").textContent = text;
}

async function downloadPDF() {
  if (!lastInput || !lastOutput) {
    alert("Please run the simulation first.");
    return;
  }

  try {
    const payload = { input: lastInput, output: lastOutput };

    const r = await fetch("http://localhost:8000/export/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!r.ok) {
      throw new Error("PDF generation failed");
    }

    const blob = await r.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "schedule_report.pdf";
    a.click();
  } catch (e) {
    console.error(e);
    alert("PDF download failed. Check console.");
  }
}


function makeCellInput({ value = "", type = "text", min, placeholder = "" }) {
  const input = document.createElement("input");
  input.type = type;
  input.value = value;
  if (min !== undefined) input.min = String(min);
  input.placeholder = placeholder;
  return input;
}

function addTaskRow(task = {}) {
  const tr = document.createElement("tr");
  tr.dataset.rowId = String(taskIdSeq++);

  const tdName = document.createElement("td");
  const name = makeCellInput({ value: task.name ?? `Task${tr.dataset.rowId}`, placeholder: "MotorCtrl" });
  tdName.appendChild(name);

  const tdPeriod = document.createElement("td");
  const period = makeCellInput({ value: task.period ?? 100, type: "number", min: 1 });
  tdPeriod.appendChild(period);

  const tdExec = document.createElement("td");
  const exec = makeCellInput({ value: task.execution_time ?? 20, type: "number", min: 1 });
  tdExec.appendChild(exec);

  const tdDeadline = document.createElement("td");
  const deadline = makeCellInput({ value: task.deadline ?? "", type: "number", min: 1, placeholder: "(defaults to period)" });
  tdDeadline.appendChild(deadline);

  const tdRemove = document.createElement("td");
  const rm = document.createElement("button");
  rm.className = "btn icon";
  rm.type = "button";
  rm.textContent = "×";
  rm.title = "Remove";
  rm.addEventListener("click", () => {
    tr.remove();
  });
  tdRemove.appendChild(rm);

  tr.append(tdName, tdPeriod, tdExec, tdDeadline, tdRemove);
  el.taskTbody.appendChild(tr);
}

function readTasksFromTable() {
  
  const rows = Array.from(el.taskTbody.querySelectorAll("tr"));
  const tasks = rows.map((tr) => {
    const inputs = tr.querySelectorAll("input");
    const [nameEl, periodEl, execEl, deadlineEl] = inputs;
    const name = String(nameEl.value || "").trim();
    const period = Number(periodEl.value);
    const execution_time = Number(execEl.value);
    const dlRaw = String(deadlineEl.value || "").trim();
    const deadline = dlRaw === "" ? null : Number(dlRaw);
    return { name, period, execution_time, deadline };
  });

  // Basic validation (front-end friendly)
  for (const t of tasks) {
    if (!t.name) throw new Error("Task name cannot be empty.");
    if (!Number.isFinite(t.period) || t.period <= 0) throw new Error(`Invalid period for task '${t.name}'.`);
    if (!Number.isFinite(t.execution_time) || t.execution_time <= 0) throw new Error(`Invalid execution time for task '${t.name}'.`);
    if (t.deadline !== null && (!Number.isFinite(t.deadline) || t.deadline <= 0)) throw new Error(`Invalid deadline for task '${t.name}'.`);
  }
  if (tasks.length === 0) throw new Error("Add at least one task.");

  return tasks;
}

function clearOutput() {
  el.gantt.innerHTML = "";
  el.metrics.innerHTML = "";
}

function renderMetrics(payload) {
  const m = payload.metrics;
  const cards = [
    {
      title: "CPU Utilization",
      value: `${(m.cpu_utilization * 100).toFixed(1)}%`,
      sub: "Sum(C/T) across all tasks",
    },
    {
      title: "Preemptive Switches",
      value: String(m.preemptive_switches ?? 0),
      sub: "Number of task preemptions during simulation",
    },

    {
      title: "Total deadline misses",
      value: String(m.total_deadline_misses),
      sub: m.total_deadline_misses === 0 ? "No misses observed in this run" : "Misses observed in this run",
    },
    {
      title: "Hyperperiod (approx)",
      value: `${m.hyperperiod} ms`,
      sub: "LCM of task periods (if computable)",
    },
  ];

  const wrap = document.createElement("div");
  wrap.className = "metrics-grid";
  for (const c of cards) {
    const d = document.createElement("div");
    d.className = "metric";
    d.innerHTML = `
      <div class="metric-title">${c.title}</div>
      <div class="metric-value">${c.value}</div>
      <div class="metric-sub">${c.sub}</div>
    `;
    wrap.appendChild(d);
  }

  const perTask = document.createElement("div");
  perTask.className = "per-task";
  const items = Object.entries(m.deadline_misses_by_task || {}).map(([k, v]) => {
    return `<span class="pill"><span class="swatch" style="background:${taskColor(k)}"></span>${k}: <b>${v}</b></span>`;
  });
  perTask.innerHTML = `
    <div class="metric-title">Deadline misses per task</div>
    <div class="pill-row">${items.join("")}</div>
  `;

  el.metrics.append(wrap, perTask);
}

function renderGantt(payload) {
  const simTime = payload.simulation_time;
  const tasks = payload.tasks.map((t) => t.name);
  const timeline = payload.timeline || [];

  // Axis
  const axis = document.createElement("div");
  axis.className = "gantt-axis";

  const ticks = 6; // 0, 20, 40, 60, 80, 100%
  for (let i = 0; i < ticks; i++) {
    const x = (i / (ticks - 1)) * 100;
    const t = Math.round((i / (ticks - 1)) * simTime);
    const tick = document.createElement("div");
    tick.className = "gantt-tick";
    tick.style.left = `${x}%`;
    tick.innerHTML = `<span>${t}</span>`;
    axis.appendChild(tick);
  }

  // Build rows
  const rowsWrap = document.createElement("div");
  rowsWrap.className = "gantt-rows";

  for (const name of tasks) {
    const row = document.createElement("div");
    row.className = "gantt-row";

    const label = document.createElement("div");
    label.className = "gantt-label";
    label.textContent = name;

    const lane = document.createElement("div");
    lane.className = "gantt-lane";

    // segments for this task
    const segs = timeline.filter((s) => s.task === name);
    for (const s of segs) {
      const left = (s.start / simTime) * 100;
      const width = ((s.end - s.start) / simTime) * 100;
      const block = document.createElement("div");
      block.className = "gantt-block";
      block.style.left = `${left}%`;
      block.style.width = `${Math.max(width, 0)}%`;
      block.style.background = taskColor(name);
      block.title = `${name}: ${s.start}–${s.end} ms`;
      lane.appendChild(block);
    }

    row.append(label, lane);
    rowsWrap.appendChild(row);
  }

  // Legend
  const legend = document.createElement("div");
  legend.className = "legend";
  legend.innerHTML = tasks
    .map((n) => `<span class="legend-item"><span class="swatch" style="background:${taskColor(n)}"></span>${n}</span>`)
    .join("");

  el.gantt.append(axis, rowsWrap, legend);
}

async function runSimulation() {
  clearOutput();
  el.runMsg.textContent = "Running…";

  try {
    const tasks = readTasksFromTable();
    const algo = el.algoSelect.value;
    const simulation_time = Number(el.simTime.value);
    if (!Number.isFinite(simulation_time) || simulation_time <= 0) {
      throw new Error("Simulation time must be a positive number.");
    }

    const body = { tasks, algorithm: algo, simulation_time };
    lastInput = body;
    const r = await fetch(`${BACKEND_URL}/schedule`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await r.json();
    lastOutput = data;
    if (!r.ok || data.error) {
      throw new Error(data.error || `Request failed (HTTP ${r.status})`);
    }

    renderGantt(data);
    renderMetrics(data);
  el.runMsg.textContent =
  `Done. Algorithm: ${data.algorithm}. ` +
  `Deadline misses: ${data.metrics.total_deadline_misses}. ` +
  `Preemptions: ${data.metrics.preemptive_switches ?? 0}.`;

  } catch (e) {
    el.runMsg.textContent = `Error: ${e.message || e}`;
  }
}
async function downloadPDF() {
  const payload = { input: lastInput, output: lastOutput };
  const r = await fetch("http://localhost:8000/export/pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "schedule_report.pdf";
  a.click();
}

// Init
addTaskRow({ name: "MotorCtrl", period: 100, execution_time: 20, deadline: "" });
addTaskRow({ name: "TempCtrl", period: 200, execution_time: 30, deadline: "" });
addTaskRow({ name: "WaterLevel", period: 300, execution_time: 40, deadline: "" });

el.addTaskBtn.addEventListener("click", () => addTaskRow());
el.runBtn.addEventListener("click", runSimulation);
el.pdfBtn.addEventListener("click", downloadPDF);

checkBackend();
