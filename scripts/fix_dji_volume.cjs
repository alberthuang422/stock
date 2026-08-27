// 定点修复 dji: 从干净备份重建并正确注入 volume(规避 CRLF 中段 \r 污染)
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");
const EXE = "C:/Users/Administrator/AppData/Local/Google/Chrome/Application/chrome.exe";
const CDP_URL = "http://127.0.0.1:9222";

function dateStr(tsSec){
  const d=new Date(tsSec*1000);
  return d.getUTCFullYear()+"-"+String(d.getUTCMonth()+1).padStart(2,"0")+"-"+String(d.getUTCDate()).padStart(2,"0");
}
function sleep(ms){return new Promise(r=>setTimeout(r,ms));}

async function fetchVolMap(browser){
  const url="https://query1.finance.yahoo.com/v8/finance/chart/%5EDJI?range=5y&interval=1d&events=history&includeAdjustedClose=true";
  let txt=null;
  for(let a=1;a<=3;a++){
    const page=await browser.newPage();
    try{
      await page.goto(url,{waitUntil:"domcontentloaded",timeout:60000});
      await page.waitForTimeout(4000);
      txt=await page.evaluate(()=>document.body.innerText.trim());
      if(!txt||!txt.startsWith("{")){
        await page.goto("https://finance.yahoo.com",{waitUntil:"domcontentloaded"});
        await page.waitForTimeout(2500);
        txt=await page.evaluate(async u=>(await fetch(u)).text(),url);
      }
    }catch(e){txt="ERR:"+e.message;}
    await page.close();
    if(txt&&txt.startsWith("{"))break;
    await sleep(6000*a);
  }
  const map=new Map();
  if(!txt||!txt.startsWith("{"))return map;
  let j;try{j=JSON.parse(txt);}catch(e){return map;}
  const r=j.chart&&j.chart.result&&j.chart.result[0];
  if(!r)return map;
  const ts=r.timestamp,q=r.indicators.quote[0];
  for(let i=0;i<ts.length;i++){if(q.close[i]==null)continue;map.set(dateStr(ts[i]),q.volume[i]);}
  return map;
}

(async()=>{
  let browser;
  try{ browser=await chromium.connectOverCDP(CDP_URL); console.log("CDP ok"); }
  catch(e){ browser=await chromium.launch({executablePath:EXE,args:["--no-sandbox","--headless=new"]}); }

  const bak="data/dji/dji, 1D.csv.bak";
  const out="data/dji/dji, 1D.csv";
  const raw=fs.readFileSync(bak,"utf-8").replace(/\r\n/g,"\n").replace(/\r/g,"\n");
  const lines=raw.split("\n").filter(l=>l.trim());
  const dates=[];
  const ohlc={};
  for(let i=1;i<lines.length;i++){
    const p=lines[i].split(",");
    const d=p[0].trim();
    dates.push(d);
    ohlc[d]={o:p[1],h:p[2],l:p[3],c:p[4]};
  }
  console.log("备份解析:",dates.length,"行,",dates[0],"~",dates[dates.length-1]);

  const volMap=await fetchVolMap(browser);
  console.log("Yahoo volume 点数:",volMap.size);

  const out_lines=["date,open,high,low,close,volume"];
  let filled=0,missing=0;
  for(const d of dates){
    const v=volMap.has(d)?volMap.get(d):"";
    const r=ohlc[d];
    out_lines.push([d,r.o,r.h,r.l,r.c,v].join(","));
    if(v!==""&&v!=null)filled++;else missing++;
  }
  fs.writeFileSync(out,out_lines.join("\n")+"\n");
  await browser.close();
  console.log("已重写 dji, 1D.csv: 填充 volume",filled,"行, 缺失",missing,"行");
})().catch(e=>{console.error("FATAL:",e);process.exit(1);});
