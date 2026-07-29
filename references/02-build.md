# 阶段 2A：Remotion 制作与正式片段

前提：导演脚本和 placement plan 已明确批准，且每个 MG cue 都有已批准的 `semantic_invariants`。旧计划缺少该字段时退回阶段 1 补齐并重新批准。本阶段直接生成正式 MG 片段并完成画面与语义抽帧检查，不生成预览视频。

## 1. 环境和工程

支持 macOS、Linux、WSL。要求 Node.js >=20、npm、FFmpeg/ffprobe >=6。项目内固定安装：

```bash
npm install --save-exact @remotion/cli@4.0.419 @remotion/bundler@4.0.419 @remotion/renderer@4.0.419 remotion@4.0.419 react@19.2.3 react-dom@19.2.3
npm install --save-dev --save-exact typescript@5.6.3 @types/react@18.3.12 @types/react-dom@18.3.1
npx remotion browser ensure
```

不得依赖全局 Remotion。创建：

- `remotion/src/specs.ts`：cue id、时间窗、30fps 帧数；
- `Root.tsx`：每 cue 一个 1920×1080@30fps composition；
- `scenes/`、`components.tsx`、`theme.ts`；
- `Package.tsx`：阶段 3 使用的唯一包装层；
- `segments/`、`proof-frames/`、`logs/`。

每个 cue 静音，不含字幕、人像、角标、章节或进度条。动画只用 `useCurrentFrame`、`interpolate`、`spring` 驱动，不用 wall clock。预留左上约 460×150、底部约 140、右下 400×400 安全区。相互对准的线和节点必须共用一套像素坐标。

`floating-overlay` 主题（抠绿链路）的额外硬约束：

- 场景背景整屏纯色 `#00FF00`；元素、文字、图标、描边、阴影禁用绿色系；
- 禁用半透明填充与模糊投影（会被 colorkey 抠穿），阴影用不透明深色偏移块；
- 批准版 `presenter_policy` 的人脸安全区绝对留空，MG 只进入 `mg_allowed_zones`。

工程搭建提速：已有同版本（@remotion/* 4.0.419 / react 19.2.3）的旧工程时，直接整目录复制 `node_modules`、`package.json`、`package-lock.json`、`tsconfig.json`，跳过 `npm install`。

按字幕本身大胆设计，每段只讲一个观点。导演脚本表达意图，不是施工图；可替换成更好的视觉比喻。唯一形式底线是不要做“幻灯片换页”，画面至少有一个会动的关系。

## 2. 一次 bundle、一次 browser

使用本 Skill 固化的 `scripts/render_segments.mjs`，不要在项目里再写一份 `render-batch.mjs`。它从批准版 placement plan 自动取得所有非纯人像 cue，并在一个 Node 进程中顺序渲染：

- `bundle()` 只调用一次；
- `openBrowser()` 只调用一次，并把同一个 `puppeteerInstance` 传给 `selectComposition()` 和每次 `renderMedia()`；
- 一个 batch 内顺序 render，禁止同时启动多个 Remotion render 进程。

```bash
node <skill-root>/scripts/render_segments.mjs \
  --project-dir "$output_dir/remotion" \
  --plan "$output_dir/mg-placement-plan.v1.json" \
  --output-dir "$output_dir"
```

只重渲受影响 cue 时增加 `--ids C02,C07 --overwrite`。浏览器不在默认位置时使用 `--browser-executable` 或 `REMOTION_BROWSER_EXECUTABLE`。其他参数以脚本 `--help` 为准。

macOS 使用 H.264 VideoToolbox：`hardwareAcceleration: "required"`，正式片段 16M；禁止 CRF、encoding max rate/buffer 和 x264 preset。Linux/WSL 未单独验证硬编时使用软件编码，并在 README 标明。

VideoToolbox只加速编码，不会跳过 Chromium 的 CSS/SVG/React 逐帧绘制。并发固定为 75%，不做 50%/75%/100% benchmark，也不按项目动态调参。`npx remotion gpu` 只诊断绘制后端，未经明确故障排查不要强制 `--gl`。

macOS 正式批量制作前，先渲染一个代表 cue；日志必须确认 `h264_videotoolbox` 且 `hardware accelerated: true`，否则停止。

## 3. 画面与语义抽帧门禁

不生成低清预览、整片预览或同内容的第二套编码。静态证据用正式片段抽帧；需要判断节奏、状态先后或视频层同步时，直接检查正式 MG 片段本身。

1. 直接批量渲染 1920×1080、16M 正式 MG。
2. 用 FFmpeg 从每个正式片段抽帧：开头、各视觉节拍、结尾前 1 秒，以及每条 `semantic_invariants[].proof_moment` 对应的证据帧；同一帧可同时证明多条验收点。
3. 先检查画面质量：重叠、错位、出界、死时间、文字和安全区。
4. 再把证据帧与批准版 `semantic_invariants` 逐条对照：画面必须直接支持 `assertion`，且没有出现任何 `forbidden`。不能用“整体意思差不多”“也算一种分叉”或“导演脚本不是施工图”替代逐条证明。
5. 写入 `semantic-checklist.v1.json`：记录数组的键必须是 `checks`、`items` 或 `invariants` 之一（`quality_gate.py` 只认这三个键），每条记录包含 `cue_id/invariant_id/evidence_frame/evidence_time_seconds/status/notes`。只有全部记录为 `passed`，该 cue 才能通过；无法仅凭静态帧判断节奏或状态先后时，直接播放正式 cue，并补抽状态变化前后的证据帧。
6. 任一画面项或语义项失败，只修改并重渲受影响的 cue，然后重新生成它的检查表和语义清单。

## 4. 连续进入整片合成与交付

全部正式片段、画面检查表和 `semantic-checklist.v1.json` 通过后，记录其路径，**立即读取并执行** [03-deliver.md](03-deliver.md)。这只是批准后同一制作阶段的后半程，不是新的用户确认边界。

不得停下或再次等待用户确认，不得把“正式 MG 已完成”“语义验收已通过”当作本次调用的交付结果。必须继续完成整片合成、包装、最终质量门禁和正式成片交付。只有质量门禁需要修复时，回到受影响步骤修复并重验；若必须改变已经批准的时间线、文案、布局或遮挡策略，才退回规划阶段请求重新批准。
