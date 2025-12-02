import React from "react";

export default function GanttChart({ timeline }) {
  if (!timeline || !timeline.length) return null;

  return (
    <div className="gantt-container">
      <div className="card-header" style={{ padding: 0, marginBottom: 6 }}>
        <div>
          <div className="card-title">Gantt View</div>
          <div className="card-description">
            Each block represents a continuous execution segment for a task.
          </div>
        </div>
        <span className="chip">Timeline</span>
      </div>
      <div className="gantt-scroll">
        <div className="gantt-row-label">CPU</div>
        <div className="gantt-row">
          {timeline.map((slot, idx) => {
            const width = Math.max(26, slot.end - slot.start);
            const isIdle = !slot.task;
            return (
              <div
                key={idx}
                className={"gantt-slot" + (isIdle ? " gantt-slot-idle" : "")}
                style={{ minWidth: width, maxWidth: Math.max(40, width) }}
                title={
                  slot.task
                    ? `${slot.task} [${slot.start} - ${slot.end} ms]`
                    : `Idle [${slot.start} - ${slot.end} ms]`
                }
              >
                {slot.task || "idle"}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
