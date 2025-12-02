import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";

export async function simulateSchedule(payload) {
  const res = await axios.post(`${API_BASE}/simulate`, payload);
  return res.data;
}

export async function healthCheck() {
  const res = await axios.get(`${API_BASE}/health`);
  return res.data;
}
