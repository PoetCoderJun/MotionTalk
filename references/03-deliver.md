# 正式渲染与交付

本阶段与制作处于同一次调用，不得再次请求确认。

## 正式渲染

使用 Skill 的薄渲染入口：

```bash
node <skill-root>/scripts/render_master.mjs \
  --project-dir "$output_dir/remotion" \
  --props "$output_dir/master-props.json" \
  --output "$output_dir/final/<project_id>-packaged.mp4"
```

入口默认使用 75% 可用并发和跨平台硬件回退，并通过 Remotion `bundle()`、
`selectComposition()` 和 `renderMedia()` 输出一次正式成片。只有在当前机器已经
完成编码器与权限预检时才显式覆盖硬件策略；不要把某个平台的编码器设为 Skill
前提，也不要另行编码包装层或生成第二条整片。

## 最终门禁

运行：

```bash
node <skill-root>/scripts/validate_master.mjs \
  --project-dir "$output_dir/remotion" \
  --plan "$output_dir/mg-placement-plan.v1.json" \
  --props "$output_dir/master-props.json" \
  --final "$output_dir/final/<project_id>-packaged.mp4" \
  --output-dir "$output_dir"
```

验证器按本项目 `render_spec` 检查尺寸、帧率、时长和音频 codec，并要求批准
计划中的每个 semantic invariant 都能在清单中找到对应证据帧。它还检查视觉、
包装和最终目录清洁度。

任何必检项失败都在同一次调用内修复并重验。只交付最终成片、导演脚本、计划和
`quality-report.v1.json`。
