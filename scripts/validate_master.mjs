#!/usr/bin/env node

import {createRequire} from "node:module";
import {readFile, readdir, stat, writeFile} from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import {pathToFileURL} from "node:url";

const HELP = `Usage:
  node validate_master.mjs --project-dir DIR --plan FILE --props FILE
    --final FILE --output-dir DIR

Validates project-defined render metadata, approved semantic evidence, visual
checks, packaging checks, and delivery cleanliness.
`;

const parseArgs = (argv) => {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") args.help = true;
    else if (token.startsWith("--")) {
      args[token.slice(2).replaceAll("-", "_")] = argv[++index];
    } else throw new Error(`Unexpected argument: ${token}`);
  }
  return args;
};

const importFromProject = async (projectDir, packageName) => {
  const projectRequire = createRequire(path.join(projectDir, "package.json"));
  return import(pathToFileURL(projectRequire.resolve(packageName)).href);
};

const readJson = async (file) => JSON.parse(await readFile(file, "utf8"));

const checklistRecords = (payload) => {
  if (Array.isArray(payload)) return payload;
  for (const key of ["checks", "items", "invariants"]) {
    if (Array.isArray(payload?.[key])) return payload[key];
  }
  return [];
};

const fileExists = async (file) =>
  stat(file).then((value) => value.isFile()).catch(() => false);

const validateChecklist = async ({file, outputDir, expected = []}) => {
  try {
    const records = checklistRecords(await readJson(file));
    if (records.length === 0) {
      return {passed: false, path: file, reason: "no checklist records"};
    }
    const evidence = await Promise.all(
      records.map(async (record) => {
        const value = record.evidence_frame ?? record.path;
        const evidencePath = value ? path.resolve(outputDir, value) : null;
        return {
          cue_id: record.cue_id,
          invariant_id: record.invariant_id,
          evidence_time_seconds: record.evidence_time_seconds,
          status: record.status,
          path: evidencePath,
          exists: evidencePath ? await fileExists(evidencePath) : false,
        };
      }),
    );
    const evidenceByKey = new Map(
      evidence.map((item) => [
        `${item.cue_id ?? ""}/${item.invariant_id ?? ""}`,
        item,
      ]),
    );
    const expectedPassed = expected.every((item) => {
      const evidenceItem = evidenceByKey.get(`${item.cue_id}/${item.invariant_id}`);
      if (!evidenceItem) return false;
      if (typeof item.proof_moment !== "number") return true;
      return (
        Math.abs(Number(evidenceItem.evidence_time_seconds) - item.proof_moment) <=
        item.tolerance
      );
    });
    return {
      passed:
        evidence.every((item) => item.status === "passed" && item.exists) &&
        expectedPassed,
      path: file,
      records: records.length,
      expected: expected.length,
      evidence,
    };
  } catch (error) {
    return {passed: false, path: file, reason: error.message};
  }
};

const main = async () => {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return process.stdout.write(HELP);
  for (const required of ["project_dir", "plan", "props", "final", "output_dir"]) {
    if (!args[required]) {
      throw new Error(`--${required.replaceAll("_", "-")} is required`);
    }
  }

  const projectDir = path.resolve(args.project_dir);
  const outputDir = path.resolve(args.output_dir);
  const finalPath = path.resolve(args.final);
  const plan = await readJson(path.resolve(args.plan));
  const props = await readJson(path.resolve(args.props));
  const renderSpec = plan.render_spec;
  const propsSpec = props.renderSpec;
  const renderer = await importFromProject(projectDir, "@remotion/renderer");
  const metadata = await renderer.getVideoMetadata(finalPath);
  const expectedDuration = Number(props.durationInFrames) / Number(renderSpec.fps);
  const propsMatchPlan =
    Number(propsSpec?.width) === Number(renderSpec.width) &&
    Number(propsSpec?.height) === Number(renderSpec.height) &&
    Number(propsSpec?.fps) === Number(renderSpec.fps);
  const structurePassed =
    propsMatchPlan &&
    metadata.width === Number(renderSpec.width) &&
    metadata.height === Number(renderSpec.height) &&
    Math.abs(Number(metadata.fps) - Number(renderSpec.fps)) < 0.01 &&
    Math.abs(Number(metadata.durationInSeconds) - expectedDuration) <=
      3 / Number(renderSpec.fps) &&
    metadata.codec !== "unknown" &&
    metadata.audioCodec !== null &&
    metadata.audioCodec !== "unknown";

  const expectedInvariants = plan.cues.flatMap((cue) =>
    cue.spec.semantic_invariants.map((invariant) => ({
      cue_id: cue.id,
      invariant_id: invariant.id,
      proof_moment:
        typeof invariant.proof_moment === "number"
          ? invariant.proof_moment
          : null,
      tolerance: 1 / Number(renderSpec.fps),
    })),
  );
  const checklistResults = {
    semantic: await validateChecklist({
      file: path.join(outputDir, "semantic-checklist.v1.json"),
      outputDir,
      expected: expectedInvariants,
    }),
    visual: await validateChecklist({
      file: path.join(outputDir, "aspect-occlusion-checklist.v1.json"),
      outputDir,
    }),
    package: await validateChecklist({
      file: path.join(outputDir, "package-checklist.v1.json"),
      outputDir,
    }),
  };

  const finalEntries = await readdir(path.dirname(finalPath), {
    withFileTypes: true,
  });
  const cleanDelivery =
    finalEntries.length === 1 &&
    finalEntries[0].isFile() &&
    path.resolve(path.dirname(finalPath), finalEntries[0].name) === finalPath &&
    path.extname(finalEntries[0].name).toLowerCase() === ".mp4";
  const checks = {
    project_render_spec: structurePassed ? "passed" : "failed",
    semantic_invariants: checklistResults.semantic.passed ? "passed" : "failed",
    visual_integrity: checklistResults.visual.passed ? "passed" : "failed",
    approved_packaging: checklistResults.package.passed ? "passed" : "failed",
    delivery_cleanliness: cleanDelivery ? "passed" : "failed",
  };
  const passed = Object.values(checks).every((value) => value === "passed");
  const report = {
    schema_version: "motiontalk.quality-report.v1",
    status: passed ? "passed" : "failed",
    packaged_video: path.relative(outputDir, finalPath),
    checks,
    evidence: {
      media: {
        width: metadata.width,
        height: metadata.height,
        fps: metadata.fps,
        durationInSeconds: metadata.durationInSeconds,
        videoCodec: metadata.codec,
        audioCodec: metadata.audioCodec,
      },
      renderStillChecklists: checklistResults,
      finalEntries: finalEntries.map((entry) => entry.name),
    },
  };
  await writeFile(
    path.join(outputDir, "quality-report.v1.json"),
    `${JSON.stringify(report, null, 2)}\n`,
  );
  if (!passed) throw new Error("MotionTalk quality gate failed");
  process.stdout.write("MotionTalk quality gate: passed\n");
};

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error.message}\n`);
  process.exitCode = 1;
});
