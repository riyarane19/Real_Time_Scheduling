import React, { useEffect, useState } from "react";
import TaskForm from "./components/TaskForm";
import GanttChart from "./components/GanttChart";
import MetricsPanel from "./components/MetricsPanel";
import { simulateSchedule, healthCheck } from "./api";

export default function App() {
  const [timeline, setTimeline] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState("Checking API...");

  useEffect(() => {
    (async () => {
      try {
        const res = await healthCheck();
        if (res && res.status === "ok") {
          setBackendStatus("API connected");
        } else {
          setBackendStatus("API reachable, but health check unexpected");
        }
      } catch (e) {
        setBackendStatus("API not reachable. Start FastAPI on port 8000.");
      }
    })();
  }, []);

  const handleSimulate = async (payload) => {
    try {
      setLoading(true);
      const res = await simulateSchedule(payload);
      setTimeline(res.timeline || []);
      setMetrics(res.metrics || null);
    } catch (e) {
      console.error(e);
      alert("Simulation failed. Check backend logs.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header style={{ marginBottom: 22 }}>
        <h1 style={{ textAlign: "center" }}>Real-Time Scheduling Dashboard</h1>
        <div style={{ fontSize: "0.78rem", color: "#94a3b8" }}>
          Backend status: <span style={{ color: "#38bdf8" }}>{backendStatus}</span>
        </div>
      </header>

      <main className="layout-grid">
        <TaskForm onSimulate={handleSimulate} isLoading={loading} />
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Schedule &amp; Analysis</div>
              <div className="card-description">
                Visualize which task runs when and inspect basic schedulability indicators.
              </div>
            </div>
            <span className="chip">Output</span>
          </div>
          <GanttChart timeline={timeline} />
          <MetricsPanel metrics={metrics} />
        </div>
      </main>
    </div>
  );
}
