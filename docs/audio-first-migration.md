# Audio-first migration / 音频优先迁移

MotionTalk now accepts a user audio file with optional materials. ASR, the explicit breath choice and aligned subtitles are managed inside the workflow. Existing prepared-video/SRT requests should be discussed as existing assets, not required from every user; extract/use their approved audio only if authorized and keep the supplied originals.

This branch incorporates the author's local Hyperframes upgrade (base `c14660f`) and reviewed working changes, replacing the public Remotion renderer. It retains the optional source-based mastering script without enabling mastering by default. Runtime dependencies are pinned. Render defaults remain one worker/local Chrome/hardware H.264, with explicit software smoke/production options.

New preparation edits **only reviewed breath gaps**, retaining 0.25 seconds by default. It does not inherit clean-talking-video's broader filler/retake editing scope. A no-trim choice preserves the timeline. Internal SRT is remapped against the same sample deletions as the prepared audio.

The original clean-talking-video repository remains the independent raw-video cleanup workflow. Its CLI and files are unchanged by the audio integration. Minutes continues using its existing clean-talking-video ASR dependency; MotionTalk is not a replacement backend for Minutes. Nothing is archived or deleted.

根许可证不变；第三方 ASR 模块保留 MIT 许可，其他依赖适用自身条款。音频、本地成片和参考素材不会自动上传或公开。旧 Remotion 契约测试不再适用于新引擎，替换为音频剪辑/字幕、纯音频初始化、渲染参数和元数据测试；旧测试及原公开树已在任务审查快照中保留。
