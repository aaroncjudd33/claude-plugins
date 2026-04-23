import { readFileSync, unlinkSync, existsSync } from 'fs';

const WS_FILE = '.browser-ws.txt';

async function main() {
  const cdpPort = existsSync(WS_FILE)
    ? readFileSync(WS_FILE, 'utf-8').trim()
    : '9222';

  let wsUrl: string | null = null;
  for (const host of ['[::1]', '127.0.0.1']) {
    try {
      const resp = await fetch(`http://${host}:${cdpPort}/json/version`);
      const info = await resp.json() as any;
      wsUrl = info.webSocketDebuggerUrl;
      if (wsUrl) break;
    } catch {}
  }

  if (!wsUrl) {
    console.log('Browser not reachable on port', cdpPort);
    if (existsSync(WS_FILE)) unlinkSync(WS_FILE);
    return;
  }

  const ws = new WebSocket(wsUrl);

  await new Promise<void>((resolve) => {
    ws.onopen = () => ws.send(JSON.stringify({ id: 1, method: 'Browser.close' }));
    ws.onmessage = (event) => {
      const msg = JSON.parse(String(event.data));
      if (msg.id === 1) {
        if (msg.error) console.error('Browser.close failed:', msg.error.message);
        else console.log('Browser closed.');
        ws.close();
        resolve();
      }
    };
    ws.onerror = () => { console.log('Browser closed (connection dropped).'); resolve(); };
    ws.onclose = () => resolve();
    setTimeout(() => { ws.close(); resolve(); }, 5_000);
  });

  if (existsSync(WS_FILE)) unlinkSync(WS_FILE);
  console.log('Session file cleaned up.');
}

main();
