#!/usr/bin/env node
import {createRequire} from "node:module";
import {existsSync, mkdirSync, readFileSync} from "node:fs";
import {dirname, join, resolve} from "node:path";
import process from "node:process";
import {pathToFileURL} from "node:url";

const help = `Usage:
  node render_segments.mjs --project-dir DIR --plan FILE --output-dir DIR [options]

Options:
  --entry FILE                 Remotion entry point (default: src/index.ts)
  --ids C01,C02                Render only these cue IDs
  --props FILE                 Optional JSON input props
  --browser-executable FILE    Chrome/Chromium executable
  --overwrite                  Replace existing segments
  --help                       Show this help

The script bundles once, opens one browser, and sequentially renders every
non-presenter cue as 1920x1080 H.264 at 16M with 75% concurrency.
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
const planPath = resolve(required("--plan"));
const outputDir = resolve(required("--output-dir"));
const entryPoint = resolve(projectDir, valueOf("--entry", "src/index.ts"));
const propsPath = valueOf("--props");
const inputProps = propsPath
  ? JSON.parse(readFileSync(resolve(propsPath), "utf8"))
  : {};
const plan = JSON.parse(readFileSync(planPath, "utf8"));
if (plan.status !== "approved" || plan.approved !== true) {
  throw new Error("placement plan must be approved");
}

const requested = new Set(
  (valueOf("--ids", "") || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean),
);
const cueIds = plan.cues
  .filter((cue) => cue.visual !== "presenter-full-screen")
  .map((cue) => cue.id)
  .filter((id) => requested.size === 0 || requested.has(id));
if (cueIds.length === 0) throw new Error("no matching non-presenter cues");

const outputSegments = join(outputDir, "segments");
mkdirSync(outputSegments, {recursive: true});
mkdirSync(join(outputDir, "logs"), {recursive: true});

const projectRequire = createRequire(join(projectDir, "package.json"));
const bundlerUrl = pathToFileURL(
  projectRequire.resolve("@remotion/bundler"),
).href;
const rendererUrl = pathToFileURL(
  projectRequire.resolve("@remotion/renderer"),
).href;
const {bundle} = await import(bundlerUrl);
const {openBrowser, renderMedia, selectComposition} = await import(rendererUrl);

const serveUrl = await bundle({
  entryPoint,
  outDir: join(projectDir, ".remotion-bundle"),
  onProgress: (progress) =>
    process.stdout.write(`\rBundle ${Math.round(progress)}%`),
});
process.stdout.write("\n");

const browserExecutable =
  valueOf("--browser-executable") ||
  process.env.REMOTION_BROWSER_EXECUTABLE ||
  null;
const browser = await openBrowser("chrome", {browserExecutable});
const hardwareAcceleration =
  process.platform === "darwin" ? "required" : "disable";
process.stdout.write(
  `Render settings: hardwareAcceleration=${hardwareAcceleration}, videoBitrate=16M, concurrency=75%, muted=true\n`,
);

try {
  for (const id of cueIds) {
    const outputLocation = join(outputSegments, `${id}.mp4`);
    if (existsSync(outputLocation) && !args.includes("--overwrite")) {
      process.stdout.write(`Skip existing ${outputLocation}\n`);
      continue;
    }
    const composition = await selectComposition({
      serveUrl,
      id,
      inputProps,
      puppeteerInstance: browser,
    });
    let lastPrinted = -1;
    await renderMedia({
      composition,
      serveUrl,
      codec: "h264",
      outputLocation,
      inputProps,
      puppeteerInstance: browser,
      concurrency: "75%",
      videoBitrate: "16M",
      hardwareAcceleration,
      muted: true,
      onProgress: ({progress}) => {
        const percent = Math.floor(progress * 100);
        if (percent !== lastPrinted && percent % 5 === 0) {
          lastPrinted = percent;
          process.stdout.write(`${id}: ${percent}%\n`);
        }
      },
    });
    process.stdout.write(`Rendered ${outputLocation}\n`);
  }
} finally {
  await browser.close({silent: false});
}
