const fs = require('fs');
const s = fs.readFileSync('Temp/ccl_fetch/check_62.js', 'utf8');

// 按 '})();' 分割为块
const parts = [];
let idx = 0;
while (true) {
  const m = s.indexOf('})();', idx);
  if (m < 0) break;
  parts.push(s.slice(idx, m + 5));
  idx = m + 5;
}
if (idx < s.length) parts.push(s.slice(idx));

function bal(code) {
  let a = 0, b = 0, c = 0, inStr = null;
  for (let i = 0; i < code.length; i++) {
    const ch = code[i];
    if (inStr) { if (ch === inStr && code[i-1] !== '\\') inStr = null; continue; }
    if (ch === '"' || ch === "'") { inStr = ch; continue; }
    if (ch === '{') a++;
    if (ch === '}') a--;
    if (ch === '(') b++;
    if (ch === ')') b--;
    if (ch === '[') c++;
    if (ch === ']') c--;
  }
  return { a, b, c };
}

parts.forEach((p, i) => {
  const r = bal(p);
  if (r.a !== 0 || r.b !== 0 || r.c !== 0) {
    console.log('BLOCK', i, 'len', p.length, 'braces', r.a, 'parens', r.b, 'brackets', r.c);
    // 打印块开头 300 字符
    console.log('  head:', p.slice(0, 220).replace(/\n/g, '\\n'));
  } else {
    console.log('BLOCK', i, 'OK len', p.length);
  }
});
