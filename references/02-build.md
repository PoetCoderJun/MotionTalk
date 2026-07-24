# 阶段 2：Remotion 制作与正式片段

前提：导演脚本和 placement plan 已明确批准。本阶段直接生成正式 MG 片段并完成抽帧检查，不默认渲染一整套低清预览。

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
- `previews/`、`segments/`、`logs/`。

每个 cue 静音，不含字幕、人像、角标、章节或进度条。动画只用 `useCurrentFrame`、`interpolate`、`spring` 驱动，不用 wall clock。预留左上约 460×150、底部约 140、右下 400×400 安全区。相互对准的线和节点必须共用一套像素坐标。

按字幕本身大胆设计，每段只讲一个观点。导演脚本表达意图，不是施工图；可替换成更好的视觉比喻。唯一形式底线是不要做“幻灯片换页”，画面至少有一个会动的关系。

## 2. 一次 bundle、一次 browser

不要对每个 cue 调一次 `npx remotion render`。把本 Skill 的 `scripts/render-batch.mjs` 复制到项目 `remotion/scripts/`，所有同规格 cue 在一个 Node 进程中顺序渲染：

- `bundle()` 只调用一次；
- `openBrowser()` 只调用一次，并把同一个 `puppeteerInstance` 传给 `selectComposition()` 和每次 `renderMedia()`；
- 一个 batch 内顺序 render，禁止同时启动多个 Remotion render 进程。

正式制作只运行：

```bash
node scripts/render-batch.mjs segment
```

macOS 使用 H.264 VideoToolbox：`hardwareAcceleration: "required"`，正式片段 16M；禁止 CRF、encoding max rate/buffer 和 x264 preset。Linux/WSL 未单独验证硬编时使用软件编码，并在 README 标明。

VideoToolbox只加速编码，不会跳过 Chromium 的 CSS/SVG/React 逐帧绘制。默认并发 75%；用一个含 SVG、文本、视频层的 20–40 秒代表 cue 实测 50%/75%/100%，选择最快且无内存压力、掉帧或浏览器崩溃的值，记录到 `remotion/README.md`。`npx remotion gpu` 只诊断绘制后端，未经对比不要强制 `--gl`。

macOS 正式批量制作前，先渲染一个代表 cue；日志必须确认 `h264_videotoolbox` 且 `hardware accelerated: true`，否则停止。

## 3. 抽帧门禁

低清预览不是默认交付，因为它仍要让 Chromium 执行每一帧动画，常常与正式渲染耗时接近，等于把所有 cue 绘制两遍。

1. 直接批量渲染 1920×1080、16M 正式 MG。
2. 用 FFmpeg 从每个正式片段抽 4–6 帧：开头、各节拍点、结尾前 1 秒，生成拼贴检查表。
3. 逐张检查重叠、错位、出界、死时间和文字；有问题只重渲受影响的 cue。
4. 完成一轮修正，记录正式片段和检查表路径，然后结束阶段 2。

只有两类情况才按需运行 `node scripts/render-batch.mjs preview <cue-id...>`：用户明确要求动态预览，或某个 cue 的节奏/视频层同步无法靠关键帧判断。不得默认预览全部 cue。
