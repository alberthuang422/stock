// 渲染验证 26 号报告：检查 ECharts 是否正常初始化（不截图，仅验证）
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
  const fileUrl = "file:///" + path.resolve(__dirname, "../reports/26_ihi_xbi_13日滚动相关/index.html").replace(/\\/g, "/");
  let target = null, sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP;
    await sess.send("Page.enable");
    await sess.send("Page.navigate", { url: fileUrl });
    await sleep(4000);
    const expr = `(() => {
      const canvases = document.querySelectorAll('canvas');
      const errs = [];
      const charts = window.echarts ? echarts.getInstanceByDom(document.getElementById('chart_compare')) : null;
      return JSON.stringify({
        canvases: canvases.length,
        chartCompareInit: !!charts,
        bodyTextLen: document.body.innerText.length,
        dataLen: (window.DATA ? Object.keys(window.DATA).length : -1),
        title: document.title
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