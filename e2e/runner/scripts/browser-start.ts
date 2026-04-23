import { chromium } from 'playwright';
import { writeFileSync, existsSync, readFileSync } from 'fs';
import { execSync } from 'child_process';
import { join } from 'path';
import dotenv from 'dotenv';

dotenv.config();

const CDP_PORT = Number(process.env.CDP_PORT) || 9222;
const WS_FILE = '.browser-ws.txt';

interface TabConfig { url: string; bringToFront?: boolean; }
interface E2EConfig { tabs: TabConfig[]; }

function loadTabConfig(): E2EConfig {
  const projectDir = process.env.E2E_PROJECT_DIR;
  if (projectDir) {
    const configPath = join(projectDir, '.e2e.json');
    if (existsSync(configPath)) {
      return JSON.parse(readFileSync(configPath, 'utf-8'));
    }
  }
  const localConfig = join('.', '.e2e.json');
  if (existsSync(localConfig)) {
    return JSON.parse(readFileSync(localConfig, 'utf-8'));
  }
  const baseURL = process.env.BASE_URL || 'http://localhost:3000';
  return { tabs: [{ url: baseURL, bringToFront: true }] };
}

function interpolate(url: string): string {
  return url.replace(/\$\{(\w+)\}/g, (_, key) => process.env[key] ?? '');
}

function portHolders(port: number): string[] {
  try {
    const lines = execSync(`netstat -ano`, { encoding: 'utf-8' })
      .split('\n')
      .filter(l => l.includes(`:${port}`) && l.includes('LISTENING'));
    return [...new Set(lines.map(l => l.trim().split(/\s+/).pop()).filter(Boolean))];
  } catch {
    return [];
  }
}

async function tryGracefulClose(port: number): Promise<boolean> {
  try {
    const browser = await chromium.connectOverCDP(`http://[::1]:${port}`);
    await browser.close();
    return true;
  } catch {
    try {
      const browser = await chromium.connectOverCDP(`http://localhost:${port}`);
      await browser.close();
      return true;
    } catch {
      return false;
    }
  }
}

async function main() {
  const holders = portHolders(CDP_PORT);
  if (holders.length > 0) {
    console.log(`Port ${CDP_PORT} is in use (PID ${holders.join(', ')}). Attempting graceful close...`);
    const closed = await tryGracefulClose(CDP_PORT);
    if (closed) await new Promise(r => setTimeout(r, 2000));
    const still = portHolders(CDP_PORT);
    if (still.length > 0) {
      console.error(`Port ${CDP_PORT} is still held by PID ${still.join(', ')}.`);
      console.error('Run "npm run browser:stop" first, or close the browser window manually.');
      process.exit(1);
    }
    console.log('Port cleared.');
  }

  console.log(`Launching browser on CDP port ${CDP_PORT}...`);

  const browser = await chromium.launch({
    headless: false,
    args: [
      `--remote-debugging-port=${CDP_PORT}`,
      '--start-maximized',
      '--disable-features=PrivateNetworkAccessPermissionPrompt',
    ],
  });

  const contextOptions: any = { viewport: null };
  if (process.env.HTTP_AUTH_USER && process.env.HTTP_AUTH_PASS) {
    contextOptions.httpCredentials = {
      username: process.env.HTTP_AUTH_USER,
      password: process.env.HTTP_AUTH_PASS,
    };
  }

  const context = await browser.newContext(contextOptions);
  const config = loadTabConfig();

  for (const tab of config.tabs) {
    const p = await context.newPage();
    await p.goto(interpolate(tab.url), { waitUntil: 'domcontentloaded', timeout: 30_000 });
    if (tab.bringToFront) await p.bringToFront();
  }

  writeFileSync(WS_FILE, String(CDP_PORT));

  console.log('\n✓ Browser launched.');
  console.log('  Run tasks:   npm run t -- "task-name"');
  console.log('  List tasks:  npm run t:list');
  console.log('  Stop:        npm run browser:stop\n');

  process.on('SIGINT', async () => {
    console.log('\nClosing...');
    await browser.close();
    try { require('fs').unlinkSync(WS_FILE); } catch {}
    process.exit(0);
  });

  await new Promise(() => {});
}

main().catch(err => {
  console.error('Error during startup:', err.message || err);
  process.exit(1);
});
