const LOGS_API_URL = "http://127.0.0.1:5000/logs";

export async function getLogs() {
  const response = await fetch(LOGS_API_URL);
  if (!response.ok) {
    throw new Error(`Unable to load logs: ${response.status}`);
  }

  const data = await response.json();
  return Array.isArray(data) ? data : [];
}

export { LOGS_API_URL };
