// 厄尔尼诺 × 小麦产量：PSD 数据提取（澳/印/美/俄/乌/阿根廷/欧盟/加拿大 + 全球主产国合计）
// attributeId: 28=Production, 178=Area Harvested, 84=Yield
const fs = require('fs');
const DIR = 'C:/Users/Administrator/Desktop/stock/Temp/psd';
const YEARS = Array.from({length: 27}, (_, i) => 2000 + i);

const CC = { AS:'澳大利亚', IN:'印度', US:'美国', RS:'俄罗斯', UP:'乌克兰', AR:'阿根廷', CA:'加拿大', E4:'欧盟' };

// NOAA CPC 官方 El Niño 事件（起始年），起始年 Y → 影响澳麦 MY Y（南半球 4-6 月种植、10-12 月收获）
const ELNINO_START = { 2002:'中-强', 2004:'弱', 2006:'中等', 2009:'中等', 2015:'超强', 2018:'弱', 2023:'强' };

// 读数
function read(crop){
  const out = {}; // out[year][cc][attr] = value
  for (const y of YEARS){
    const d = JSON.parse(fs.readFileSync(`${DIR}/${crop}_${y}.json`,'utf8'));
    for (const r of d){
      if (!CC[r.countryCode]) continue;
      (out[r.marketYear] ??= {})[r.countryCode] ??= {};
      out[r.marketYear][r.countryCode][r.attributeId] = r.value;
    }
  }
  return out;
}
const w = read('wheat');

// 澳麦产量表
console.log('=== 澳大利亚小麦产量（Mt，PSD MY=收获起始年）===');
console.log('MY | 产量 | 面积(ha,百万) | 单产(t/ha) | 厄尔尼诺');
const ausRows = [];
for (const y of YEARS){
  const r = w[y]?.AS || {};
  const prod=(r[28]||0)/1000, area=(r[178]||0)/1e6, yld=(r[84]||0)/1000;
  ausRows.push({y, prod});
  console.log(`${y} | ${prod.toFixed(1)} | ${area.toFixed(2)} | ${yld.toFixed(2)} | ${ELNINO_START[y]?'EN-'+ELNINO_START[y]:''}`);
}

// 事件响应：事件年 vs 前5年均值
console.log('\n=== 澳麦事件响应：EN 年 vs 前5年均值（Mt）===');
for (const y of Object.keys(ELNINO_START).map(Number)){
  const prev = ausRows.filter(r=>r.y>=y-5&&r.y<=y-1).map(r=>r.prod);
  const m = prev.reduce((a,b)=>a+b,0)/prev.length;
  const cur = ausRows.find(r=>r.y===y).prod;
  const next = ausRows.find(r=>r.y===y+1);
  console.log(`EN${y}(${ELNINO_START[y]}): MY${y} ${cur.toFixed(1)} vs 前5均 ${m.toFixed(1)} = ${((cur/m-1)*100).toFixed(0)}%${next?` | 次年${next.prod.toFixed(1)}(${((next.prod/cur-1)*100).toFixed(0)}%)`:''}`);
}

// 对照组：非 EN 年 vs 前5均
const nonEn = ausRows.filter(r=>r.y>=2005&&r.y<=2025&&!ELNINO_START[r.y]).map(r=>{
  const prev = ausRows.filter(q=>q.y>=r.y-5&&q.y<=r.y-1).map(q=>q.prod);
  return r.prod/(prev.reduce((a,b)=>a+b,0)/prev.length)-1;
});
const enDev = Object.keys(ELNINO_START).map(Number).map(y=>{
  const prev = ausRows.filter(q=>q.y>=y-5&&q.y<=y-1).map(q=>q.prod);
  return ausRows.find(r=>r.y===y).prod/(prev.reduce((a,b)=>a+b,0)/prev.length)-1;
});
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
console.log(`\nEN 年偏离均值 ${ (mean(enDev)*100).toFixed(0) }%（n=${enDev.length}）| 非 EN 年 ${ (mean(nonEn)*100).toFixed(0) }%（n=${nonEn.length}）| 全期均值 ${ (mean(ausRows.filter(r=>r.y>=2005&&r.y<=2025).map(r=>r.prod))*1).toFixed(1) } Mt`);

// 印度小麦（厄尔尼诺→季风弱→秋播土壤水差）
console.log('\n=== 印度小麦产量（Mt）===');
for (const y of YEARS){
  const r = w[y]?.IN || {};
  console.log(`${y}: ${((r[28]||0)/1000).toFixed(1)}${ELNINO_START[y]?' | EN-'+ELNINO_START[y]:''}`);
}

// 俄乌美的 EN 年对照（检验"厄尔尼诺对 CIS/北美小麦无一致信号"）
console.log('\n=== EN 年 俄/乌/美 产量 vs 前5均 ===');
for (const y of Object.keys(ELNINO_START).map(Number)){
  const line=[`EN${y}:`];
  for (const cc of ['RS','UP','US']){
    const prev=[],prevY=[];
    for(let k=y-5;k<y;k++){ const r=w[k]?.[cc]||{}; prev.push((r[28]||NaN)/1000); }
    const cur=(w[y]?.[cc]?.[28]||NaN)/1000;
    const m=prev.filter(v=>!isNaN(v));
    if(m.length===5&&!isNaN(cur)) line.push(`${CC[cc]} ${cur.toFixed(1)}(${((cur/mean(m)-1)*100).toFixed(0)}%)`);
  }
  console.log(line.join(' '));
}
