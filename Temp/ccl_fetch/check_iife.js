const fs = require('fs');
const s = fs.readFileSync('Temp/ccl_fetch/check_62.js', 'utf8');
// 找到所有 IIFE 边界并逐个尝试编译
const blocks = [];
let idx = 0;
while (true) {
  const st = s.indexOf('(function(){', idx);
  if (st < 0) break;
  let depth = 0, i = st, inStr = null;
  for (; i < s.length; i++) {
    const c = s[i];
    if (inStr) { if (c === inStr && s[i-1] !== '\\') inStr = null; continue; }
    if (c === '"' || c === "'") { inStr = c; continue; }
    if (c === '(') depth++;
    if (c === ')') depth--;
    if (depth === 0) break;
  }
  blocks.push({ st, end: i });
  idx = i + 1;
}
console.log('IIFE count:', blocks.length);
for (let j = 0; j < blocks.length; j++) {
  const b = blocks[j];
  const code = s.slice(b.st, b.end + 1);
  try { new Function(code); console.log(j, 'OK at', b.st); }
  catch (e) { console.log(j, 'FAIL at', b.st, '->', e.message); }
}
