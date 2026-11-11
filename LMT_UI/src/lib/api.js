import { reactive } from "vue";
export const account = reactive({
  user: null,
  token: localStorage.getItem("caseplay_token") || "",
});
export function saveAccount(data) {
  account.token = data.token;
  account.user = data.user;
  localStorage.setItem("caseplay_token", data.token);
}
export async function api(path, options = {}) {
  const response = await fetch(
    (import.meta.env.VITE_API_BASE || "/api") + path,
    {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...(account.token ? { Authorization: `Bearer ${account.token}` } : {}),
        ...options.headers,
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
    },
  );
  const data = await response
    .json()
    .catch(() => ({ error: "服务暂不可用，请稍后重试。" }));
  if (!response.ok) {
    if (response.status === 401 && !path.includes("/auth/login")) {
      account.token = "";
      account.user = null;
      localStorage.removeItem("caseplay_token");
    }
    throw new Error(data.error || "请求失败，请重试。");
  }
  return data;
}
export async function loadAccount() {
  if (account.token && !account.user) account.user = await api("/auth/me");
  return account.user;
}
export async function signOut() {
  try {
    await api("/auth/logout", { method: "POST" });
  } finally {
    account.user = null;
    account.token = "";
    localStorage.removeItem("caseplay_token");
  }
}
export async function exportSession(id) {
  const response = await fetch(
    (import.meta.env.VITE_API_BASE || "/api") + `/sessions/${id}/export`,
    { headers: { Authorization: `Bearer ${account.token}` } },
  );
  if (!response.ok) throw new Error("导出失败，请重新登录后重试。");
  const blob = await response.blob();
  const href = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = href;
  link.download = `caseplay-session-${id}.json`;
  link.click();
  URL.revokeObjectURL(href);
}
