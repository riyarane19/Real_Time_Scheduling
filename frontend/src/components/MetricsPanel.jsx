import React from "react";

export default function MetricsPanel({ metrics }) {
  if (!metrics) return null;

  const totalMisses = metrics.total_deadline_misses || 0;
  const utilization = metrics.cpu_utilization?.toFixed(1) ?? "0.0";

  const perTask = metrics.per_task_deadline_misses || {};

  return (
    <div style={{ marginTop: 14 }}>
      <div className="card-header" style={{ padding: 0 }}>
        <div>
          <div className="card-title">Schedulability Metrics</div>
          <div className="card-description">
            Quick overview of utilization and observed deadline misses.
          </div>
        </div>
        <span className="chip">Metrics</span>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">CPU Utilization</div>
          <div className="metric-value">{utilization}%</div>
          <div className="metric-sub">Sum(C/T) across all tasks</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Total deadline misses</div>
          <div className="metric-value">{totalMisses}</div>
          <div className="metric-sub">
            {totalMisses === 0 ? "No misses observed in this run" : "One or more tasks missed deadlines"}
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Hyperperiod (approx)</div>
          <div className="metric-value">
            {metrics.hyperperiod_approx ? `${metrics.hyperperiod_approx} ms` : "—"}
          </div>
          <div className="metric-sub">LCM of task periods (if computable)</div>
        </div>
      </div>

      {Object.keys(perTask).length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div className="card-description" style={{ marginBottom: 4 }}>
            Deadline misses per task:
          </div>
          <div className="tag-row">
            {Object.entries(perTask).map(([name, count]) => (
              <span key={name} className="tag-pill">
                {name}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
