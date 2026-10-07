# 音频驱动的视觉制作

```bash
node <skill-root>/scripts/init_project.mjs --project-dir "$output_dir/hyperframes" --plan "$plan"
```

输入无需视频流。初始化主音频、内部字幕、可 seek 的 GSAP composition 和 project-state.json，只是 scaffold。按导演计划实际制作视觉故事，不把默认标题卡当成完整创作。

根画布直接位于 body，明确尺寸与时长；唯一主音频有唯一 id，可选视频/B-roll 默认静音避免音轨重复。DOM/SVG 字幕和图形保证中文可读性、留白与安全区。视觉随论证推进，数据必须真实，示意关系应明确标注。

时段用 clip/data-start/data-duration，Hyperframes 控制媒体；暂停动画注册到 window.__timelines.master，不自行播放/seek 媒体，不使用 CSS keyframes、系统时钟或网络字体。可选 [组件](06-modern-components.md) 安装前核对来源与许可。

```bash
node <skill-root>/scripts/hf.mjs lint "$output_dir/hyperframes"
node <skill-root>/scripts/hf.mjs preview "$output_dir/hyperframes"
```

连续预览覆盖开头、转场、密集内容和结尾；截图抽查不等于连续观看。核对字幕同步并实际试听；未执行就标 pending。完成制作后记录真实证据：

```json
{"status":"ready","input":"audio","needs_visual_production":false,
 "visual_review":{"scope":"continuous","evidence":["preview-review.md"]}}
```

证据说明实际看过的时段、问题与修订，不能伪造。渲染器检查状态记录，不验证证据内容真假。随后按 [交付](03-deliver.md) 继续。
