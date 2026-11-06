// "同步" button: triggers /api/sync and shows the latest workflow run status.
(() => {
  const button = document.getElementById("sync-button");
  const status = document.getElementById("sync-status");
  if (!button || !status) return;
  let timer = null;

  const show = (text, busy) => {
    status.textContent = text;
    button.disabled = busy;
  };

  const describe = (run) => {
    if (!run) return ["", false];
    if (run.status !== "completed") return ["同步中…", true];
    if (run.conclusion === "success") {
      const minutes = Math.round((Date.now() - Date.parse(run.updated_at)) / 60000);
      return [minutes < 10 ? "同步完成，1–2 分钟后刷新页面可见" : "", false];
    }
    return ["上次同步失败", false];
  };

  const poll = async () => {
    try {
      const res = await fetch("/api/sync", { cache: "no-store" });
      const data = await res.json();
      if (!res.ok) return show(data.error === "not_configured" ? "同步未配置" : "", false);
      const [text, busy] = describe(data.run);
      show(text, busy);
      clearTimeout(timer);
      if (busy) timer = setTimeout(poll, 15000);
    } catch {
      show("", false);
    }
  };

  button.addEventListener("click", async () => {
    show("正在触发…", true);
    try {
      const res = await fetch("/api/sync", { method: "POST" });
      const data = await res.json();
      if (res.status === 202) {
        show("同步中…", true);
        timer = setTimeout(poll, 10000);
      } else if (res.status === 409) {
        show("同步中…", true);
        timer = setTimeout(poll, 15000);
      } else if (res.status === 429) {
        show("刚同步过，请 3 分钟后再试", false);
      } else {
        show(data.error === "not_configured" ? "同步未配置" : "触发失败", false);
      }
    } catch {
      show("触发失败", false);
    }
  });

  poll();
})();
