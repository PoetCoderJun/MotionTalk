[English](README.md) · **简体中文**

# MotionTalk

**从一段音频，到完整社交视频。**

提供音频文件，可选素材文件夹。MotionTalk 内部完成转写与匹配字幕，先询问是否智能剪气口，再与你逐步确定创意、视觉叙事并通过 Hyperframes 输出 MP4。不要求人物视频或用户准备的 SRT。

按 [CC BY-NC-SA 4.0](LICENSE.md) 供非商业使用；商业用途须事先书面授权。第三方材料保留自身许可。

## 开始使用

```bash
npx skills add PoetCoderJun/MotionTalk
```

在可读本机文件/图片、执行命令的 Agent 中说：

```text
用 $motiontalk，把 /data/my-audio.wav 做成一条完整社交视频，
用画面解释录音里的观点。可选素材在 /data/materials。
```

没有明确气口选择时 Agent 必须问。选择剪：结合试听与词级时间戳，只将审核确认的气口默认压到 0.25 秒；不把词间空隙一律当气口，保留思考与强调停顿。选择不剪：保持原时间线。口头填充词、口误、重说不包含在气口授权内。

接着逐步沟通发布版式、核心创意、可选素材/B-roll、风格和可选参考片。参考可访问时分析表达，不复制未经许可的画面或音乐。没有参考或素材也可继续。通常批准具体导演计划后制作；明确无人值守授权时可连续完成。发布仍由你决定。

<a id="作者自用案例"></a>

## 交付与作品

交付完整 MP4、准备音频与内部 SRT、采样区间剪辑报告、导演计划、可编辑 HTML/CSS/GSAP 工程及技术检查报告。初始化生成的是 scaffold，仍需实际视觉制作；几张标题卡与渲染成功不等于创意验收。

### Vibe Working：图解与屏幕演示

![作者既有成片：工作流程图、人物和屏幕演示，6倍速](assets/examples/vibe-working-6x.gif)

摘取《每一个没Vibe Working过的好朋友我都跟她急》**00:39–01:27**，以 **6 倍速**展示，约 8 秒。

### 具身话题：随论证展开的图解

![作者既有具身话题成片：图解逐步展开，配合字幕与人物画中画，6倍速](assets/examples/embodied-correction-6x.gif)

摘取《具身智能-数采纠正-清晰人声版》**最后 30 秒**，以 **6 倍速**展示，约 5 秒。

以上为作者既有成片的无声 GIF 摘录，不是本次音频优先版本的端到端验证。

**[更多示例视频 · 小红书「诗人程序员Jun.AI」](https://www.xiaohongshu.com/user/profile/5b40fe744eacab72c9f480ef)**

## 环境、数据与限制

需要 Python 3.10+、FFmpeg/ffprobe、Node >=22、本机完整 Google Chrome。安装 Skill 后在其目录安装已审阅依赖：

```bash
python3 -m pip install -r requirements.txt
npm ci
```

lockfile 固定 Hyperframes 0.8.30、GSAP 3.14.2。内置 DashScope ASR 需配置（包括 DASHSCOPE_API_KEY）与上传／费用明确授权：音频代理上传服务，异步轮询并下载转写结果，不是离线 ASR。本地渲染不意味着全流程本地，Agent 服务自身的数据处理也适用。详见 [音频准备](references/00-audio.md)。

默认单 worker 和硬件 H.264；硬件不合适时可明确选软件模式，不自动下载浏览器或升级运行时。可选组件与资产安装前核对来源和许可。

ASR 可能错字、错时间；气口处理依赖真实试听与可用词级时间戳，不是自动气口检测。拼接边界可能需人工细修。不剪路径保留时间线但归一化容器与采样率。技术检查涵盖结构、剪辑映射、字幕、尺寸、编码和时长；连续视觉审查与试听另行记录。批准/验收状态不是身份签名，脚本不验证证据真假。不声明客户、部署业绩或耗时成本收益。

## 工程与兼容

阅读 [Harness 工程案例](docs/harness-case-study.md)。安装依赖后运行：

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s scripts/tests -v
node --test tests/*.test.mjs
python3 examples/plan-validation/run.py
```

测试使用合成输入／mock 服务结果，不调用云模型；[音频渲染样例](examples/audio-only-smoke/README.md) 是技术验证，不是创作者展示。

[clean-talking-video](https://github.com/PoetCoderJun/clean-talking-video) 原视频剪辑流程继续保留，[Minutes](https://github.com/PoetCoderJun/dingtalk-style-minutes) 既有依赖不变。无删除或归档。见 [迁移说明](docs/audio-first-migration.md)、[第三方许可说明](THIRD_PARTY_NOTICES.md)。根许可证未改，商业用途仍须事先书面授权。
