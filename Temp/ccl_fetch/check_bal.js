const fs = require('fs');
const s = fs.readFileSync('Temp/ccl_fetch/check_62.js', 'utf8');
let depth = 0, inStr = null, line = 1;
for (let i = 0; i < s.length; i++) {
  const c = s[i];
  if (c === '\n') line++;
  if (inStr) { if (c === inStr && s[i-1] !== '\\') inStr = null; continue; }
  if (c === '"' || c === "'") { inStr = c; continue; }
  if (c === '{') depth++;
  if (c === '}') { depth--; if (depth < 0) { console.log('NEG brace at line', line, 'char', i); break; } }
}
console.log('final brace depth:', depth);

let d2 = 0; line = 1; inStr = null;
for (let i = 0; i < s.length; i++) {
  const c = s[i];
  if (c === '\n') line++;
  if (inStr) { if (c === inStr && s[i-1] !== '\\') inStr = null; continue; }
  if (c === '"' || c === "'") { inStr = c; continue; }
  if (c === '(') d2++;
  if (c === ')') { d2--; if (d2 < 0) { console.log('NEG paren at line', line, 'char', i); break; } }
}
console.log('final paren depth:', d2);
