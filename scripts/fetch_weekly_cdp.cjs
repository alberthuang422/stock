// 原生 CDP 拉取 Yahoo 周线（interval=1wk），写入 data/<folder>/<stem>, W.csv
// 复权口径：close 用 adjclose；open/high/low 按 ratio=adjclose/close 调整（与仓库已有 W.csv 一致）
// 失败（解析/限流）不覆盖已有文件。 用法：node fetch_weekly_cdp.cjs [test AAPL,MSFT]
const fs = require("fs");
const path = require("path");

const OUT_ROOT = path.resolve(__dirname, "../data");
const CDP = "http://localhost:9222";
const sleep = ms => new Promise(r => setTimeout(r, ms));

function toYahoo(folder) {
  const f = folder.toLowerCase();
  if (/^\d+\.hk$/.test(f)) return f.replace(".hk", ".HK");
  if (/^\d+\.ss$/.test(f)) return f.replace(".ss", ".SS");
  if (f === "brk.b") return "BRK-B";
  if (f === "dji") return "^DJI";
  if (f === "vix") return "^VIX";
  return folder.toUpperCase();
}

function buildJobs() {
  const dirs = fs.readdirSync(OUT_ROOT, { withFileTypes: true }).filter(d => d.isDirectory());
  const jobs = [];
  for (const d of dirs) {
    const folder = d.name;
    const files = fs.readdirSync(path.join(OUT_ROOT, folder));
    const daily = files.find(f => f.endsWith(", 1D.csv") && !f.startsWith("BATS_"));
    if (!daily) continue;
    const stem = daily.slice(0, -", 1D.csv".length);
    jobs.push({ folder, symbol: toYahoo(folder), outPath: path.join(OUT_ROOT, folder, stem + ", W.csv") });
  }
  return jobs;
}

async function cdpSession(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let idc = 0;
  const pending = new Map();
  const openP = new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws open error")); });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => {
    const id = ++idc; pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params }));
  });
  return { openP, send, close: () => { try { ws.close(); } catch {} } };
}

async function fetchJson(sess, symbol) {
  const sym = encodeURIComponent(symbol);
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${sym}?range=max&interval=1wk&events=history&includeAdjustedClose=true`;
  const url2 = url.replace("query1", "query2");
  for (const u of [url, url2]) {
    try {
      await sess.send("Page.navigate", { url: "about:blank" });
      await sleep(200);
      await sess.send("Page.navigate", { url: u });
      // poll innerText until valid JSON whose meta.symbol matches (避免读到上一标的残留)
      let txt = null;
      for (let i = 0; i < 16; i++) {
        await sleep(500);
        const r = await sess.send("Runtime.evaluate", { expression: "document.body.innerText", returnByValue: true });
        const v = r && r.result && r.result.value;
        if (v && v.trim().startsWith("{")) {
          try {
            const j = JSON.parse(v);
            const ms = j && j.chart && j.chart.result && j.chart.result[0] && j.chart.result[0].meta && j.chart.result[0].meta.symbol;
            if (ms && ms.toUpperCase() === symbol.toUpperCase()) { txt = v; break; }
          } catch {}
        }
      }
      if (!txt) continue;
      return JSON.parse(txt);
    } catch (e) {
      // try next host
    }
  }
  return null;
}

function easternDate(tsSec) {
  // Yahoo 周线 timestamp 为周五收盘 epoch；转 US/Eastern 日期得到真实交易日（完整周=周五，末周不完整=最后交易日）
  return new Date(tsSec * 1000).toLocaleDateString("en-CA", { timeZone: "America/New_York" });
}

function processChart(json) {
  const res = json && json.chart && json.chart.result && json.chart.result[0];
  if (!res || !res.timestamp) return null;
  const ts = res.timestamp;
  const q = res.indicators.quote[0];
  const adjArr = (res.indicators.adjclose && res.indicators.adjclose[0]) ? res.indicators.adjclose[0].adjclose : null;
  const rows = [];
  for (let i = 0; i < ts.length; i++) {
    const c = q.close[i];
    if (c == null) continue;
    const o = q.open[i], h = q.high[i], l = q.low[i], v = q.volume[i];
    const adj = adjArr ? adjArr[i] : null;
    const ratio = (adj != null && c !== 0) ? adj / c : 1;
    rows.push([easternDate(ts[i]), o * ratio, h * ratio, l * ratio, (adj != null ? adj : c), v]);
  }
  return rows;
}

function writeWeekly(outPath, rows) {
  const header = "date,open,high,low,close,volume";
  const lines = [header, ...rows.map(r => r.map(x => (x == null ? "" : String(x))).join(","))];
  fs.writeFileSync(outPath, lines.join("\n"));
}

(async () => {
  const isTest = process.argv[2] === "test";
  let jobs = buildJobs();
  if (isTest) {
    const syms = (process.argv[3] || "AAPL").split(",");
    jobs = syms.map(s => ({ folder: s, symbol: s, outPath: null }));
  }

  // open one tab, reuse
  const resp = await fetch(`${CDP}/json/new`, { method: "PUT" });
  const target = await resp.json();
  const sess = await cdpSession(target.webSocketDebuggerUrl);
  await sess.openP;
  await sess.send("Page.enable");

  let ok = 0, fail = 0;
  const failed = [];
  for (const job of jobs) {
    const json = await fetchJson(sess, job.symbol);
    const rows = json ? processChart(json) : null;
    if (!rows || rows.length < 20) {
      fail++; failed.push(job.symbol + (rows ? `(only ${rows ? rows.length : 0} rows)` : "(no json)"));
      console.log(`FAIL ${job.symbol}`);
      await sleep(300);
      continue;
    }
    if (isTest) {
      console.log(`TEST ${job.symbol}: ${rows.length} rows, ${rows[0][0]} ~ ${rows[rows.length - 1][0]}`);
      console.log("  first:", rows[0].join(","));
      console.log("  last :", rows[rows.length - 1].join(","));
    } else {
      writeWeekly(job.outPath, rows);
      console.log(`OK   ${job.symbol} -> ${job.outPath}  (${rows.length} rows, ${rows[0][0]}~${rows[rows.length - 1][0]})`);
      ok++;
    }
    await sleep(350);
  }

  if (!isTest) {
    console.log(`\nDONE ok=${ok} fail=${fail}`);
    if (failed.length) console.log("FAILED:", failed.join(" | "));
  }
  try { await fetch(`${CDP}/json/close/${target.id}`); } catch {}
  sess.close();
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
