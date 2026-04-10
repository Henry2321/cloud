async function readJson(response) {
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.message || "Request failed");
  }

  return payload;
}

// KHAI BÁO ĐƯỜNG LINK API GATEWAY THẬT TỪ AWS
const API_BASE_URL = "https://qf2xb7lha4.execute-api.us-east-1.amazonaws.com";

export async function getDashboardSummary(signal) {
  const response = await fetch(`${API_BASE_URL}/api/dashboard-summary`, {
    signal,
  });
  return readJson(response);
}

// ĐÃ SỬA: Dùng API_BASE_URL thay cho localhost:8000
export async function getSpamIps(signal) {
  const response = await fetch(`${API_BASE_URL}/api/cloudwatch/spam-ips`, {
    signal,
  });
  if (!response.ok) throw new Error("Unable to load spam IPs");
  return readJson(response);
}

export async function getFindings(signal) {
  const response = await fetch(`${API_BASE_URL}/api/findings`, { signal });
  return readJson(response);
}

export async function triggerScan(signal) {
  const response = await fetch(`${API_BASE_URL}/api/scan`, {
    method: "POST",
    signal,
  });
  return readJson(response);
}

export async function remediateFinding(findingId) {
  const response = await fetch(
    `${API_BASE_URL}/api/findings/${findingId}/remediate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    },
  );

  return readJson(response);
}
