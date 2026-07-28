# 包装基线契约

包装层独立于 MG 层。用户要求改变 MG 风格时，保持本文件的章节牌、进度条和字幕规格。

## 必需配置

`mg-placement-plan.v1.json` 必须包含：

```json
{
  "package_style": {
    "profile": "sample-classic-v1",
    "chapter_header": {
      "enabled": true,
      "position": "top-left"
    },
    "progress": {
      "enabled": true,
      "left_px": 46,
      "right_px": 46,
      "bottom_px": 28,
      "height_px": 30,
      "show_labels": true,
      "label_layer": "ass-only",
      "mode": "continuous-cumulative",
      "segment_by_chapter_duration": true
    },
    "captions": {
      "enabled": true,
      "single_layer": true
    }
  }
}
```

`sample-classic-v1` 不允许关闭章节牌、进度条或字幕，不允许把进度条降到 24px 以下。轨道内显示短章节标签，但只能由 ASS 绘制一次；`Package.tsx` 不画标签。

## 固定视觉结构

- 章节 pill：左 42px、上 38px；深色渐变背景、14px 圆角、5px 章节强调色；显示 `CHAPTER i/N` 和标题。
- 进度轨道：左/右 46px、底部 28px、高 30px；连续圆角深色底轨、2px 浅边框。
- 进度填充：位于底轨内部，上下保留 2px；从全片 0 秒累计向右，不按章节归零。
- 章节分隔：按章节时长比例计算；不受标题长度影响。
- 字幕：底部 96px，单套字幕，不与进度轨道重叠。

## 绘制顺序

1. 人像与 MG 合成底片。
2. 章节底轨。
3. 累计进度填充。
4. 章节 pill。
5. ASS 进度标签与字幕。

不要把填充放到底轨下方，否则半透明底轨会把填充压暗；不要同时在 `Package.tsx` 和 ASS 里画标签，否则会出现双字、重影和重叠。长标题使用 `short_label`，极窄章节退回数字。

## 验收

至少保存以下全尺寸证据帧：

- 开头 0.15 秒；
- 每章开始后 0.15 秒；
- 中段；
- 结尾前 0.25 秒。

逐帧确认章节 pill 可读、进度轨道高度明显、章节分段总数正确、填充单调向右、字幕只有一套。
