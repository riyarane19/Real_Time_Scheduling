from asyncio import tasks
from turtle import width
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import io
from reportlab.lib import colors


TASK_COLORS = [
    colors.limegreen,
    colors.deepskyblue,
    colors.salmon,
    colors.orange,
    colors.violet,
]


def draw_gantt_diagram(c, timeline, tasks, sim_time, y_start, page_width):
    if not timeline:
        c.drawString(40, y_start, "No execution timeline available.")
        return y_start - 20

    left = 120
    right = page_width - 40
    width = right - left
    row_h = 22

    # Task → row index + color
    task_rows = {}
    for i, task in enumerate(tasks):
        task_rows[task] = {
            "row": i,
            "color": TASK_COLORS[i % len(TASK_COLORS)]
        }

    # Draw axis
    c.setStrokeColor(colors.grey)
    for t in range(0, sim_time + 1, max(1, sim_time // 5)):
        x = left + (t / sim_time) * width
        c.line(x, y_start + 5, x, y_start - len(tasks) * row_h - 5)
        c.drawString(x - 5, y_start + 10, str(t))

    # Draw rows
    for task, info in task_rows.items():
        y = y_start - info["row"] * row_h

        # lane background
        c.setFillColor(colors.whitesmoke)
        c.rect(left, y - 14, width, 16, fill=1, stroke=0)

        # label
        c.setFillColor(colors.black)
        c.drawString(40, y - 12, task)

    # Draw execution blocks
    for seg in timeline:
        task = seg.get("task")
        if task is None or task not in task_rows:
            continue

        start = seg["start"]
        end = seg["end"]

        x = left + (start / sim_time) * width
        w = ((end - start) / sim_time) * width
        y = y_start - task_rows[task]["row"] * row_h - 14

        c.setFillColor(task_rows[task]["color"])
        c.roundRect(x, y, w, 14, 4, fill=1)

    return y_start - len(tasks) * row_h - 30



def generate_schedule_pdf(input_data: dict, output_data: dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 40
    # Task names (used in multiple sections)
    tasks = [t.get("name", "") for t in input_data.get("tasks", [])]

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Real-Time Scheduling Report")
    y -= 30

    #c.setFont("Helvetica", 10)
    #c.drawString(40, y, f"Generated on: {datetime.now()}")
    #y -= 40

    # INPUT DATA
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Input Tasks")
    y -= 20
    
    c.setFont("Helvetica", 10)
    for task in input_data.get("tasks", []):
        name = task.get("name", "")
        period = task.get("period", "")
        exec_time = task.get("execution_time", "")
        deadline = task.get("deadline")
        if deadline in (None, ""):
            deadline = period

        c.drawString(
        50,
        y,
        f"{name:12}  P={period} ms   C={exec_time} ms   D={deadline} ms"
        )
        y -= 15

    y -= 10



    # OUTPUT DATA
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Scheduling Results")
    y -= 20

    algo = output_data.get("algorithm", "N/A")
    metrics = output_data.get("metrics", {})

    total_misses = metrics.get("total_deadline_misses", "N/A")
    cpu_util = metrics.get("cpu_utilization", "N/A")
    hyperperiod = metrics.get("hyperperiod", "N/A")

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Algorithm: {algo}")
    y -= 15
    c.drawString(50, y, f"Total Deadline Misses: {total_misses}")
    y -= 15
    c.drawString(
    50,
    y,
    f"CPU Utilization: {round(cpu_util * 100, 1)}%"
)
    y -= 20
    c.drawString(50, y, f"Hyperperiod (approx): {hyperperiod} ms")
    y -= 25
    # Deadline misses per task
    misses_by_task = metrics.get("deadline_misses_by_task", {})

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Deadline Misses per Task")
    y -= 15

    c.setFont("Helvetica", 10)
    for task_name in tasks:
        misses = misses_by_task.get(task_name, 0)
        c.drawString(70, y, f"{task_name}: {misses}")
        y -= 12


    y -= 20

    # GANTT DIAGRAM
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Execution Timeline (Gantt Diagram)")
    y -= 30

    timeline = output_data.get("timeline", [])
    sim_time = output_data.get("simulation_time", 1)

    y = draw_gantt_diagram(
    c,
    timeline,
    tasks,
    sim_time,   
    y,
    width
)


    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.read()
