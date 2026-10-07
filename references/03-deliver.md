# 导出与交付

```bash
node <skill-root>/scripts/render_master.mjs --project-dir "$output_dir/hyperframes" \
  --plan "$plan" --output "$output_dir/final/video.mp4"
node <skill-root>/scripts/validate_master.mjs --plan "$plan" \
  --final "$output_dir/final/video.mp4" --output-dir "$output_dir"
```

production 导出要求 ready 和连续预览证据。默认本机完整 Chrome、单 worker、硬件 H.264；环境不支持时明确使用 --encoding software，不静默替换。不能自动下载浏览器或升级运行时。--purpose smoke 仅用于标为合成的技术测试，不绕过创作者视频的制作。

final/ 仅含最终 MP4，日志、计划、字幕和报告在工作目录。校验批准状态、尺寸/帧率、视频和音频时长、H.264/AAC、单文件交付；时长容差为三帧，不是感知同步证明。连续观看和试听覆盖开头/中段/尾段，核对字幕、论点与尾部音频。

quality-report.v1.json scope=technical；视觉与听感单独记录，没做就 pending，不把技术通过写成创意或音质已确认。交付视频、导演计划、准备报告、技术报告、预览/试听结论和真实限制。失败保留日志，不以假样例替代。

不自动上传 GitHub、Library 或视频平台；[非商业许可](../LICENSE.md) 与商业事先书面授权要求保留。
