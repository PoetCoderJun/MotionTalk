# 内部音频准备

用户只提供音频，可选素材目录；以下路径均由 Agent 管理。

## ASR

先记录气口 yes/no。内置 ASR 来自 clean-talking-video 的 DashScope 模块，需要有效配置和上传／费用授权。当前没有内置离线 ASR 模型，本地渲染不意味着转写全本地。未授权时不上传，可先推进创意沟通。

```bash
python3 <skill-root>/scripts/transcribe_audio.py --audio "$audio" \
  --output-dir "$output_dir/asr" --trim-breaths no --allow-cloud-asr
```

--trim-breaths 根据已记录选择填 yes/no；ASR 本身不剪音频。内部 transcript.json 含 segments 与词级时间戳。ASR 错字或时间误差仍需内容复核。配置包括 DASHSCOPE_API_KEY（也接受原模块别名）、DASHSCOPE_BASE_URL、DASHSCOPE_ASR_MODEL。代理 OGG 经服务上传接口发送、提交异步识别、轮询并下载结果；音频并非只留在本机。复用模块源码见 [transcribe.py](../scripts/vendor/clean_talking_video/transcribe.py)。

## 不剪

```bash
python3 <skill-root>/scripts/prepare_audio.py --audio "$audio" \
  --transcript "$output_dir/asr/transcript.json" --trim-breaths no \
  --output-dir "$output_dir/prepared"
```

保留时间线，转为 48 kHz/24-bit WAV，不加倍速、母带或删词。

## 智能剪气口

```bash
python3 <skill-root>/scripts/prepare_audio.py --audio "$audio" \
  --transcript "$output_dir/asr/transcript.json" --trim-breaths yes \
  --propose-gaps "$output_dir/gap-review.json"
```

候选默认未分类、未批准，不是气口检测结果。保留音频 SHA-256，逐个试听；仅确认的气口填 kind=breath、approved=true 和具体听审理由。思考与强调停顿保留；选中区间不能包含已标记词。无词级时间戳或无法试听时不批准自动剪辑。

```bash
python3 <skill-root>/scripts/prepare_audio.py --audio "$audio" \
  --transcript "$output_dir/asr/transcript.json" --trim-breaths yes \
  --reviewed-gaps "$output_dir/gap-review.json" --keep-gap 0.25 \
  --output-dir "$output_dir/prepared"
```

只压缩批准区间，目标间隙两端各保留一半；不剪填充词、口误或重说。采样网格确定删除区间，直接拼接不做改变时长的交叉淡化。ASR 词边界不准或剪口有声音时应调整并试听，脚本不能证明听感自然。

输出 narration.wav、transcript.json、final.srt、audio-preparation-report.json；剪气口时另保存所用 gap-review.json。报告保存源哈希、保留/删除的采样区间与时长；词和字幕共用同一映射，并保留源时间戳。SRT 毫秒、音频采样、画面帧网格精度不同，不将精确时间映射写成感知同步已自动验收。
