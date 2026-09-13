// TV 导出·通用版：argv 控制 symbol / 周期 / 起始日期(可选)
// 用法: node tv_export_any.cjs [symbol] [interval] [startDate]
// 例:   node tv_export_any.cjs "NYMEX:CLQ2026" "1小时"          → 默认可见范围
//       node tv_export_any.cjs "NASDAQ:AAPL"  "天" "2000-01-01" → 自定义起始
const fs = require("fs");
const path = require("path");
const os = require("os");
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

const SYMBOL = process.argv[2] || null;
const INTERVAL = process.argv[3] || null;
const START_DATE = process.argv[4] || null;

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
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 400));
  return r.result && r.result.value;
}
async function clickAt(sess, x, y) {
  await sess.send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y });
  await sleep(120);
  await sess.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await sleep(80);
  await sess.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
}
async function centerOf(sess, selExpr) {
  return evalJS(sess, `(() => { const e = ${selExpr}; if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; })()`);
}
async function clickExactText(sess, text, yMin = 0, yMax = 9999) {
  const pos = await evalJS(sess, `(() => {
    let el = null;
    document.querySelectorAll('*').forEach(e => {
      const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join('');
      if (own === ${JSON.stringify(text)} && e.getBoundingClientRect().width > 0) {
        const r = e.getBoundingClientRect();
        if (r.y >= ${yMin} && r.y <= ${yMax}) el = e;
      }
    });
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 };
  })()`);
  if (pos) await clickAt(sess, pos.x, pos.y);
  return pos;
}
const DL_ITEM = `(() => { let el = null; document.querySelectorAll('*').forEach(e => { const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(''); if (own === '下载图表数据…' && e.getBoundingClientRect().width > 0) el = e; }); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; })()`;

(async () => {
  const DL_DIR = path.join(os.homedir(), "Downloads");
  const before = new Set(fs.readdirSync(DL_DIR).filter(f => f.toLowerCase().endsWith(".csv")));

  const tabs = await fetch(CDP + "/json").then(r => r.json());
  let page = tabs.find(t => t.type === "page" && t.url.includes("/chart"));
  if (!page) throw new Error("no chart tab");
  const sess = await mkSession(page.webSocketDebuggerUrl);
  await sess.openP; await sess.send("Page.enable"); await sess.send("Runtime.enable");

  // 0. 激活窗口
  await sess.send("Page.bringToFront");
  await sleep(800);
  console.log("[0] 窗口聚焦:", await evalJS(sess, `document.hasFocus()`));

  // 1. 切品种（导航）
  if (SYMBOL) {
    const url = `https://cn.tradingview.com/chart/?symbol=${encodeURIComponent(SYMBOL)}`;
    await sess.send("Page.navigate", { url });
    console.log("[1] 导航到", SYMBOL);
    await sleep(10000);
  }

  // 2. 切周期
  if (INTERVAL) {
    const pos = await clickExactText(sess, INTERVAL, 0, 120);
    if (pos) { console.log("[2] 已切周期:", INTERVAL); await sleep(4000); }
    else console.log("[2] ⚠️ 未找到周期按钮:", INTERVAL);
  }

  // 3. 可选：自定义起始日期
  if (START_DATE) {
    const goto = await centerOf(sess, `document.querySelector('[data-name="go-to-date"]')`);
    await clickAt(sess, goto.x, goto.y);
    await sleep(1800);
    const val = await evalJS(sess, `(async () => {
      const input = document.querySelector('input[name="start-date-range"]');
      input.focus();
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      setter.call(input, '');
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await new Promise(r => setTimeout(r, 200));
      setter.call(input, ${JSON.stringify(START_DATE)});
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
      await new Promise(r => setTimeout(r, 300));
      return input.value;
    })()`);
    console.log("[3] 起始日期:", val);
    const confirm = await centerOf(sess, `[...document.querySelectorAll('button')].find(b => (b.textContent||'').trim() === '前往到' && b.getBoundingClientRect().width > 0)`);
    await clickAt(sess, confirm.x, confirm.y);
    await sleep(6000);
  }

  console.log("    当前:", await evalJS(sess, `document.title`));

  // 4. 管理布局 → 下载图表数据…
  let dlItem = await evalJS(sess, DL_ITEM);
  if (!dlItem) {
    const btn = await centerOf(sess, `[...document.querySelectorAll('[data-name="save-load-menu"]')].find(x => x.getBoundingClientRect().width > 0)`);
    await clickAt(sess, btn.x, btn.y);
    await sleep(1800);
    dlItem = await evalJS(sess, DL_ITEM);
  }
  if (!dlItem) throw new Error("菜单项「下载图表数据…」未出现");
  await clickAt(sess, dlItem.x, dlItem.y);
  console.log("[4] 已点击「下载图表数据…」");
  await sleep(2000);

  // 5. 确认「下载」
  const dlgBtns = await evalJS(sess, `(() => {
    const btns = [...document.querySelectorAll('button')].filter(b => b.getBoundingClientRect().width > 0 && /下载|导出|export|download/i.test(b.textContent||''));
    return btns.map(b => { const r = b.getBoundingClientRect(); return { txt: (b.textContent||'').trim().slice(0,30), x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) }; });
  })()`);
  console.log("[5] 确认按钮:", JSON.stringify(dlgBtns));
  if (!dlgBtns.length) throw new Error("未找到确认按钮");
  await clickAt(sess, dlgBtns[dlgBtns.length - 1].x, dlgBtns[dlgBtns.length - 1].y);

  // 6. 等 CSV 新文件
  let csvFile = null;
  for (let i = 0; i < 40; i++) {
    const now = fs.readdirSync(DL_DIR).filter(f => f.toLowerCase().endsWith(".csv"));
    const nf = now.find(f => !before.has(f));
    if (nf) { csvFile = nf; break; }
    await sleep(1000);
  }
  if (!csvFile) throw new Error("40s 内未见 CSV 落盘");
  const p = path.join(DL_DIR, csvFile);
  await sleep(1500);
  const content = fs.readFileSync(p, "utf8").trim().split("\n");
  console.log(`[6] SUCCESS: ${p}`);
  console.log(`    行数: ${content.length}`);
  console.log(`    表头: ${content[0]}`);
  console.log(`    首行: ${content[1]}`);
  console.log(`    末行: ${content[content.length - 1]}`);
  sess.close();
  process.exit(0);
})().catch(e => { console.error("ERR:", e.message); process.exit(1); });