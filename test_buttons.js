
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
  const targets = await fetchJson('http://localhost:9223/json');
  const page = targets.find(t => t.type === 'page');
  if (!page) { console.log('No page'); return; }
  console.log('Page loaded:', page.url.slice(0, 80));

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
      if (m.id && pending.has(m.id)) {
        pending.get(m.id)(m.result);
        pending.delete(m.id);
      }
    });

    await new Promise(r => setTimeout(r, 6000));
    let r;
    
    // Test 1: Open Payer dropdown
    await send('Runtime.evaluate', { expression: "document.querySelector('#dd-btn-payers').click()" });
    await new Promise(r => setTimeout(r, 500));
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-menu-payers').classList.contains('show')" });
    console.log('TEST 1 - Payer dropdown opens:', r.result?.value);

    // Test 2: Click "All" button
    await send('Runtime.evaluate', { expression: "document.querySelectorAll('#dd-menu-payers .dd-actions button')[0].click()" });
    await new Promise(r => setTimeout(r, 800));
    r = await send('Runtime.evaluate', { expression: "state.filters.payers.size" });
    console.log('TEST 2 - After "All" click, payer count:', r.result?.value, '(expected: 10)');
    
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-btn-payers').classList.contains('has-active')" });
    console.log('TEST 3 - Button has has-active class:', r.result?.value, '(expected: true)');
    
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-count-payers').textContent" });
    console.log('TEST 4 - Count badge shows:', r.result?.value, '(expected: 10)');

    // Test 5: Click "None" button
    await send('Runtime.evaluate', { expression: "document.querySelectorAll('#dd-menu-payers .dd-actions button')[1].click()" });
    await new Promise(r => setTimeout(r, 800));
    r = await send('Runtime.evaluate', { expression: "state.filters.payers.size" });
    console.log('TEST 5 - After "None" click, payer count:', r.result?.value, '(expected: 0)');

    // Test 6: Click single checkbox
    await send('Runtime.evaluate', { expression: "document.querySelectorAll('#dd-menu-payers input[type=checkbox]')[0].click()" });
    await new Promise(r => setTimeout(r, 800));
    r = await send('Runtime.evaluate', { expression: "[...state.filters.payers].join(',')" });
    console.log('TEST 6 - After clicking 1st checkbox (Aetna):', r.result?.value, '(expected: Aetna)');
    
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-count-payers').textContent" });
    console.log('TEST 7 - Count badge shows:', r.result?.value, '(expected: 1)');
    
    // Test 8: Check subtitle updated
    r = await send('Runtime.evaluate', { expression: "document.getElementById('subtitle').textContent.slice(0, 80)" });
    console.log('TEST 8 - Subtitle after Aetna filter:', r.result?.value);

    // Test 9: Test Age Band
    await send('Runtime.evaluate', { expression: "document.querySelector('#dd-btn-payers').click()" });
    await new Promise(r => setTimeout(r, 300));
    await send('Runtime.evaluate', { expression: "document.querySelector('#dd-btn-age_bands').click()" });
    await new Promise(r => setTimeout(r, 500));
    await send('Runtime.evaluate', { expression: "document.querySelectorAll('#dd-menu-age_bands input[type=checkbox]')[2].click()" });
    await new Promise(r => setTimeout(r, 800));
    r = await send('Runtime.evaluate', { expression: "[...state.filters.age_bands].join(',')" });
    console.log('TEST 9 - After clicking 3rd age checkbox (35-49):', r.result?.value);

    ws.close();
    process.exit(0);
  });
  ws.on('error', (e) => { console.error('WS err:', e.message); process.exit(1); });
}
main().catch(e => { console.error('Main err:', e); process.exit(1); });
