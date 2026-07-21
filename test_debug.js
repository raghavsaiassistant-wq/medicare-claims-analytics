
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
  const targets = await fetchJson('http://localhost:9226/json');
  const page = targets.find(t => t.type === 'page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  const consoleLogs = [];
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
      if (m.method === 'Runtime.consoleAPICalled') {
        consoleLogs.push(`[${m.params.type}] ${m.params.args.map(a => a.value).join(' ')}`);
      }
      if (m.method === 'Runtime.exceptionThrown') {
        consoleLogs.push(`[EXCEPTION] ${m.params.exceptionDetails.text} ${m.params.exceptionDetails.exception?.description || ''}`);
      }
    });

    // Enable console
    await send('Runtime.enable', {});
    await send('Page.enable', {});

    await new Promise(r => setTimeout(r, 10000));  // wait longer

    let r;
    r = await send('Runtime.evaluate', { expression: "state ? state.loaded : 'no state'" });
    console.log('state.loaded:', r.result?.value);

    console.log('\n--- CONSOLE LOGS ---');
    consoleLogs.forEach(l => console.log(l));

    ws.close();
    process.exit(0);
  });
  ws.on('error', e => { console.error('WS err:', e.message); process.exit(1); });
}
main().catch(e => { console.error('Main err:', e); process.exit(1); });
