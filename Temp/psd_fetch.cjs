// PSD 全历史拉取：3 作物 × marketYear 2000..2026 × country/all
// 用法: USDA_FAS_API_KEY=xxx node Temp/psd_fetch.cjs
const fs = require('fs');
const path = require('path');

const KEY = process.env.USDA_FAS_API_KEY;
if (!KEY) { console.error('no key'); process.exit(1); }

const OUT = path.join(__dirname, 'psd');
fs.mkdirSync(OUT, { recursive: true });

const COM = [
  ['0410000', 'wheat'],
  ['0440000', 'corn'],
  ['2222000', 'soybean'],
];
const YEARS = [];
for (let y = 2000; y <= 2026; y++) YEARS.push(y);

const jobs = [];
for (const [code, name] of COM) {
  for (const y of YEARS) {
    const f = path.join(OUT, `${name}_${y}.json`);
    if (!fs.existsSync(f) || fs.statSync(f).size < 1000) {
      jobs.push({ code, name, y, f });
    }
  }
}
console.log('jobs to fetch:', jobs.length);

let idx = 0;
const CONC = 4;
async function worker() {
  while (true) {
    const j = jobs[idx++];
    if (!j) return;
    for (let attempt = 1; attempt <= 4; attempt++) {
      try {
        const r = await fetch(`https://api.fas.usda.gov/api/psd/commodity/${j.code}/country/all/year/${j.y}`, {
          headers: { 'X-Api-Key': KEY },
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const txt = await r.text();
        fs.writeFileSync(j.f, txt);
        console.log('ok', j.name, j.y, txt.length);
        break;
      } catch (e) {
        if (attempt === 4) { console.error('FAIL', j.name, j.y, e.message); }
        else await new Promise(res => setTimeout(res, 800 * attempt));
      }
    }
    await new Promise(res => setTimeout(res, 120));
  }
}
Promise.all(Array.from({ length: CONC }, worker)).then(() => {
  console.log('DONE. files:', fs.readdirSync(OUT).length);
});
