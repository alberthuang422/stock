// 渲染自检：打开报告页，检查 echarts 加载 + canvas 渲染 + 捕获 console 错误
const fs = require("fs");
const path = require("path");

const REPORT = "file:///" + path.resolve(__dirname, "../reports/35_网安vs网络设备/index.html").replace(/\\/g, "/");
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function cdpSession(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let idc = 0;
  const pending = new Map();
  const errors = [];
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
    if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") {
      errors.push(m.params.args.map(a => a.value || a.description || "").join(" "));
    }
    if (m.method === "Runtime.exceptionThrown") {
      errors.push(m.params.exceptionDetails.text + " " + (m.params.exceptionDetails.exception?.description || ""));
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++idc;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { openP, send, errors, close: () => { try { ws.close(); } catch {} } };
}

(async () => {
  let target = null, sess = null;
  try {
    const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
    target = await resp.json();
    sess = await cdpSession(target.webSocketDebuggerUrl);
    await sess.openP;
    await sess.send("Page.enable");
    await sess.send("Runtime.enable");
    await sess.send("Page.navigate", { url: REPORT });
    await sleep(6000);
    const r = await sess.send("Runtime.evaluate", {
      expression: `JSON.stringify({
        echartsLoaded: typeof echarts !== "undefined",
        charts: document.querySelectorAll("canvas").length,
        divs: document.querySelectorAll(".chart").length,
        bodyText: document.body.innerText.slice(0, 200)
      })`,
      returnByValue: true
    });
    console.log("CHECK:", r.result.value);
    console.log("CONSOLE_ERRORS:", sess.errors.length ? sess.errors.slice(0, 5) : "none");
    // 截图仅作验证不交付
    const shot = await sess.send("Page.captureScreenshot", { format: "png" });
    const pngPath = path.resolve(__dirname, "../results/31_csco_panw_crwd_ssr_check.png");
    fs.writeFileSync(pngPath, Buffer.from(shot.data, "base64"));
    console.log("screen saved:", pngPath, Buffer.from(shot.data, "base64").length, "bytes");
  } catch (e) {
    console.error("ERR:", e.message);
    process.exit(1);
  } finally {
    if (sess) sess.close();
    if (target && target.id) { try { await fetch(`${CDP}/json/close/${target.id}`); } catch {} }
  }
})();