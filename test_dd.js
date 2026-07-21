
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
  const targets = await fetchJson('http://localhost:9224/json');
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
    await new Promise(r => setTimeout(r, 8000));  // wait for full load

    let r;
    // 1. Check what state the dashboard is in
    r = await send('Runtime.evaluate', { expression: "typeof state !== 'undefined' ? state.loaded : 'state undefined'" });
    console.log('1. state.loaded:', r.result?.value);

    r = await send('Runtime.evaluate', { expression: "document.querySelectorAll('.filter-dd-btn').length" });
    console.log('2. Filter buttons count:', r.result?.value);

    // 3. Check if dropdown actually has event listeners
    r = await send('Runtime.evaluate', { expression: "(() => { const b = document.querySelector('#dd-btn-payers'); if (!b) return 'no button'; const r = b.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height, visible: r.width > 0 && r.height > 0}; })()" });
    console.log('3. Payer button position:', JSON.stringify(r.result?.value));

    // 4. Check for any console errors
    r = await send('Runtime.evaluate', { expression: "window.__errors || 'no errors captured'" });
    console.log('4. Captured errors:', r.result?.value);

    // 5. Check if dropdown menu is in DOM at all
    r = await send('Runtime.evaluate', { expression: "document.querySelectorAll('.filter-dd-menu').length" });
    console.log('5. Dropdown menus in DOM:', r.result?.value);

    // 6. Check the actual filter-dd-btn onclick handler
    r = await send('Runtime.evaluate', { expression: "typeof buildFilterDropdowns" });
    console.log('6. buildFilterDropdowns defined:', r.result?.value);

    // 7. Force click via dispatchEvent (more reliable than .click())
    r = await send('Runtime.evaluate', { expression: "(() => { const b = document.querySelector('#dd-btn-payers'); b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true})); return 'dispatched'; })()" });
    console.log('7. Dispatched click event:', r.result?.value);

    await new Promise(r => setTimeout(r, 500));
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-menu-payers').classList.contains('show')" });
    console.log('8. Dropdown visible after dispatchEvent:', r.result?.value);

    // 9. Real .click()
    r = await send('Runtime.evaluate', { expression: "(() => { document.querySelector('#dd-btn-payers').click(); return 'clicked'; })()" });
    await new Promise(r => setTimeout(r, 500));
    r = await send('Runtime.evaluate', { expression: "document.querySelector('#dd-menu-payers').classList.contains('show')" });
    console.log('9. Dropdown visible after .click():', r.result?.value);

    // 10. Screenshot the current state
    const r10 = await send('Page.captureScreenshot', { format: 'png' });
    require('fs').writeFileSync(r"C:\Users\modir\James\projects\medicare-claims-analytics\dashboard\test_after_click.png", Buffer.from(r10.data, 'base64'));
    console.log('10. Screenshot saved');

    ws.close();
    process.exit(0);
  });
  ws.on('error', e => { console.error('WS err:', e.message); process.exit(1); });
}
main().catch(e => { console.error('Main err:', e); process.exit(1); });
