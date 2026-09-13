// TV 批量导出：CL 合约链 CLJ2026 → CLN2027，周期 [1小时, 天]
// 用法: node tv_export_batch.cjs [symbol ...]   （缺省=内置 16 合约全列表）
const fs = require("fs");
const path = require("path");
const os = require("os");
const CDP = "http://localhost:9222";
const DL_DIR = path.join(os.homedir(), "Downloads");
const OUT_DIR = "/Users/alberthuang/Desktop/股票分析/data/tradingview";
const INTERVALS = ["1小时", "天"];
const DEFAULT_SYMBOLS = [
  "CLJ2026","CLK2026","CLM2026","CLN2026","CLQ2026","CLU2026","CLV2026","CLX2026","CLZ2026",
  "CLF2027","CLG2027","CLH2027","CLJ2027","CLK2027","CLM2027","CLN2027"
];
const SYMBOLS = process.argv.slice(2).length ? process.argv.slice(2) : DEFAULT_SYMBOLS;
const sleep = ms => new Promise(r => setTimeout(r, ms));

function mkSession(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let idc = 0; let dlgIdc = 0; const pending = new Map();
  const openP = new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws open")); });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    // 自动处理「离开此网站？」beforeunload 原生弹窗（accept=离开）
    if (m.method === "Page.javascriptDialogOpening") {
      ws.send(JSON.stringify({ id: --dlgIdc, method: "Page.handleJavaScriptDialog", params: { accept: true } }));
      console.log("  [dialog] 自动点击「离开」:", (m.params.message || "").slice(0, 50));
      return;
    }
    if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); }
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const id = ++idc; pending.set(id, { res, rej }); ws.send(JSON.stringify({ id, method, params })); });
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}
async function evalJS(sess, expr) {
  const r = await sess.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails.exception?.description || r.exceptionDetails.text).slice(0, 300));
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

async function exportOnce(sess, interval) {
  const before = new Set(fs.readdirSync(DL_DIR).filter(f => f.toLowerCase().endsWith(".csv")));
  // 1. 切周期
  const pos = await clickExactText(sess, interval, 0, 120);
  if (!pos) throw new Error("未找到周期按钮: " + interval);
  await sleep(4000);
  // 2. 管理布局 → 下载图表数据…
  let dlItem = await evalJS(sess, `(() => { let el = null; document.querySelectorAll('*').forEach(e => { const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(''); if (own === '下载图表数据…' && e.getBoundingClientRect().width > 0) el = e; }); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; })()`);
  if (!dlItem) {
    const btn = await centerOf(sess, `[...document.querySelectorAll('[data-name="save-load-menu"]')].find(x => x.getBoundingClientRect().width > 0)`);
    await clickAt(sess, btn.x, btn.y);
    await sleep(1800);
    dlItem = await evalJS(sess, `(() => { let el = null; document.querySelectorAll('*').forEach(e => { const own = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).join(''); if (own === '下载图表数据…' && e.getBoundingClientRect().width > 0) el = e; }); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x + r.width/2, y: r.y + r.height/2 }; })()`);
  }
  if (!dlItem) throw new Error("菜单项「下载图表数据…」未出现");
  await clickAt(sess, dlItem.x, dlItem.y);
  await sleep(2000);
  // 3. 确认「下载」
  const dlgBtns = await evalJS(sess, `(() => {
    const btns = [...document.querySelectorAll('button')].filter(b => b.getBoundingClientRect().width > 0 && /下载|导出|export|download/i.test(b.textContent||''));
    return btns.map(b => { const r = b.getBoundingClientRect(); return { x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2) }; });
  })()`);
  if (!dlgBtns.length) throw new Error("未找到确认按钮");
  await clickAt(sess, dlgBtns[dlgBtns.length - 1].x, dlgBtns[dlgBtns.length - 1].y);
  // 4. 等新 CSV
  let csvFile = null;
  for (let i = 0; i < 40; i++) {
    const now = fs.readdirSync(DL_DIR).filter(f => f.toLowerCase().endsWith(".csv"));
    const nf = now.find(f => !before.has(f));
    if (nf) { csvFile = nf; break; }
    await sleep(1000);
  }
  if (!csvFile) throw new Error("40s 未落盘");
  await sleep(1200);
  // 5. 归位
  const src = path.join(DL_DIR, csvFile);
  const dst = path.join(OUT_DIR, csvFile);
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.renameSync(src, dst);
  const lines = fs.readFileSync(dst, "utf8").trim().split("\n");
  return { file: csvFile, rows: lines.length, first: lines[1] || "", last: lines[lines.length - 1] || "" };
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  const tabs = await fetch(CDP + "/json").then(r => r.json());
  const page = tabs.find(t => t.type === "page" && t.url.includes("/chart"));
  if (!page) throw new Error("no chart tab");
  const sess = await mkSession(page.webSocketDebuggerUrl);
  await sess.openP; await sess.send("Page.enable"); await sess.send("Runtime.enable");

  // 若连接时已有弹窗挂着（阻塞页面），先按掉
  await sess.send("Page.handleJavaScriptDialog", { accept: true }).catch(() => {});
  await sess.send("Page.bringToFront");
  await sleep(800);
  if (!(await evalJS(sess, `document.hasFocus()`))) throw new Error("窗口未聚焦，中止");
  console.log(`[start] ${SYMBOLS.length} 合约 × ${INTERVALS.length} 周期`);
  const results = [];
  for (const sym of SYMBOLS) {
    for (const interval of INTERVALS) {
      const tag = `${sym}·${interval}`;
      try {
        await sess.send("Page.navigate", { url: `https://cn.tradingview.com/chart/?symbol=${encodeURIComponent("NYMEX:" + sym)}` });
        await sleep(9000);
        const title = await evalJS(sess, `document.title`);
        if (!title.toUpperCase().includes(sym)) throw new Error("symbol 加载异常: " + title.slice(0, 40));
        let r;
        try { r = await exportOnce(sess, interval); }
        catch (e) { console.log(`  retry: ${e.message.slice(0, 60)}`); await sleep(3000); r = await exportOnce(sess, interval); }
        results.push({ sym, interval, ...r });
        console.log(`[ok] ${tag}: ${r.rows} 行, ${r.last.slice(0, 11)} → ${r.file}`);
      } catch (e) {
        results.push({ sym, interval, error: e.message.slice(0, 100) });
        console.log(`[FAIL] ${tag}: ${e.message.slice(0, 100)}`);
        await sleep(2000);
      }
    }
  }
  const okCount = results.filter(r => !r.error).length;
  console.log(`\n[summary] ${okCount}/${results.length} 成功`);
  results.forEach(r => {
    if (r.error) console.log(`  FAIL ${r.sym}·${r.interval}: ${r.error}`);
    else console.log(`  OK ${r.sym}·${r.interval}: ${r.rows}行 ${r.first.slice(0, 11)} → ${r.last.slice(0, 11)}`);
  });
  fs.writeFileSync(path.join(OUT_DIR, "_batch_report.json"), JSON.stringify(results, null, 2));
  sess.close();
  process.exit(0);
})().catch(e => { console.error("FATAL:", e.message); process.exit(1); });