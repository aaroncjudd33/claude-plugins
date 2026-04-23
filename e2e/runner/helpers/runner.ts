import { chromium, Page, Browser } from 'playwright';
import { readFileSync, existsSync } from 'fs';
import dotenv from 'dotenv';

dotenv.config();

const WS_FILE = '.browser-ws.txt';

async function cdpUrl(cdpPort: string): Promise<string> {
  for (const host of ['[::1]', '127.0.0.1']) {
    try {
      const resp = await fetch(`http://${host}:${cdpPort}/json/list`);
      const targets = await resp.json() as any[];
      if (targets.some((t: any) => t.type === 'page')) return `http://${host}:${cdpPort}`;
    } catch {}
  }
  return `http://127.0.0.1:${cdpPort}`;
}

export interface TaskResult {
  pass?: boolean;
  done?: boolean;
  message: string;
  details?: string;
}

export function step(message: string): void {
  console.log(`       → ${message}`);
}

export interface Task {
  name: string;
  tags: string[];
  run: (page: Page) => Promise<TaskResult>;
}

const registry: Task[] = [];

export function task(name: string, tags: string[], run: (page: Page) => Promise<TaskResult>): void {
  registry.push({ name, tags: tags.map(t => t.toLowerCase()), run });
}

export function getTasks(): Task[] { return registry; }

export function findTasks(query: string): Task[] {
  const q = query.toLowerCase();
  return registry.filter(t =>
    t.name.toLowerCase().includes(q) || t.tags.some(tag => tag.includes(q))
  );
}

export async function connectToPage(): Promise<{ browser: Browser; page: Page }> {
  if (!existsSync(WS_FILE)) {
    throw new Error('No browser session found. Run: npm run browser:start');
  }
  const cdpPort = readFileSync(WS_FILE, 'utf-8').trim();
  const base = await cdpUrl(cdpPort);
  const targetDomain = process.env.TARGET_DOMAIN || '';

  const browser = await chromium.connectOverCDP(base);
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      const url = p.url();
      if (url.startsWith('devtools://')) continue;
      if (!targetDomain || url.includes(targetDomain)) return { browser, page: p };
    }
  }
  // Fallback: first non-devtools page
  for (const ctx of browser.contexts()) {
    for (const p of ctx.pages()) {
      if (!p.url().startsWith('devtools://')) return { browser, page: p };
    }
  }
  throw new Error('No page found in browser. Check that the browser started correctly.');
}

export function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(`Assertion failed: ${message}`);
}

// ── Story System ──────────────────────────────────────────────

export interface Story {
  id: string;
  name: string;
  tags?: string[];
  allTags?: string[];
  include?: string[];
  exclude?: string[];
}

const storyRegistry: Story[] = [];

export function story(id: string, name: string, criteria: Omit<Story, 'id' | 'name'>): void {
  storyRegistry.push({ id: id.toLowerCase(), name, ...criteria });
}

export function getStories(): Story[] { return storyRegistry; }

export function findStory(query: string): Story | undefined {
  const q = query.toLowerCase();
  return storyRegistry.find(s => s.id === q || s.name.toLowerCase().includes(q));
}

export function resolveStory(s: Story): Task[] {
  const all = getTasks();
  const matched = new Set<Task>();

  if (s.tags) {
    for (const tag of s.tags) {
      const t = tag.toLowerCase();
      for (const t2 of all) if (t2.tags.includes(t)) matched.add(t2);
    }
  }
  if (s.allTags) {
    const required = s.allTags.map(t => t.toLowerCase());
    for (const t of all) if (required.every(r => t.tags.includes(r))) matched.add(t);
  }
  if (s.include) {
    for (const q of s.include) {
      const ql = q.toLowerCase();
      for (const t of all) if (t.name.toLowerCase().includes(ql) || t.tags.includes(ql)) matched.add(t);
    }
  }
  if (s.exclude) {
    const ex = s.exclude.map(e => e.toLowerCase());
    return [...matched].filter(t => !ex.some(e => t.name.toLowerCase().includes(e)));
  }
  return [...matched];
}
