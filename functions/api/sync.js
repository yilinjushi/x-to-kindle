// Cloudflare Pages Function behind the site's "同步" button.
// POST /api/sync  -> dispatch the Publish Bookmarks workflow (latest 10 unsynced bookmarks)
// GET  /api/sync  -> status of the most recent run
// Requires the Pages secret GITHUB_TOKEN: a fine-grained token limited to
// yilinjushi/x-to-kindle with "Actions: Read and write".
// POST also requires the Pages secret SYNC_PASSWORD, sent in the X-Sync-Password header.

const REPO = "yilinjushi/x-to-kindle";
const WORKFLOW = "publish-bookmarks.yml";
const COOLDOWN_MS = 3 * 60 * 1000;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

const enc = new TextEncoder();

async function safeEqual(a, b) {
  const [da, db] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b)),
  ]);
  const x = new Uint8Array(da), y = new Uint8Array(db);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

async function gh(env, path, init = {}) {
  return fetch(`https://api.github.com/repos/${REPO}${path}`, {
    ...init,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "User-Agent": "x-to-kindle-sync",
      "X-GitHub-Api-Version": "2022-11-28",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
    },
  });
}

async function latestRun(env) {
  const res = await gh(env, `/actions/workflows/${WORKFLOW}/runs?per_page=1`);
  if (!res.ok) throw new Error(`GitHub ${res.status}`);
  const run = (await res.json()).workflow_runs?.[0];
  if (!run) return null;
  return {
    status: run.status, // queued | in_progress | completed ...
    conclusion: run.conclusion, // success | failure | null ...
    created_at: run.created_at,
    updated_at: run.updated_at,
  };
}

export async function onRequestGet({ env }) {
  if (!env.GITHUB_TOKEN) return json({ error: "not_configured" }, 503);
  try {
    return json({ run: await latestRun(env) });
  } catch (e) {
    return json({ error: String(e.message || e) }, 502);
  }
}

export async function onRequestPost({ env, request }) {
  if (!env.GITHUB_TOKEN || !env.SYNC_PASSWORD) return json({ error: "not_configured" }, 503);
  if (!(await safeEqual(request.headers.get("X-Sync-Password") || "", env.SYNC_PASSWORD))) {
    return json({ error: "bad_password" }, 401);
  }
  // Only accept same-origin button presses.
  const origin = request.headers.get("Origin");
  if (origin && origin !== new URL(request.url).origin) return json({ error: "forbidden" }, 403);
  try {
    const run = await latestRun(env);
    if (run && run.status !== "completed") return json({ state: "running", run }, 409);
    if (run && Date.now() - Date.parse(run.created_at) < COOLDOWN_MS) {
      return json({ state: "cooldown", run }, 429);
    }
    const res = await gh(env, `/actions/workflows/${WORKFLOW}/dispatches`, {
      method: "POST",
      body: JSON.stringify({ ref: "main", inputs: { count: "50", max_new: "10" } }),
    });
    if (!res.ok) return json({ error: `GitHub ${res.status}` }, 502);
    return json({ state: "started" }, 202);
  } catch (e) {
    return json({ error: String(e.message || e) }, 502);
  }
}
