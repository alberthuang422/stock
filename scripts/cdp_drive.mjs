// 极简 CDP 直连驱动：node cdp_drive.mjs <url> <exprFile> [waitMs]
// 用于绕过 web-access proxy，直接对接 127.0.0.1:9222
const [, , url, exprFile, waitMsRaw] = process.argv;
const waitMs = parseInt(waitMsRaw || "6000", 10);
const base = "http://127.0.0.1:9222";

async function newTarget() {
  // 新版 Chrome 需 PUT
  let r = await fetch(`${base}/json/new?about:blank`, { method: "PUT" });
  if (!r.ok) r = await fetch(`${base}/json/new?about:blank`);
  return await r.json();
}

function connect(wsUrl) {
  return new Promise((res, rej) => {
    const ws = new WebSocket(wsUrl);
    let id = 0;
    const pending = new Map();
    ws.onopen = () => res({
      send(method, params = {}) {
        return new Promise((ok, no) => {
          const mid = ++id;
          pending.set(mid, { ok, no });
          ws.send(JSON.stringify({ id: mid, method, params }));
        });
      },
      close: () => ws.close(),
    });
    ws.onerror = (e) => rej(new Error("ws error"));
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.id && pending.has(m.id)) {
        const { ok, no } = pending.get(m.id);
        pending.delete(m.id);
        m.error ? no(new Error(JSON.stringify(m.error))) : ok(m.result);
      }
    };
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const t = await newTarget();
  const c = await connect(t.webSocketDebuggerUrl);
  await c.send("Page.enable");
  await c.send("Runtime.enable");
  if (url && url !== "-") {
    await c.send("Page.navigate", { url });
    await sleep(waitMs);
  }
  let expr = "document.title";
  if (exprFile && exprFile !== "-") {
    const fs = await import("node:fs");
    expr = fs.readFileSync(exprFile, "utf8");
  }
  const r = await c.send("Runtime.evaluate", {
    expression: expr, awaitPromise: true, returnByValue: true, timeout: 300000,
  });
  const out = r.result && "value" in r.result ? r.result.value : JSON.stringify(r);
  console.log(typeof out === "string" ? out : JSON.stringify(out, null, 1));
  c.close();
  process.exit(0);
})().catch((e) => { console.error("ERR:", e.message); process.exit(1); });
