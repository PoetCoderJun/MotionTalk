#!/usr/bin/env node
import {runCli} from './hyperframes_runtime.mjs';

const [command, ...args] = process.argv.slice(2);
const allowed = ['catalog', 'add', 'lint', 'preview', 'doctor'];
if (!command || command === '--help') {
  console.log('Usage: node scripts/hf.mjs catalog|add|lint|preview|doctor [Hyperframes CLI options]\nRender with render_master.mjs. Use --help after a command for its options.');
} else if (!allowed.includes(command)) {
  console.error(`Unsupported command ${command}. Use render_master.mjs for exports.`);
  process.exitCode = 1;
} else {
  try { await runCli([command, ...args]); }
  catch (error) { console.error(error.message); process.exitCode = 1; }
}
