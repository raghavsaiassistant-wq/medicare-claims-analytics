
const https = require('https');
const pako = require('pako');

function fetchGz(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    }).on('error', reject);
  });
}

async function main() {
  console.log("Testing pako.ungzip on real gz file...");
  const url = 'https://raghavsaiassistant-wq.github.io/medicare-claims-analytics/data/fact_med.json.gz';
  const buf = await fetchGz(url);
  console.log(`Downloaded: ${buf.length} bytes`);

  try {
    // Method 1: pako.ungzip with {to: 'string'}
    const text1 = pako.ungzip(new Uint8Array(buf), { to: 'string' });
    console.log(`Method 1 (string): OK, ${text1.length} chars, first 80: ${text1.slice(0, 80)}`);
  } catch (e) {
    console.log(`Method 1 FAILED: ${e.message}`);
  }

  try {
    // Method 2: pako.ungzip returning Uint8Array
    const arr = pako.ungzip(new Uint8Array(buf));
    console.log(`Method 2 (Uint8Array): OK, ${arr.length} bytes, first 20 hex: ${Array.from(arr.slice(0, 20)).map(b => b.toString(16).padStart(2, '0')).join(' ')}`);
    const text = new TextDecoder().decode(arr);
    console.log(`  Decoded: ${text.length} chars, first 80: ${text.slice(0, 80)}`);
  } catch (e) {
    console.log(`Method 2 FAILED: ${e.message}`);
  }

  try {
    // Method 3: Use zlib (built-in) like the browser
    const zlib = require('zlib');
    const text = zlib.gunzipSync(buf).toString();
    console.log(`Method 3 (zlib): OK, ${text.length} chars, first 80: ${text.slice(0, 80)}`);
  } catch (e) {
    console.log(`Method 3 FAILED: ${e.message}`);
  }
}

main().catch(e => console.error("MAIN ERR:", e));
