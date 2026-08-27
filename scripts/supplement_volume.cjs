// 给 data/ 下所有股票 CSV 补充成交量(volume)
// 逻辑:
//   - 缺 volume 列的 OHLCV 文件: 拉全量日线(分块防降采样), 仅注入 volume 列
//   - 有 volume 但陈旧的: 拉 last_date -> now 增量, 追加新行(带 volume)
//   - 已含 volume 且最新的: 跳过
// 复用本机 Chrome CDP(9222), 失败回退自启 headless Chrome。
// 用法: node supplement_volume.cjs [--dry] [--delay 1.0]

const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

const EXE = "C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe";
const DATA_ROOT = path.resolve(__dirname, "../data");
const CDP_URL = "http://127.0.0.1:9222";

const args = process.argv.slice(2);
const DRY = args.includes("--dry");
const delayArg = args.find(a => a.startsWith("--delay"));
const BASE_DELAY = delayArg ? parseFloat(delayArg.split("=")[1]) : 1.0;

// ---- ticker 映射 ----
function toYahoo(prefix){
  let p = prefix.trim();
  if (p.startsWith("BATS_")) p = p.slice(5);
  const pl = p.toLowerCase();
  const idx = {"dji":"^DJI","vix":"^VIX","gspc":"^GSPC","ixic":"^IXIC","rut":"^RUT"};
  if (idx[pl]) return idx[pl];
  if (pl.endsWith(".hk")) return p.slice(0,-3)+".HK";
  if (pl.endsWith(".ss")) return p.slice(0,-3)+".SS";
  if (pl.endsWith(".sz")) return p.slice(0,-3)+".SZ";
  if (pl==="brk.b"||pl==="brk-b") return "BRK-B";
  if (p.includes(".")) return p.replace(/\./g,"-").toUpperCase();
  return p.toUpperCase();
}

function dateStr(tsSec){
  const d = new Date(tsSec*1000);
  return d.getUTCFullYear()+"-"+String(d.getUTCMonth()+1).padStart(2,"0")+"-"+String(d.getUTCDate()).padStart(2,"0");
}

// 拉取 [p1,p2] 区间, interval 可为 1d/1wk, 返回 rows: {date,o,h,l,c,v,adj}
async function fetchRange(browser, ticker, p1, p2, interval){
  const iv = interval || "1d";
  const enc = encodeURIComponent(ticker);
  const url = "https://query1.finance.yahoo.com/v8/finance/chart/"+enc+
    "?period1="+Math.floor(p1/1000)+"&period2="+Math.floor(p2/1000)+
    "&interval="+iv+"&events=history&includeAdjustedClose=true";
  const page = await browser.newPage();
  let txt = null;
  try{
    await page.goto(url,{waitUntil:"domcontentloaded",timeout:60000});
    await page.waitForTimeout(3500);
    txt = await page.evaluate(()=>document.body.innerText.trim());
    if(!txt||!txt.startsWith("{")){
      await page.goto("https://finance.yahoo.com",{waitUntil:"domcontentloaded"});
      await page.waitForTimeout(2500);
      txt = await page.evaluate(async u=>(await fetch(u)).text(), url);
    }
  }catch(e){ txt="ERR:"+e.message; }
  await page.close();
  if(!txt||!txt.startsWith("{")) return null;
  let j;
  try{ j = JSON.parse(txt); }catch(e){ return null; }
  const r = j.chart && j.chart.result && j.chart.result[0];
  if(!r) return null;
  const ts = r.timestamp, q = r.indicators.quote[0];
  const adj = (r.indicators.adjclose && r.indicators.adjclose[0]) ? r.indicators.adjclose[0].adjclose : [];
  const rows = [];
  for(let i=0;i<ts.length;i++){
    if(q.close[i]==null) continue;
    rows.push({date:dateStr(ts[i]), o:q.open[i], h:q.high[i], l:q.low[i], c:q.close[i], v:q.volume[i], adj: adj[i]!=null?adj[i]:q.close[i]});
  }
  return rows;
}

async function fetchWithRetry(browser, ticker, p1, p2){
  for(let attempt=1; attempt<=3; attempt++){
    const rows = await fetchRange(browser, ticker, p1, p2);
    if(rows && rows.length) return rows;
    console.error("    [重试 "+attempt+"/3] "+ticker+" 区间无数据, 冷却中...");
    await sleep(6000*attempt);
  }
  return null;
}

// 全量日线(用 range=5y 单请求, 避免指数长历史被拆成多块), 返回 Map date->row
async function fetchFull(browser, ticker){
  const enc = encodeURIComponent(ticker);
  const url = "https://query1.finance.yahoo.com/v8/finance/chart/"+enc+
    "?range=5y&interval=1d&events=history&includeAdjustedClose=true";
  let txt = null;
  for(let attempt=1; attempt<=3; attempt++){
    const page = await browser.newPage();
    try{
      await page.goto(url,{waitUntil:"domcontentloaded",timeout:60000});
      await page.waitForTimeout(4000);
      txt = await page.evaluate(()=>document.body.innerText.trim());
      if(!txt||!txt.startsWith("{")){
        await page.goto("https://finance.yahoo.com",{waitUntil:"domcontentloaded"});
        await page.waitForTimeout(2500);
        txt = await page.evaluate(async u=>(await fetch(u)).text(), url);
      }
    }catch(e){ txt="ERR:"+e.message; }
    await page.close();
    if(txt && txt.startsWith("{")) break;
    await sleep(6000*attempt);
  }
  const map = new Map();
  if(!txt||!txt.startsWith("{")) return map;
  let j; try{ j=JSON.parse(txt); }catch(e){ return map; }
  const r = j.chart && j.chart.result && j.chart.result[0];
  if(!r) return map;
  const ts=r.timestamp, q=r.indicators.quote[0];
  for(let i=0;i<ts.length;i++){
    if(q.close[i]==null) continue;
    map.set(dateStr(ts[i]), {v:q.volume[i]});
  }
  return map;
}

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

// ---- 扫描目标文件 ----
function findTargets(){
  const out = [];
  const walk = (dir) => {
    for(const e of fs.readdirSync(dir, {withFileTypes:true})){
      const fp = path.join(dir, e.name);
      if(e.isDirectory()){ walk(fp); continue; }
      if(!e.name.toLowerCase().endsWith(".csv")) continue;
      const raw = fs.readFileSync(fp, "utf-8");
      const firstLine = raw.split("\n",1)[0].trim();
      const cols = firstLine.split(",").map(c=>c.trim().toLowerCase());
      const hasOHLC = ["date","open","high","low","close"].every(c=>cols.includes(c));
      if(!hasOHLC) continue;
      const hasVol = cols.includes("volume");
      const hasAdj = cols.includes("adj_close");
      // last date
      const lines = raw.split("\n").filter(l=>l.trim());
      let lastDate = null;
      for(let i=lines.length-1;i>=1;i--){
        const d = lines[i].split(",")[0].trim();
        if(/^\d{4}-\d{2}-\d{2}$/.test(d)){ lastDate = d; break; }
      }
      const m = e.name.match(/^(.*?),\s/);
      const prefix = m ? m[1].trim() : path.basename(e.name, ".csv");
      const isWeekly = /,\s*(1W|W)\b/i.test(e.name);
      const interval = isWeekly ? "1wk" : "1d";
      out.push({fp, prefix, ticker:toYahoo(prefix), hasVol, hasAdj, lastDate, header:firstLine, interval});
    }
  };
  walk(DATA_ROOT);
  return out;
}

function isCurrent(lastDate){
  if(!lastDate) return false;
  const today = new Date();
  const cutoff = new Date(today.getFullYear(), today.getMonth(), today.getDate()-1); // 今天或昨天视为最新
  const cd = cutoff.toISOString().slice(0,10);
  return lastDate >= cd; // YYYY-MM-DD 字符串比较
}

// ---- 主流程 ----
(async()=>{
  const targets = findTargets();
  const needAction = [];
  for(const t of targets){
    if(!t.hasVol){ needAction.push({...t, action:"ADD_COLUMN"}); }
    else if(!isCurrent(t.lastDate)){ needAction.push({...t, action:"APPEND"}); }
  }
  const skipCount = targets.length - needAction.length;
  console.log("扫描 OHLCV 文件:", targets.length, " | 需处理:", needAction.length, " | 跳过(已最新):", skipCount);
  if(DRY){
    console.log("\n[DRY] 计划处理文件:");
    for(const t of needAction) console.log("  ["+t.action+"] "+t.fp+"  ticker="+t.ticker+"  last="+t.lastDate);
    return;
  }

  // 浏览器: 优先 CDP, 回退自启
  let browser;
  try{
    browser = await chromium.connectOverCDP(CDP_URL);
    console.log("已连接 CDP:", CDP_URL);
  }catch(e){
    console.log("CDP 不可用, 自启 headless Chrome ...");
    browser = await chromium.launch({executablePath:EXE, args:["--no-sandbox","--headless=new"]});
  }

  let ok=0, fail=0, addedRows=0, addedCols=0;
  const failed=[];
  for(const t of needAction){
    console.log("\n["+t.action+"] "+t.fp+"  ("+t.ticker+", last="+t.lastDate+")");
    try{
      const raw = fs.readFileSync(t.fp, "utf-8").replace(/\r\n/g,"\n").replace(/\r/g,"\n");
      const lines = raw.split("\n").filter(l=>l.length);
      const header = lines[0];
      const cols = header.split(",").map(c=>c.trim().toLowerCase());
      const di = cols.indexOf("date");
      const existing = new Map(); // date -> line
      const dates = [];
      for(let i=1;i<lines.length;i++){
        const parts = lines[i].split(",");
        const d = parts[di].trim();
        existing.set(d, lines[i]);
        dates.push(d);
      }
      const firstDate = dates[0];
      const lastDate = dates[dates.length-1];

      if(t.action==="ADD_COLUMN"){
        // 全量拉 volume, 注入新列
        const map = await fetchFull(browser, t.ticker);
        let filled=0, missing=0;
        const newLines = [header+",volume"];
        for(const d of dates){
          const rw = map.get(d);
          const v = (rw && rw.v!=null) ? rw.v : "";
          newLines.push(existing.get(d)+","+v);
          if(rw && rw.v!=null) filled++; else missing++;
        }
        fs.writeFileSync(t.fp, newLines.join("\n")+"\n");
        addedCols++;
        console.log("    已补 volume 列: 填充 "+filled+" 行, 缺失 "+missing+" 行");
        ok++;
      } else { // APPEND
        const back = t.interval==="1wk" ? 14*86400000 : 2*86400000;
        const mapRows = await fetchWithRetry(browser, t.ticker, new Date(new Date(lastDate+"T00:00:00Z").getTime()-back), new Date(), t.interval);
        if(!mapRows){ failed.push(t.fp); fail++; console.log("    拉取失败, 跳过"); await sleep(BASE_DELAY*1000); continue; }
        const newRows = mapRows.filter(r=>r.date > lastDate);
        if(newRows.length===0){ console.log("    无新增行(已最新)"); ok++; await sleep(BASE_DELAY*1000); continue; }
        const out = lines.slice();
        for(const rw of newRows){
          if(t.hasAdj) out.push([rw.date,rw.o,rw.h,rw.l,rw.c,rw.v,rw.adj].join(","));
          else out.push([rw.date,rw.o,rw.h,rw.l,rw.c,rw.v].join(","));
        }
        fs.writeFileSync(t.fp, out.join("\n")+"\n");
        addedRows += newRows.length;
        console.log("    追加 "+newRows.length+" 行 ("+newRows[0].date+" ~ "+newRows[newRows.length-1].date+")");
        ok++;
      }
    }catch(e){
      failed.push(t.fp); fail++;
      console.error("    处理异常: "+e.message);
    }
    await sleep(BASE_DELAY*1000);
  }

  await browser.close();
  console.log("\n==== 完成 ====");
  console.log("成功:", ok, " 失败:", fail, " 补列文件:", addedCols, " 追加行数:", addedRows);
  if(failed.length) console.log("失败文件:\n  "+failed.join("\n  "));
})().catch(e=>{console.error("FATAL:",e);process.exit(1);});
