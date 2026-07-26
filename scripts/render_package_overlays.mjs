#!/usr/bin/env node
import {createRequire} from "node:module";
import {mkdirSync, readFileSync} from "node:fs";
import {join, resolve} from "node:path";
import process from "node:process";
import {pathToFileURL} from "node:url";

const help = `Usage:
  node render_package_overlays.mjs --project-dir DIR --props FILE --output-dir DIR [options]

Options:
  --entry FILE                 Remotion entry point (default: src/index.ts)
  --composition ID             Packaging composition (default: Package)
  --browser-executable FILE    Chrome/Chromium executable
  --help                       Show this help

The script bundles once, opens one browser, and renders one transparent PNG at
the start of each topic. The composition must support overlayOnly input props.
`;

const args = process.argv.slice(2);
if (args.includes("--help") || args.includes("-h")) {
  process.stdout.write(help);
  process.exit(0);
}
const valueOf = (flag, fallback = null) => {
  const index = args.indexOf(flag);
  if (index === -1) return fallback;
  if (!args[index + 1] || args[index + 1].startsWith("--")) {
    throw new Error(`${flag} requires a value`);
  }
  return args[index + 1];
};
const required = (flag) => {
  const value = valueOf(flag);
  if (!value) throw new Error(`${flag} is required\n\n${help}`);
  return value;
};

const projectDir = resolve(required("--project-dir"));
const propsPath = resolve(required("--props"));
const outputDir = resolve(required("--output-dir"));
const entryPoint = resolve(projectDir, valueOf("--entry", "src/index.ts"));
const compositionId = valueOf("--composition", "Package");
const parsedProps = JSON.parse(readFileSync(propsPath, "utf8"));
const inputProps = {...parsedProps, overlayOnly: true};
if (!Array.isArray(inputProps.topics) || inputProps.topics.length === 0) {
  throw new Error("package props must contain a non-empty topics array");
}
const overlayDir = join(outputDir, "package-overlays");
mkdirSync(overlayDir, {recursive: true});

const projectRequire = createRequire(join(projectDir, "package.json"));
const bundlerUrl = pathToFileURL(
  projectRequire.resolve("@remotion/bundler"),
).href;
const rendererUrl = pathToFileURL(
  projectRequire.resolve("@remotion/renderer"),
).href;
const {bundle} = await import(bundlerUrl);
const {openBrowser, renderStill, selectComposition} = await import(rendererUrl);

const serveUrl = await bundle({
  entryPoint,
  outDir: join(projectDir, ".remotion-bundle"),
});
const browserExecutable =
  valueOf("--browser-executable") ||
  process.env.REMOTION_BROWSER_EXECUTABLE ||
  null;
const browser = await openBrowser("chrome", {browserExecutable});
try {
  const composition = await selectComposition({
    serveUrl,
    id: compositionId,
    inputProps,
    puppeteerInstance: browser,
  });
  for (const topic of inputProps.topics) {
    const frame = Math.max(
      0,
      Math.min(
        composition.durationInFrames - 1,
        Math.ceil(Number(topic.startSeconds) * composition.fps),
      ),
    );
    const output = join(overlayDir, `${topic.id}.png`);
    await renderStill({
      composition,
      serveUrl,
      output,
      frame,
      inputProps,
      imageFormat: "png",
      puppeteerInstance: browser,
    });
    process.stdout.write(`Rendered ${output} at frame ${frame}\n`);
  }
} finally {
  await browser.close({silent: false});
}
