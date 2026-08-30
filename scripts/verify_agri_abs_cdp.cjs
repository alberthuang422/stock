// CDP 无头渲染校验：canvas 数 + pageerror + 关键 DOM
const { execSync, spawn } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const file = process.argv[2];
if (!file) { console.error("usage: node verify_cdp.cjs <file.html>"); process.exit(1); }

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "chrome-cdp-verify-"));
const chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const proc = spawn(chrome, [
  "--headless=new", "--no-sandbox", "--disable-gpu",
  `--remote-debugging-port=9333`, `--user-data-dir=${tmp}`, "about:blank",
], { stdio: "ignore" });

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

(async () => {
  try {
    await sleep(1800);
    const res = await fetch("http://localhost:9333/json");
    const tabs = await res.json();
    const page = tabs.find(t => t.type === "page");
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 0;
    const pending = {};
    const errors = [];
    const send = (method, params) => new Promise((resolve) => {
      const mid = ++id;
      pending[mid] = resolve;
      ws.send(JSON.stringify({ id: mid, method, params }));
    });
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && pending[msg.id]) { pending[msg.id](msg.result); delete pending[msg.id]; }
      if (msg.method === "Runtime.exceptionThrown") {
        const d = msg.params.exceptionDetails;
        errors.push(d.exception?.description || d.text);
      }
    };
    await new Promise(r => ws.onopen = r);
    await send("Runtime.enable");
    await send("Page.enable");
    await send("Page.navigate", { url: "file://" + path.resolve(file) });
    await sleep(4500); // 等 ECharts + CDN
    const r1 = await send("Runtime.evaluate", { expression: "document.querySelectorAll('canvas').length", returnByValue: true });
    const r2 = await send("Runtime.evaluate", { expression: "document.querySelectorAll('table').length", returnByValue: true });
    const r3 = await send("Runtime.evaluate", { expression: "document.querySelectorAll('.term').length", returnByValue: true });
    const r4 = await send("Runtime.evaluate", { expression: "document.querySelector('#det_tbl tbody').children.length", returnByValue: true });
    console.log(JSON.stringify({
      canvas: r1.result.value, tables: r2.result.value,
      termSpans: r3.result.value, detailRows: r4.result.value,
      pageErrors: errors,
    }, null, 1));
    ws.close();
  } catch (e) {
    console.error("VERIFY FAIL:", e.message);
    process.exitCode = 1;
  } finally {
    proc.kill("SIGKILL");
    try { fs.rmSync(tmp, { recursive: true, force: true }); } catch {}
  }
})();
