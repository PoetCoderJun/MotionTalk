# 规划

先完成明确气口选择与 [音频准备](00-audio.md)。主时间线是 prepared/narration.wav 和内部 final.srt；用户不必提供视频/SRT。

逐步解决 layout、idea、materials、style、references；可选项为空时写 none / []。无人物视频可做全屏 DOM/SVG；参考可访问则分析表达，不复用未经许可的资产。依据转写组织论点、演示、比较和视觉推进，不照每句重复标题卡。

生成 MG导演脚本.md 与 mg-placement-plan.v1.json。结构例见 [plan.json](../examples/plan-validation/plan.json)：source.audio/subtitles 是内部产物，duration_seconds 来自实际音频；audio_preparation.trim_breaths 必须明确 yes/no，可另记录准备报告路径。creative_brief 解决版式、创意、素材和风格，references 可空。visual_direction/package_direction 是具体创意说明，render_spec 决定画布与帧率。

cues 从零连续覆盖，边界在帧网格上，最后一帧为音频时长的帧舍入。草案 status=draft/approved=false；批准后 status=approved/approved=true，记录 approval_text。已获无人值守授权则引用原文继续。

```bash
python3 <skill-root>/scripts/validate_plan.py --plan "$plan"
```

验证只检查结构和时间，不认证批准身份或创意质量。未获授权不伪造审批；超出授权才重新规划。批准后按 [制作](02-build.md) 连续执行。
