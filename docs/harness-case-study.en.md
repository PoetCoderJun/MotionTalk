# MotionTalk: an inspectable Agent Harness case study

[中文](harness-case-study.md) · [Back to the project](../README_EN.md)

An Agent can propose visuals and generate rendering code, but a successful render does not establish that it expresses the right content. MotionTalk leaves open-ended direction to the Agent and puts mechanically checkable constraints in small scripts.

## From intent to evidence

| Stage | Reviewable artifact | Public implementation |
| --- | --- | --- |
| Planning | Readable script, machine plan, visual intent and assertions for every cue | [Planning rules](../references/01-plan.md) |
| Approval | `status=approved` and `approved=true`; replan after changes | [Stage routing](../SKILL.md) |
| Structure | Positive render spec, frame grid, contiguous cues from zero through source duration, nonempty prompts and assertions | [validate_plan.py](../scripts/validate_plan.py) |
| Build and inspect | One project composition; one renderer for video and evidence frames; Agent-authored semantic / visual / packaging checklists | [Build rules](../references/02-build.md), [render_master.mjs](../scripts/render_master.mjs) |
| Delivery gate | Output metadata, evidence paths and times for assertions, passed checklist records, one MP4 in the final directory | [validate_master.mjs](../scripts/validate_master.mjs), [Delivery rules](../references/03-deliver.md) |

The harness combines plans, state, tool entry points, evidence and acceptance contracts. Visual creation remains flexible; reference themes are not code enums.

## What is actually deterministic

`validate_plan.py` rejects unapproved plans, empty visual prompts, missing assertions, off-grid times and cue gaps / overlaps. It does not check whether source media exists or decodes, or whether the actual SRT matches; those are planning input checks. Approval fields do not authenticate a user, signature or approved revision, and inputs are not bound by hashes.

`validate_master.mjs` compares output dimensions, frame rate and duration with plan / props (a three-frame duration tolerance), checks known codecs and audio presence. For numeric proof moments, recorded evidence times must be within one frame; every checklist record must be passed and its evidence file must exist. The final directory must contain only the specified MP4.

These are record and file checks. The validator does not interpret evidence pixels, verify that an image matches its reported time, establish audio provenance, or invoke the plan validator itself. Run plan validation first, then build, inspect frames and write checklists, then validate delivery. The report supports review; it is not a proof of visual correctness.

## Reproduce the smallest evidence

From the repository root:

```bash
python3 examples/plan-validation/run.py
python3 -m unittest discover -s tests -v
node scripts/render_master.mjs --help
node scripts/validate_master.mjs --help
```

The [synthetic example](../examples/plan-validation/README.md) checks only the plan contract. It reads no media, calls no models and downloads no dependencies. Existing tests cover approval, timeline, prompt and renderer interface contracts; they are not a full production render or visual evaluation. The four README images are existing visual evidence; their complete source videos and rendering projects are not bundled.

## Transferable engineering ideas

For Work, break “a correct summary” into source provenance, assertion evidence and editable delivery. The separation of planning, approval and evidence is worth exploring in Robotics and Finance, with their own safety constraints, environment feedback and domain evaluation. This media case does not establish robotics deployment, financial-system performance or enterprise ROI.

Use and adaptation follow [CC BY-NC-SA 4.0](../LICENSE.md); commercial use requires prior written permission. Third-party materials retain their own rights.
