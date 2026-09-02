const fs = require('fs');
const s = fs.readFileSync('Temp/ccl_fetch/check_62.js', 'utf8');
const st = s.indexOf('(function(){');
const end = s.indexOf('})();') + 5;
const px = s.slice(st, end);
fs.writeFileSync('Temp/ccl_fetch/px_iife.js', px);

function bal(code) {
  let a = 0, b = 0, c = 0, inStr = null;
  for (let i = 0; i < code.length; i++) {
    const ch = code[i];
    if (inStr) { if (ch === inStr && code[i-1] !== '\\') inStr = null; continue; }
    if (ch === '"' || ch === "'") { inStr = ch; continue; }
    if (ch === '{') a++; if (ch === '}') a--;
    if (ch === '(') b++; if (ch === ')') b--;
    if (ch === '[') c++; if (ch === ']') c--;
  }
  return { a, b, c };
}
console.log('ch_px block bal:', bal(px));
const lines = px.split('\n');
for (let i = 0; i < lines.length; i++) {
  const r = bal(lines[i]);
  if (r.a !== 0 || r.b !== 0) {
    console.log('line', i + 1, JSON.stringify(lines[i].slice(0, 100)), 'brace', r.a, 'paren', r.b);
  }
}
