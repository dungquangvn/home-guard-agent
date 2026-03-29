export async function querySecurityLogs({
  question,
  top_k = 6,
  start_time = null,
  end_time = null,
}) {
  const response = await fetch("http://127.0.0.1:5000/security_chat/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question, top_k, start_time, end_time }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Không thể truy vấn security chat.");
  }

  return data;
}
