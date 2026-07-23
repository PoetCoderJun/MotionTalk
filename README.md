# producing-course-video-mg

一个用于课程视频 MG 后期制作的 Codex Skill。它从已经精剪完成的人像视频、最终 SRT 和可选的同步录屏出发，完成字幕驱动的 MG 规划、预览、画面合成与交付验收。

本仓库发布的是工作流说明与 Codex Skill 配置，不包含课程原片、字幕、成片、字体、品牌素材或既有课程工程。

## 能做什么

- 检查单视频或双视频输入是否满足 MG 制作条件；
- 根据最终字幕规划整条视频在人像、录屏和 MG 之间的切换；
- 生成可审阅的 MG 导演脚本和机器可读 placement plan；
- 使用 Remotion 制作帧驱动 MG；
- 使用 FFmpeg 合成人像、录屏、MG 和唯一主音轨；
- 输出干净母版与包含字幕、章节和进度条的打包版；
- 在正式渲染前执行导演脚本确认和低清预览确认。

它不负责 ASR、口播精剪或双视频重新同步。

## 安装 Skill

将仓库克隆到 Codex 的个人 Skill 目录：

```bash
git clone https://github.com/PoetCoderJun/producing-course-video-mg.git ~/.agents/skills/producing-course-video-mg
```

确认以下文件存在：

```text
producing-course-video-mg/
├── README.md
├── LICENSE.md
├── SKILL.md
└── agents/
    └── openai.yaml
```

重启或重新加载 Codex 后，可以通过 `$producing-course-video-mg` 显式调用。

## 运行环境

- macOS、Linux 或 WSL；
- Node.js `>=20` 与 npm；
- FFmpeg 和 ffprobe `>=6`；
- Remotion `4.0.419`；
- React 和 React DOM `19.2.3`；
- TypeScript `5.6.3`。

完整安装命令、浏览器准备和 FFmpeg 能力检查见 [SKILL.md](./SKILL.md) 的“独立运行与依赖”部分。Remotion 使用项目内依赖，通过 `npx remotion` 调用，不要求全局安装。

## 输入

调用时准备：

- `face_video`：精剪后的人像或口播视频；
- `subtitles`：与人像视频匹配的最终 SRT；
- `screen_video`：可选，与人像视频从 `00:00` 同步且等长的录屏；
- `lesson_id`：本次制作的课程标识；
- `output_dir`：全部中间产物与交付物的输出目录。

示例：

```text
Use $producing-course-video-mg to create MG for:
- face_video: /data/face.mp4
- subtitles: /data/final.srt
- screen_video: /data/screen.mp4
- lesson_id: lesson-alpha
- output_dir: /work/mg/lesson-alpha
```

## 工作流门禁

这个 Skill 不会未经确认直接跑到最终成片：

1. 先交付 MG 导演脚本与 placement plan，获得明确批准后才制作 MG。
2. 先交付低清预览与检查材料，获得明确批准后才渲染正式片段和成片。

批准后若时间点、文案、布局或遮挡策略改变，需要退回相应门禁重新确认。

## 隐私与素材安全

- 视频、字幕和产物默认只在本地处理；
- 不要把课程原片、录屏、SRT、学员信息或最终成片提交到本仓库；
- 不要提交 API key、访问令牌、Cookie、账号配置或本机绝对路径；
- 若素材包含第三方图片、字体、品牌或人物肖像，发布成片前应另行确认授权。

## 第三方依赖

本仓库不打包 Remotion、React、Node.js、FFmpeg 或浏览器程序。它们分别适用各自的许可和使用条款，本仓库的许可不会覆盖或改变第三方依赖的许可。

Remotion 使用特殊许可：个人、小型团队和部分非营利主体可能符合免费条件，其他组织可能需要商业许可。使用前请检查 [Remotion 当前许可](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)。

## 许可

本仓库中的原创说明文字和配置采用 [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](./LICENSE.md) 许可。

- 可以在非商业目的下复制、修改和分享；
- 必须署名并说明是否修改；
- 修改版必须继续采用相同许可；
- 不允许商业使用；商业授权需要事先取得著作权人的书面许可。

这是一份非商用许可，因此本项目应描述为 `source-available` 或“开放内容”，不应标记为 OSI-approved open source。

## 发布前检查

```bash
# 检查本机路径、密钥和令牌痕迹
rg -n '/Users/|/home/|BEGIN .*PRIVATE KEY|api[_-]?key|access[_-]?token|secret|cookie' .

# 检查不应进入仓库的大文件和媒体素材
find . -type f -size +1M -print

# 检查 Skill 基础结构
python /path/to/skill-creator/scripts/quick_validate.py .
```

发布前还应确认：

- 仓库名称与 `SKILL.md` 中的 `name` 一致；
- `agents/openai.yaml` 的显示名称、描述和默认提示仍与 Skill 一致；
- README 中的 GitHub 地址与实际仓库地址一致；
- Git 提交只包含发布包文件，没有课程素材和运行产物；
- GitHub 仓库说明明确写明 `Noncommercial`，不要选择会暗示允许商用的许可证标签；
- 创建首个稳定 tag 前，在一台新环境中完成依赖安装与 Skill 校验。
