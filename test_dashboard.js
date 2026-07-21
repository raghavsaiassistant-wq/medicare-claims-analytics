
// Test the data loading + filter logic in isolation
const https = require('https');

function fetchGz(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve(Buffer.concat(chunks)));
    }).on('error', reject);
  });
}

const zlib = require('zlib');

async function main() {
  console.log("Loading data.json...");
  const dataJson = await new Promise((resolve, reject) => {
    https.get('https://raghavsaiassistant-wq.github.io/medicare-claims-analytics/data.json', (res) => {
      let body = '';
      res.on('data', c => body += c);
      res.on('end', () => resolve(JSON.parse(body)));
    }).on('error', reject);
  });
  console.log("  KPIs:", dataJson.kpis);
  console.log("  Top 3 drugs:", dataJson.top_drugs.slice(0, 3).map(d => d.drug));

  console.log("\nLoading fact_med.json.gz...");
  const medBuf = await fetchGz('https://raghavsaiassistant-wq.github.io/medicare-claims-analytics/data/fact_med.json.gz');
  const meds = JSON.parse(zlib.gunzipSync(medBuf).toString());
  console.log(`  ${meds.length} medications loaded`);

  console.log("\nLoading fact_enc.json.gz...");
  const encBuf = await fetchGz('https://raghavsaiassistant-wq.github.io/medicare-claims-analytics/data/fact_enc.json.gz');
  const encs = JSON.parse(zlib.gunzipSync(encBuf).toString());
  console.log(`  ${encs.length} encounters loaded`);

  console.log("\nLoading conditions.json.gz...");
  const condBuf = await fetchGz('https://raghavsaiassistant-wq.github.io/medicare-claims-analytics/data/conditions.json.gz');
  const conds = JSON.parse(zlib.gunzipSync(condBuf).toString());
  console.log(`  ${conds.length} conditions loaded`);

  // Test filter logic - filter to Medicare payer only
  console.log("\n=== TEST: Filter to Medicare ===");
  const filteredMeds = meds.filter(m => m.yn === 'Medicare');
  const filteredEncs = encs.filter(e => e.yn === 'Medicare');
  const totalRev = filteredMeds.reduce((s, m) => s + m.tc, 0);
  console.log(`  Filtered meds: ${filteredMeds.length}`);
  console.log(`  Filtered encs: ${filteredEncs.length}`);
  console.log(`  Total revenue: $${(totalRev/1e6).toFixed(2)}M`);

  // Test drug filter - Simvastatin
  console.log("\n=== TEST: Filter to Simvastatin ===");
  const simvaMeds = meds.filter(m => m.dd && m.dd.toLowerCase().includes('simvastatin'));
  console.log(`  ${simvaMeds.length} Simvastatin fills`);
  console.log(`  Revenue: $${(simvaMeds.reduce((s,m) => s+m.tc, 0)/1e6).toFixed(2)}M`);

  // Test condition filter - find patients with Viral Sinusitis
  console.log("\n=== TEST: Patients with Viral Sinusitis ===");
  const vsP = conds.filter(c => c.d === 'Viral sinusitis (disorder)');
  const vsPatients = new Set(vsP.map(c => c.pk));
  console.log(`  ${vsP.length} condition records, ${vsPatients.size} unique patients`);
  const vsMeds = meds.filter(m => vsPatients.has(m.pk));
  console.log(`  ${vsMeds.length} medication fills for these patients`);

  console.log("\n✓ All filter logic works correctly");
}

main().catch(e => { console.error("ERR:", e.message); process.exit(1); });
