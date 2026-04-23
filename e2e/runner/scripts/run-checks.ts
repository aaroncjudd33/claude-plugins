import { connectToPage, getTasks, findTasks, getStories, findStory, resolveStory, Task } from '../helpers/runner';

// ── Register your tasks here ──────────────────────────────────
// import '../tasks/my-feature';

// ── Register your stories here ────────────────────────────────
// import '../stories/BPT2-XXXX';

const args = process.argv.slice(2);
const command = args[0] || '';

function listTasks(query?: string) {
  const tasks = query ? findTasks(query) : getTasks();
  const allTags = new Set<string>();
  for (const t of tasks) t.tags.forEach(tag => allTags.add(tag));
  console.log(`\nTasks (${tasks.length} total)`);
  if (allTags.size > 0) console.log(`Tags: ${[...allTags].sort().join(', ')}\n`);
  for (const t of tasks) {
    console.log(`  ${t.name}`);
    console.log(`    tags: ${t.tags.join(', ')}`);
  }
  console.log('');
}

function listStories(query?: string) {
  const stories = getStories();
  const filtered = query
    ? stories.filter(s => s.id.includes(query.toLowerCase()) || s.name.toLowerCase().includes(query.toLowerCase()))
    : stories;
  console.log(`\nStories (${filtered.length} total)\n`);
  for (const s of filtered) {
    const resolved = resolveStory(s);
    console.log(`  ${s.id.toUpperCase()} — ${s.name}`);
    console.log(`    resolves to ${resolved.length} task(s):`);
    for (const t of resolved) console.log(`      - ${t.name}`);
    console.log('');
  }
}

async function runTaskList(tasks: Task[], label: string) {
  console.log(`\nConnecting to browser...`);
  const { browser, page } = await connectToPage();
  console.log(`Running ${tasks.length} task(s) — ${label}\n`);

  let passed = 0, failed = 0, done = 0, skipped = 0;

  for (const t of tasks) {
    console.log(`\n  ▶  ${t.name}`);
    const startTime = Date.now();
    try {
      const result = await t.run(page);
      const elapsed = Date.now() - startTime;
      if (result.message.startsWith('skipped')) {
        skipped++;
        console.log(`  -  ${t.name} (${elapsed}ms)\n     ${result.message}`);
      } else if (result.pass === true) {
        passed++;
        console.log(`  ✓  ${t.name} (${elapsed}ms)\n     ${result.message}`);
      } else if (result.pass === false) {
        failed++;
        console.log(`  ✗  ${t.name} (${elapsed}ms)\n     ${result.message}`);
      } else if (result.done) {
        done++;
        console.log(`  ●  ${t.name} (${elapsed}ms)\n     ${result.message}`);
      }
      if (result.details) console.log(`     ${result.details}`);
    } catch (err) {
      failed++;
      const elapsed = Date.now() - startTime;
      console.log(`  ✗  ${t.name} (${elapsed}ms)\n     ERROR: ${err instanceof Error ? err.message : String(err)}`);
    }
  }

  const parts: string[] = [];
  if (passed) parts.push(`${passed} passed`);
  if (failed) parts.push(`${failed} failed`);
  if (done) parts.push(`${done} done`);
  if (skipped) parts.push(`${skipped} skipped`);
  console.log(`\n  ${parts.join(', ')}\n`);

  try { browser.disconnect(); } catch {}
  process.exit(failed > 0 ? 1 : 0);
}

async function main() {
  if (command === '--list' || command === 'list') {
    listTasks(args[1]);
  } else if (command === '--stories' || command === 'stories') {
    listStories(args[1]);
  } else if (command === '--help' || command === '') {
    console.log(`
Usage:
  npm run t -- <query>         Run tasks matching query (name or tag)
  npm run t -- story <id>      Run all tasks for a story
  npm run t -- --list          List all tasks
  npm run t -- --list <q>      Search tasks
  npm run t -- --stories       List all stories

Examples:
  npm run t -- "my-feature"    Run tasks matching "my-feature"
  npm run t -- story BPT2-1234 Run all tasks for a story
  npm run t -- --list          Show all registered tasks
`);
  } else if (command === 'story') {
    const s = findStory(args[1]);
    if (!s) { console.log(`\nNo story found matching "${args[1]}".\n`); listStories(); return; }
    await runTaskList(resolveStory(s), `${s.id.toUpperCase()} — ${s.name}`);
  } else {
    const tasks = findTasks(command);
    if (tasks.length === 0) {
      const s = findStory(command);
      if (s) { await runTaskList(resolveStory(s), `${s.id.toUpperCase()} — ${s.name}`); return; }
      console.log(`\nNo tasks or stories match "${command}". Run with --help.\n`);
      return;
    }
    await runTaskList(tasks, `matching "${command}"`);
  }
}

main().catch(err => { console.error(err.message); process.exit(1); });
