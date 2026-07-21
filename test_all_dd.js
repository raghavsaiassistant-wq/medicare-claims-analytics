
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
  const targets = await fetchJson('http://localhost:9227/json');
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
    r = await send('Runtime.evaluate', { expression: "state.loaded + ' | buttons: ' + document.querySelectorAll('.filter-dd-btn').length" });
    console.log(r.result?.value);

    // For each of 7 dropdowns, open it, click All, verify count > 0
    const dims = ['payers', 'age_bands', 'encounter_classes', 'genders', 'cities', 'years', 'specialties'];
    for (const dim of dims) {
      // Open dropdown
      await send('Runtime.evaluate', { expression: `document.querySelector('#dd-btn-${dim}').click()` });
      await new Promise(r => setTimeout(r, 200));
      
      // Check if menu is visible
      r = await send('Runtime.evaluate', { expression: `document.querySelector('#dd-menu-${dim}').classList.contains('show')` });
      const visible = r.result?.value;
      
      // Get values count
      r = await send('Runtime.evaluate', { expression: `RAW.filters.${dim}.length` });
      const total = r.result?.value;
      
      // Click All
      await send('Runtime.evaluate', { expression: `document.querySelectorAll('#dd-menu-${dim} .dd-actions button')[0].click()` });
      await new Promise(r => setTimeout(r, 300));
      
      // Check filter applied
      r = await send('Runtime.evaluate', { expression: `state.filters.${dim}.size` });
      const active = r.result?.value;
      
      console.log(`  ${dim.padEnd(20)} open=${visible}  total=${total}  after All=${active}  ${active > 0 ? '✓' : '✗'}`);
      
      // Click None to reset for next test
      await send('Runtime.evaluate', { expression: `document.querySelectorAll('#dd-menu-${dim} .dd-actions button')[1].click()` });
      await new Promise(r => setTimeout(r, 200));
    }
    
    // Also test: single checkbox click
    await send('Runtime.evaluate', { expression: "document.querySelector('#dd-btn-payers').click()" });
    await new Promise(r => setTimeout(r, 300));
    await send('Runtime.evaluate', { expression: "document.querySelectorAll('#dd-menu-payers input[type=checkbox]')[0].click()" });
    await new Promise(r => setTimeout(r, 500));
    r = await send('Runtime.evaluate', { expression: "[...state.filters.payers].join(',')" });
    console.log(`  Single checkbox click: ${r.result?.value}`);

    ws.close();
    process.exit(0);
  });
  ws.on('error', e => { console.error('WS err:', e.message); process.exit(1); });
}
main().catch(e => { console.error('Main err:', e); process.exit(1); });
