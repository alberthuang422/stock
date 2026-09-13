// 探针：真实点击 save-load-menu 后全量 dump 含关键字的元素 + 截图
const fs = require("fs");
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

function mkSession(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let idc = 0; const pending = new Map();
  const openP = new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws open")); });
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); } };
  const send = (method, params = {}) => new Promise((res, rej) => { const id = ++idc; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })); });
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}
async function evalJS(sess, expr) {
  const r = await sess.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 300));
  return r.result && r.result.value;
}

(async () => {
  const tabs = await fetch(CDP + "/json").then(r => r.json());
  const page = tabs.find(t => t.type === "page" && t.url.includes("tradingview"));
  const sess = await mkSession(page.webSocketDebuggerUrl);
  await sess.openP;
  await sess.send("Page.enable"); await sess.send("Runtime.enable");

  // 确保在图表页
  if (!page.url.includes("/chart")) {
    await sess.send("Page.navigate", { url: "https://cn.tradingview.com/chart/?symbol=NASDAQ%3AAAPL" });
    await sleep(9000);
  }
  console.log("URL:", page.url.slice(0, 80));

  // 真实点击 save-load-menu
  const rect = await evalJS(sess, `(() => { const el = document.querySelector('[data-name="save-load-menu"]'); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; })()`);
  console.log("按钮位置:", JSON.stringify(rect));
  await sess.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: rect.x, y: rect.y });
  await sess.send("Input.dispatchMouseEvent", { type: "mousePressed", x: rect.x, y: rect.y, button: "left", clickCount: 1 });
  await sleep(80);
  await sess.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: rect.x, y: rect.y, button: "left", clickCount: 1 });
  console.log("已点击，等待菜单 …");
  await sleep(2000);

  // 全量 dump：含关键字的任何元素（无过滤）
  const kwDump = await evalJS(sess, `(() => {
    const kw = /导出|export|csv|下载|download|另存|副本|重命名|发布/i;
    const out = [];
    document.querySelectorAll('body *').forEach(e => {
      const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(' ');
      if (own && kw.test(own)) {
        const r = e.getBoundingClientRect();
        out.push({ txt: own.slice(0, 50), tag: e.tagName, w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) });
      }
    });
    return out.slice(0, 30);
  })()`);
  console.log("含关键字元素:", JSON.stringify(kwDump, null, 2));

  // 截图
  const shot = await sess.send("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync("/tmp/tv_menu_click.png", Buffer.from(shot.data, "base64"));
  console.log("截图: /tmp/tv_menu_click.png");

  sess.close();
  process.exit(0);
})().catch(e => { console.error("ERR:", e.message); process.exit(1); });