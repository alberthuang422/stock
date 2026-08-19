// 拉 Yahoo quoteSummary 估值快照（SBUX）
const { chromium } = require("playwright-core");
const fs = require("fs");
const path = require("path");

(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const page = await browser.newPage();
  const url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/SBUX?modules=defaultKeyStatistics,financialData,summaryDetail,earnings";
  let txt = null;
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(4000);
    txt = await page.evaluate(() => document.body.innerText.trim());
  } catch (e) { console.error("goto err:", e.message); }
  if (!txt || !txt.startsWith("{")) {
    const p2 = await browser.newPage();
    await p2.goto("https://finance.yahoo.com", { waitUntil: "domcontentloaded", timeout: 45000 });
    await p2.waitForTimeout(3000);
    txt = await p2.evaluate(async (u) => { const r = await fetch(u); return await r.text(); }, url);
    await p2.close();
  }
  await page.close();
  if (!txt) { console.error("no data"); await browser.close(); process.exit(1); }
  let j; try { j = JSON.parse(txt); } catch (e) { console.error("not json:", txt.slice(0,300)); await browser.close(); process.exit(1); }
  const r = j.quoteSummary && j.quoteSummary.result && j.quoteSummary.result[0];
  if (!r) { console.error("no result"); await browser.close(); process.exit(1); }
  const pick = (o) => o ? (o.raw ?? o.fmt ?? null) : null;
  const out = {
    price: pick(r.summaryDetail && r.summaryDetail.regularMarketPrice),
    trailingPE: pick(r.summaryDetail && r.summaryDetail.trailingPE),
    forwardPE: pick(r.summaryDetail && r.summaryDetail.forwardPE),
    marketCap: pick(r.summaryDetail && r.summaryDetail.marketCap),
    fiftyTwoWeekHigh: pick(r.summaryDetail && r.summaryDetail.fiftyTwoWeekHigh),
    fiftyTwoWeekLow: pick(r.summaryDetail && r.summaryDetail.fiftyTwoWeekLow),
    dividendYield: pick(r.summaryDetail && r.summaryDetail.dividendYield),
    beta: pick(r.summaryDetail && r.summaryDetail.beta),
    trailingEps: pick(r.defaultKeyStatistics && r.defaultKeyStatistics.trailingEps),
    forwardEps: pick(r.defaultKeyStatistics && r.defaultKeyStatistics.forwardEps),
    pegRatio: pick(r.defaultKeyStatistics && r.defaultKeyStatistics.pegRatio),
    priceToBook: pick(r.defaultKeyStatistics && r.defaultKeyStatistics.priceToBook),
    totalCash: pick(r.financialData && r.financialData.totalCash),
    totalDebt: pick(r.financialData && r.financialData.totalDebt),
    ebitda: pick(r.financialData && r.financialData.ebitda),
    revenue: pick(r.financialData && r.financialData.totalRevenue),
    grossMargins: pick(r.financialData && r.financialData.grossMargins),
    operatingMargins: pick(r.financialData && r.financialData.operatingMargins),
    profitMargins: pick(r.financialData && r.financialData.profitMargins),
    freeCashflow: pick(r.financialData && r.financialData.freeCashflow),
    returnOnEquity: pick(r.financialData && r.financialData.returnOnEquity),
  };
  // earnings 简况
  const e = r.earnings;
  if (e && e.financialsChart && e.financialsChart.yearly) {
    out.yearlyEps = e.financialsChart.yearly.map(y => ({ yr: y.fiscalDate.slice(0,4), eps: y.earnings.raw }));
  }
  if (e && e.financialsChart && e.financialsChart.quarterly) {
    out.quarterlyEps = e.financialsChart.quarterly.slice(-8).map(q => ({ date: q.date, eps: q.earnings.raw }));
  }
  console.log(JSON.stringify(out, null, 2));
  fs.writeFileSync("/Users/alberthuang/Desktop/股票分析/results/sbux_valuation.json", JSON.stringify(out, null, 2));
  await browser.close();
})().catch(e => { console.error("FATAL:", e); process.exit(1); });
