#!/usr/bin/env node

import {createRequire} from "node:module";
import {readFile, mkdir} from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import {pathToFileURL} from "node:url";

const HELP = `Usage:
  node render_master.mjs --project-dir DIR --props FILE [--output FILE]
    [--still FRAME:FILE ...] [--browser-executable FILE]
    [--concurrency NUMBER|PERCENT] [--hardware-acceleration MODE]
    [--video-bitrate RATE] [--offthread-video-threads NUMBER]
Defaults: concurrency 75%; hardware acceleration if-possible.
Hardware modes: disable, if-possible, required. At least one output is required.
`;

const DEFAULT_CONCURRENCY = "75%";
const DEFAULT_HARDWARE_ACCELERATION = "if-possible";
const HARDWARE_ACCELERATION_MODES = new Set(["disable", "if-possible", "required"]);

const parseArgs = (argv) => {
  const args = {stills: []};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") {
      args.help = true;
    } else if (token === "--still") {
      args.stills.push(argv[++index]);
    } else if (token.startsWith("--")) {
      const key = token.slice(2).replaceAll("-", "_");
      args[key] = argv[++index];
    } else {
      throw new Error(`Unexpected argument: ${token}`);
    }
  }
  return args;
};

const importFromProject = async (projectDir, packageName) => {
  const requireFromProject = createRequire(path.join(projectDir, "package.json"));
  const resolved = requireFromProject.resolve(packageName);
  return import(pathToFileURL(resolved).href);
};

const parseStill = (value) => {
  const separator = value.indexOf(":");
  if (separator < 1) throw new Error(`Invalid --still ${value}; expected FRAME:FILE`);
  const frame = Number(value.slice(0, separator));
  const output = value.slice(separator + 1);
  if (!Number.isInteger(frame) || frame < 0 || !output) {
    throw new Error(`Invalid --still ${value}; expected FRAME:FILE`);
  }
  return {frame, output: path.resolve(output)};
};

const parseConcurrency = (value) => {
  if (!value) return DEFAULT_CONCURRENCY;
  if (/^[1-9]\d*%$/.test(value)) return value;
  const number = Number(value);
  if (!Number.isInteger(number) || number < 1)
    throw new Error("--concurrency must be a positive integer or percentage");
  return number;
};

const parseRenderOptions = (args) => {
  const hardwareAcceleration = args.hardware_acceleration ?? DEFAULT_HARDWARE_ACCELERATION;
  if (!HARDWARE_ACCELERATION_MODES.has(hardwareAcceleration))
    throw new Error("--hardware-acceleration must be disable, if-possible, or required");
  const offthreadVideoThreads = args.offthread_video_threads
    ? Number(args.offthread_video_threads)
    : undefined;
  if (offthreadVideoThreads !== undefined &&
      (!Number.isInteger(offthreadVideoThreads) || offthreadVideoThreads < 1)) {
    throw new Error("--offthread-video-threads must be a positive integer");
  }
  return {
    concurrency: parseConcurrency(args.concurrency),
    hardwareAcceleration,
    videoBitrate: args.video_bitrate || undefined,
    offthreadVideoThreads,
  };
};

const main = async () => {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return process.stdout.write(HELP);
  if (!args.project_dir || !args.props)
    throw new Error("--project-dir and --props are required");
  if (!args.output && args.stills.length === 0)
    throw new Error("At least one --output or --still is required");
  const renderOptions = parseRenderOptions(args);

  const projectDir = path.resolve(args.project_dir);
  const propsPath = path.resolve(args.props);
  const inputProps = JSON.parse(await readFile(propsPath, "utf8"));
  if (inputProps.srtPath) {
    const captionsModule = await importFromProject(projectDir, "@remotion/captions");
    const srtPath = path.resolve(path.dirname(propsPath), inputProps.srtPath);
    inputProps.captions = captionsModule.parseSrt({
      input: await readFile(srtPath, "utf8"),
    }).captions;
  }
  inputProps.captions ??= [];
  inputProps.caption_highlights ??= {};

  const bundler = await importFromProject(projectDir, "@remotion/bundler");
  const renderer = await importFromProject(projectDir, "@remotion/renderer");
  const serveUrl = await bundler.bundle({
    entryPoint: path.join(projectDir, "src", "index.ts"),
    publicDir: path.join(projectDir, "public"),
  });
  const browserExecutable = args.browser_executable
    ? path.resolve(args.browser_executable)
    : undefined;
  const composition = await renderer.selectComposition({
    serveUrl,
    id: "MasterComposition",
    inputProps,
    browserExecutable,
  });

  if (args.output) {
    const outputLocation = path.resolve(args.output);
    await mkdir(path.dirname(outputLocation), {recursive: true});
    let lastReportedPercent = -5;
    await renderer.renderMedia({
      composition,
      serveUrl,
      inputProps,
      codec: "h264",
      audioCodec: "aac",
      outputLocation,
      overwrite: true,
      concurrency: renderOptions.concurrency,
      disallowParallelEncoding: false,
      hardwareAcceleration: renderOptions.hardwareAcceleration,
      videoBitrate: renderOptions.videoBitrate,
      offthreadVideoThreads: renderOptions.offthreadVideoThreads,
      offthreadVideoCacheSizeInBytes: 128 * 1024 * 1024,
      mediaCacheSizeInBytes: 256 * 1024 * 1024,
      browserExecutable,
      onStart: ({frameCount, parallelEncoding, resolvedConcurrency}) => {
        process.stdout.write(`Render start: ${frameCount} frames, concurrency ` +
          `${resolvedConcurrency}, parallel encoding ${parallelEncoding}\n`);
      },
      onProgress: ({progress, renderedFrames, encodedFrames}) => {
        const percent = Math.floor(progress * 100);
        if (percent >= lastReportedPercent + 5 || percent === 100) {
          lastReportedPercent = percent;
          process.stdout.write(`Render ${percent}%: rendered ${renderedFrames}, ` +
            `encoded ${encodedFrames}\n`);
        }
      },
    });
  }

  for (const request of args.stills.map(parseStill)) {
    await mkdir(path.dirname(request.output), {recursive: true});
    await renderer.renderStill({
      composition,
      serveUrl,
      inputProps,
      frame: request.frame,
      output: request.output,
      imageFormat: "png",
      overwrite: true,
      browserExecutable,
    });
  }
};

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error.message}\n`);
  process.exitCode = 1;
});
