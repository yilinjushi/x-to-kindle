// Cloudflare Pages middleware: password-protect the whole site.
// The password lives in the Pages secret SITE_PASSWORD (never in this repo).
// A successful login sets an HttpOnly cookie holding an HMAC derived from the
// password, so changing the secret logs everyone out.

const COOKIE = "site_auth";
const LOGIN_PATH = "/__login";
const MAX_AGE = 60 * 60 * 24 * 30; // 30 days

const enc = new TextEncoder();

async function token(password) {
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(password), { name: "HMAC", hash: "SHA-256" }, false, ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode("x-to-kindle-site-auth-v1"));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function safeEqual(a, b) {
  // Compare digests so timing does not leak length or prefix matches.
  const [da, db] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(a)),
    crypto.subtle.digest("SHA-256", enc.encode(b)),
  ]);
  const x = new Uint8Array(da), y = new Uint8Array(db);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

function getCookie(request, name) {
  const header = request.headers.get("Cookie") || "";
  for (const part of header.split(";")) {
    const i = part.indexOf("=");
    if (i > -1 && part.slice(0, i).trim() === name) return part.slice(i + 1).trim();
  }
  return "";
}

function safeNext(value) {
  // Only allow same-site relative paths to avoid open redirects.
  return typeof value === "string" && value.startsWith("/") && !value.startsWith("//") ? value : "/";
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

const SECURITY_HEADERS = {
  "Cache-Control": "no-store",
  "X-Robots-Tag": "noindex, nofollow",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
};

function loginPage(next, failed) {
  const html = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>需要密码</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;display:flex;min-height:100vh;margin:0;align-items:center;justify-content:center;background:#f6f6f4;color:#222}
form{background:#fff;padding:2rem;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,.08);width:min(320px,calc(100vw - 32px));box-sizing:border-box}
h1{font-size:1.1rem;margin:0 0 1rem}
input,button{width:100%;box-sizing:border-box;font-size:1rem;padding:.6rem;margin-top:.5rem;border-radius:8px}
input{border:1px solid #ccc}
button{border:0;background:#222;color:#fff;cursor:pointer}
p{color:#b00020;font-size:.9rem;margin:.5rem 0 0}
@media (prefers-color-scheme: dark){body{background:#111;color:#eee}form{background:#1c1c1c}input{background:#111;color:#eee;border-color:#444}button{background:#eee;color:#111}}
</style></head><body>
<form method="post" action="${LOGIN_PATH}">
<h1>请输入访问密码</h1>
<input type="hidden" name="next" value="${escapeHtml(next)}">
<input type="password" name="password" autocomplete="current-password" autofocus required>
<button type="submit">进入</button>
${failed ? "<p>密码错误</p>" : ""}
</form></body></html>`;
  return new Response(html, {
    status: 401,
    headers: {
      ...SECURITY_HEADERS,
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
    },
  });
}

export async function onRequest(context) {
  const { request, env, next } = context;
  const password = env.SITE_PASSWORD;
  if (!password) {
    // Fail closed: never serve content when the secret is missing.
    return new Response("Site password is not configured.", { status: 503, headers: SECURITY_HEADERS });
  }

  const url = new URL(request.url);
  const expected = await token(password);

  if (url.pathname === LOGIN_PATH) {
    if (request.method !== "POST") return loginPage("/", false);
    let form;
    try {
      form = await request.formData();
    } catch {
      return loginPage("/", true);
    }
    const target = safeNext(form.get("next"));
    if (await safeEqual(String(form.get("password") || ""), password)) {
      return new Response(null, {
        status: 303,
        headers: {
          ...SECURITY_HEADERS,
          Location: target,
          "Set-Cookie": `${COOKIE}=${expected}; Path=/; Max-Age=${MAX_AGE}; HttpOnly; Secure; SameSite=Lax`,
        },
      });
    }
    return loginPage(target, true);
  }

  if (await safeEqual(getCookie(request, COOKIE), expected)) {
    const response = await next();
    const out = new Response(response.body, response);
    out.headers.set("X-Robots-Tag", "noindex, nofollow");
    out.headers.set("Cache-Control", "private, max-age=0, must-revalidate");
    return out;
  }

  return loginPage(url.pathname + url.search, false);
}
