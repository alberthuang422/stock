// 渲染验证 51 号报告：检查 ECharts 是否正常初始化、无 JS 报错（不截图，仅验证）
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
  const fileUrl = "file:///" + path.resolve(__dirname, "../reports/51_MCD_SBUX_DJI_XLY_相关性/index.html").replace(/\\/g, "/");
  let target = null, sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP;
    await sess.send("Page.enable");

    // 收集 console / 页面错误
    const errs = [];
    sess.send("Runtime.enable").catch(() => {});
    sess.send("Log.enable").catch(() => {});
    const origSend = sess.send.bind(sess);
    // 直接在页面里用 echarts 实例数检查
    await sess.send("Page.navigate", { url: fileUrl });
    await sleep(6000);
    const expr = `(() => {
      const canvases = document.querySelectorAll('canvas').length;
      const charts = echarts.getInstanceByDom(document.getElementById('chart_roll_dji'));
      const bodyTextLen = document.body.innerText.length;
      const titles = [...document.querySelectorAll('h1,h2')].map(x => x.innerText);
      // 检查每个 ECharts 容器是否渲染出 canvas
      const ids = ['chart_roll_dji','chart_roll_xly','chart_norm_mcd','chart_norm_sbux','chart_year','chart_monthly','chart_rel'];
      const rendered = ids.map(i => { const el = document.getElementById(i); return i + ':' + (el && el.querySelector('canvas') ? 'OK' : 'EMPTY'); });
      return JSON.stringify({ canvases, chartRollInit: !!charts, bodyTextLen, titles, rendered });
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