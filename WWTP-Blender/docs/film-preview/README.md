# 返修预览与验证

本目录对应 `plant_film.blend`，文件 SHA256 见 settings.json。Blender 5.2.2 LTS、Cycles CPU、12 samples、17% 尺寸，均为预览。

- screens.jpg：粗、细格栅带水与隐藏水体；外围池壁封闭，内槽连续。
- meter.jpg：两条长喉计量渠带水与隐藏水体。
- contact.jpg：17 段镜头各两帧，共 34 张；已逐页查看。
- screen-water-transition.mp4：粗格栅第 577–600 帧连续显隐过渡，24 fps，共 1 秒；过渡取帧见 transition.jpg。
- validation.json：93 个运动对象有变化，无失效驱动、无缺失贴图；32 项水体隐藏检查通过。
- transition-validation.json：连续片段的独立检查记录。

另见 ../FILM_DRAWING_VALIDATION.json 的 25 项保存后检查（含八个角墙、两条 1.50 m 喉宽）、../FILM_PIPE_PORTS.json 的无阻挡中心线检查，以及 ../FILM_DRAWING_REVIEW.md 中的图纸依据与假定。上述预览不替代完整 4K 长片的渲染和闪烁验收。
