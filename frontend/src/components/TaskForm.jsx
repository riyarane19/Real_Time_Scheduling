import React, { useState } from "react";

const defaultTask = { name: "", execution_time: "", period: "", deadline: "" };

export default function TaskForm({ onSimulate, isLoading }) {
  const [task, setTask] = useState(defaultTask);
  const [tasks, setTasks] = useState([]);
  const [algorithm, setAlgorithm] = useState("RM");
  const [duration, setDuration] = useState(200);

  const handleAddTask = () => {
    if (!task.name || !task.execution_time || !task.period || !task.deadline) return;
    setTasks([...tasks, { ...task, execution_time: Number(task.execution_time), period: Number(task.period), deadline: Number(task.deadline) }]);
    setTask(defaultTask);
  };

  const handleSimulate = () => {
    if (!tasks.length) return;
    onSimulate({
      tasks,
      algorithm,
      duration: Number(duration) || 200,
    });
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">Task Set &amp; Algorithm</div>
          <div className="card-description">
            Define periodic tasks and choose a scheduling policy. The simulator runs in 1 ms steps.
          </div>
        </div>
        <span className="chip">Input</span>
      </div>

      <div className="field-group">
        <div>
          <label>Task name</label>
          <input
            placeholder="T1, Motor, UI..."
            value={task.name}
            onChange={(e) => setTask({ ...task, name: e.target.value })}
          />
        </div>
        <div>
          <label>WCET / C (ms)</label>
          <input
            type="number"
            min="0"
            placeholder="e.g., 2"
            value={task.execution_time}
            onChange={(e) => setTask({ ...task, execution_time: e.target.value })}
          />
        </div>
        <div>
          <label>Period / T (ms)</label>
          <input
            type="number"
            min="1"
            placeholder="e.g., 10"
            value={task.period}
            onChange={(e) => setTask({ ...task, period: e.target.value })}
          />
        </div>
        <div>
          <label>Deadline / D (ms)</label>
          <input
            type="number"
            min="1"
            placeholder="e.g., 10"
            value={task.deadline}
            onChange={(e) => setTask({ ...task, deadline: e.target.value })}
          />
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
        <button type="button" className="button-secondary" onClick={handleAddTask}>
          + Add task
        </button>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <div style={{ width: 130 }}>
            <label>Algorithm</label>
            <select value={algorithm} onChange={(e) => setAlgorithm(e.target.value)}>
              <option value="RM">Rate Monotonic (RM)</option>
              <option value="DM">Deadline Monotonic (DM)</option>
              <option value="EDF">Earliest Deadline First (EDF)</option>
              <option value="LLF">Least Laxity First (LLF)</option>
            </select>
          </div>
          <div style={{ width: 120 }}>
            <label>Duration (ms)</label>
            <input
              type="number"
              min="10"
              placeholder="200"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="tag-row">
        <span className="tag-pill">Periodic model</span>
        <span className="tag-pill">Single-core</span>
        <span className="tag-pill">Preemptive</span>
      </div>

      <div className="task-list">
        <div className="task-row-header task-row">
          <span>Task</span>
          <span>WCET</span>
          <span>Period</span>
          <span>Deadline</span>
        </div>
        {tasks.length === 0 && (
          <div style={{ fontSize: "0.78rem", color: "#64748b", padding: "4px 2px" }}>
            No tasks yet. Add a few tasks to start the simulation.
          </div>
        )}
        {tasks.map((t, idx) => (
          <div key={idx} className="task-row">
            <span>{t.name}</span>
            <span>{t.execution_time} ms</span>
            <span>{t.period} ms</span>
            <span>{t.deadline} ms</span>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 12, display: "flex", justifyContent: "flex-end" }}>
        <button
          type="button"
          className="button"
          disabled={isLoading || !tasks.length}
          onClick={handleSimulate}
        >
          {isLoading ? "Simulating..." : "Run simulation"}
        </button>
      </div>
    </div>
  );
}
