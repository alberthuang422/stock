// TradingView CDP 探测脚本：navigate / eval / shot / dump
// 用法示例：
//   node tv_probe.cjs navigate <url>
//   node tv_probe.cjs eval "<js>"
//   node tv_probe.cjs shot <out.png>
//   node tv_probe.cjs dump
const fs = require("fs");
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

const [, , cmd, a1, a2] = process.argv;

async function cdpSession(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let idc = 0;
  const pending = new Map();
  const openP = new Promise((res, rej) => {
    ws.onopen = res;
    ws.onerror = () => rej(new Error("ws open error"));
  });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++idc;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}

async function withTab(fn) {
  const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
  if (!resp.ok) throw new Error("new tab: " + resp.status);
  const target = await resp.json();
  const sess = await cdpSession(target.webSocketDebuggerUrl);
  await sess.openP;
  try {
    await sess.send("Page.enable");
    await sess.send("Runtime.enable");
    return await fn(sess);
  } finally {
    sess.close();
    try { await fetch(`${CDP}/json/close/${target.id}`); } catch {}
  }
}

(async () => {
  if (cmd === "navigate") {
    const url = a1;
    await withTab(async sess => {
      await sess.send("Page.navigate", { url });
      await sleep(9000);
      const r = await sess.send("Runtime.evaluate", { expression: "document.title", returnByValue: true });
      console.log("TITLE:", r.result.value);
      console.log("URL:", (await sess.send("Runtime.evaluate", { expression: "location.href", returnByValue: true })).result.value);
    });
  } else if (cmd === "dump") {
    await withTab(async sess => {
      const r = await sess.send("Runtime.evaluate", { expression: "document.body ? document.body.innerText : ''", returnByValue: true });
      console.log(r.result.value);
    });
  } else if (cmd === "eval") {
    await withTab(async sess => {
      const r = await sess.send("Runtime.evaluate", { expression: a1, returnByValue: true });
      console.log(JSON.stringify(r.result && r.result.value, null, 2));
    });
  } else if (cmd === "shot") {
    const out = a1;
    await withTab(async sess => {
      const shot = await sess.send("Page.captureScreenshot", { format: "png" });
      fs.writeFileSync(out, Buffer.from(shot.data, "base64"));
      console.log("SAVED:", out);
    });
  } else {
    console.error("unknown cmd");
    process.exit(1);
  }
})().catch(e => { console.error("ERR:", e.message); process.exit(1); });