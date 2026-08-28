// 渲染验证 52 号报告：检查 ECharts 是否正常初始化、无 JS 报错（不截图，仅验证）
const path = require("path");
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

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

(async () => {
  const fileUrl = "file:///" + path.resolve(__dirname, "../reports/52_持仓组合技术面与操作建议/index.html").replace(/\\/g, "/");
  let target = null, sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP;
    await sess.send("Page.enable");
    const errs = [];
    sess.send("Runtime.enable").catch(() => {});
    sess.send("Log.enable").catch(() => {});
    // 监听 console 报错
    sess.send("Runtime.evaluate", {
      expression: `window.__errs = []; window.addEventListener('error', e => window.__errs.push(e.message));`,
      returnByValue: true,
    }).catch(() => {});
    await sess.send("Page.navigate", { url: fileUrl });
    await sleep(7000);
    const expr = `(() => {
      const ids = ['CSCO','MCD','VST','APO','ABBV','GILD','SBUX','XYZ'].map(t => 'chart_' + t);
      const rendered = ids.map(i => { const el = document.getElementById(i); return i + ':' + (el && el.querySelector('canvas') ? 'OK' : 'EMPTY'); });
      const dai = document.getElementById('chart_dai');
      return JSON.stringify({
        canvases: document.querySelectorAll('canvas').length,
        bodyTextLen: document.body.innerText.length,
        titles: [...document.querySelectorAll('h1,h2')].map(x => x.innerText.slice(0, 40)),
        rendered,
        dai: dai && dai.querySelector('canvas') ? 'OK' : 'EMPTY',
        jsErrors: window.__errs || []
      });
    })()`;
    const r = await sess.send("Runtime.evaluate", { expression: expr, returnByValue: true });
    console.log("渲染检查:", r.result.value);
  } catch (e) {
    console.error("err:", e.message);
  } finally {
    if (sess) sess.close();
    if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }
  }
  console.log("DONE");
})().catch(e => { console.error("FATAL:", e); process.exit(1); });