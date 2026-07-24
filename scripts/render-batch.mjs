#!/usr/bin/env node
import {mkdirSync} from 'node:fs';
import {platform} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {getCompositions, openBrowser, renderMedia, selectComposition} from '@remotion/renderer';

const usage = `Usage:
  node scripts/render-batch.mjs preview [composition-id ...]
  node scripts/render-batch.mjs segment [composition-id ...]
  node scripts/render-batch.mjs package [composition-id ...]

Options:
  --concurrency=<number|percent>  Default: 75%
  --help                         Show this help

The entry point is bundled once and one browser is reused for every render in
the batch. Preview is opt-in; the normal path renders final segments directly.`;

const rawArgs = process.argv.slice(2);
if (rawArgs.includes('--help') || rawArgs.includes('-h')) {
  console.log(usage);
  process.exit(0);
}

const profileName = rawArgs[0];
const profiles = {
  preview: {scale: 0.5, bitrate: '4M', directory: 'previews', suffix: '.preview.mp4'},
  segment: {scale: 1, bitrate: '16M', directory: 'segments', suffix: '.mp4'},
  package: {scale: 1, bitrate: '16M', directory: 'final', suffix: '_final.mp4'},
};
const profile = profiles[profileName];
if (!profile) {
  console.error(usage);
  process.exit(2);
}

const concurrencyArg = rawArgs.find((arg) => arg.startsWith('--concurrency='));
const concurrency = concurrencyArg?.slice('--concurrency='.length) || '75%';
const requestedIds = rawArgs.slice(1).filter((arg) => !arg.startsWith('--'));

const here = dirname(fileURLToPath(import.meta.url));
const remotionRoot = resolve(here, '..');
const outputRoot = resolve(remotionRoot, '..');
const outputDirectory = join(outputRoot, profile.directory);
const entryPoint = join(remotionRoot, 'src', 'index.ts');
mkdirSync(outputDirectory, {recursive: true});

const startedAt = Date.now();
console.log(`[batch] profile=${profileName} concurrency=${concurrency}`);
console.log('[batch] bundling once');
let lastBundlePercent = -1;
const serveUrl = await bundle({
  entryPoint,
  onProgress: (progress) => {
    const percent = progress <= 1 ? Math.round(progress * 100) : Math.round(progress);
    if (percent !== lastBundlePercent && (percent % 20 === 0 || percent === 100)) {
      lastBundlePercent = percent;
      console.log(`[bundle] ${percent}%`);
    }
  },
});

console.log('[batch] opening one browser');
const browser = await openBrowser('chrome', {logLevel: 'verbose'});

try {
  const selected = [];
  if (requestedIds.length) {
    for (const id of requestedIds) {
      selected.push(
        await selectComposition({
          serveUrl,
          id,
          puppeteerInstance: browser,
          logLevel: 'verbose',
        }),
      );
    }
  } else {
    const compositions = await getCompositions(serveUrl, {
      puppeteerInstance: browser,
      logLevel: 'verbose',
    });
    selected.push(
      ...compositions.filter((composition) =>
        profileName === 'package'
          ? composition.id.endsWith('-package')
          : !composition.id.includes('-package'),
      ),
    );
  }

  if (selected.length === 0) throw new Error(`No compositions selected for ${profileName}`);

  for (const composition of selected) {
    const basename =
      profileName === 'package'
        ? `${composition.id.replace(/-package$/, '')}${profile.suffix}`
        : `${composition.id}${profile.suffix}`;
    const outputLocation = join(outputDirectory, basename);
    let lastReported = -1;
    const renderStartedAt = Date.now();
    console.log(`[render] ${composition.id} -> ${outputLocation}`);
    await renderMedia({
      composition,
      serveUrl,
      puppeteerInstance: browser,
      outputLocation,
      codec: 'h264',
      hardwareAcceleration: platform() === 'darwin' ? 'required' : 'disable',
      videoBitrate: profile.bitrate,
      scale: profile.scale,
      concurrency,
      overwrite: true,
      logLevel: 'verbose',
      onProgress: ({progress}) => {
        const percent = Math.floor(progress * 10) * 10;
        if (percent !== lastReported) {
          lastReported = percent;
          console.log(`[render] ${composition.id} ${percent}%`);
        }
      },
    });
    console.log(`[render] ${composition.id} done in ${((Date.now() - renderStartedAt) / 1000).toFixed(1)}s`);
  }
} finally {
  await browser.close({silent: true});
}

console.log(`[batch] done in ${((Date.now() - startedAt) / 1000).toFixed(1)}s`);
