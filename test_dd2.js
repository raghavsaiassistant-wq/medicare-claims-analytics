
const http = require('http');
const WebSocket = require('ws');
async function fetchJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (res) => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => resolve(JSON.parse(body)));
    }).on('error', reject);
  });
}
async function main() {
  const targets = await fetchJson('http://localhost:9225/json');
  const page = targets.find(t => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.on('open', async () => {
    function send(method, params) {
      return new Promise((resolve) => {
        const myId = ++id;
        pending.set(myId, resolve);
        ws.send(JSON.stringify({id: myId, method, params}));
      });
    }
    ws.on('message', (data) => {
      const m = JSON.parse(data);
      if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); }
    });
    await new Promise(r => setTimeout(r, 8000));

    let r;
    r = await send('Runtime.evaluate', { expression: "typeof state !== 'undefined' ? state.loaded : 'undef'" });
    console.log('1. state.loaded:', r.result?.value);

    r = await send('Runtime.evaluate', { expression: "document.querySelectorAll('.filter-dd-btn').length" });
    console.log('2. Filter buttons:', r.result?.value);

    r = await send('Runtime.evaluate', { expression: "document.querySelectorAll('.filter-dd-menu').length" });
    console.log('3. Dropdown menus:', r.result?.value);

    r = await send('Runtime.evaluate', { expression: "RAW.filters.payers.length" });
    console.log('4. RAW.filters.payers:', r.result?.value);

    // Check if dropdown is positioned correctly
    r = await send('Runtime.evaluate', { expression: "(() => { const m = document.querySelector('#dd-menu-payers'); if (!m) return 'no menu'; const cs = getComputedStyle(m); return {display: cs.display, position: cs.position, top: cs.top, left: cs.left, zIndex: cs.zIndex, visibility: cs.visibility}; })()" });
    console.log('5. Payer menu computed style:', JSON.stringify(r.result?.value));

    // Click and check
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-btn-payers').click(); 'ok'" });
    await new Promise(r => setTimeout(r, 500));
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-menu-payers').classList.contains('show')" });
    console.log('6. Payer dropdown visible after click:', r.result?.value);

    // Now click an All button via dispatchEvent
    r = await send('Runtime.evaluate', { expression: "(() => { const b = document.querySelectorAll('#dd-menu-payers .dd-actions button')[0]; b.dispatchEvent(new MouseEvent('click', {bubbles: true})); return 'dispatched'; })()" });
    await new Promise(r => setTimeout(r, 500));
    r = await send('Runtime.evaluate', { expression: "state.filters.payers.size" });
    console.log('7. payers selected after All dispatch:', r.result?.value);

    ws.close();
    process.exit(0);
  });
  ws.on('error', e => { console.error('WS err:', e.message); process.exit(1); });
}
main().catch(e => { console.error('Main err:', e); process.exit(1); });
