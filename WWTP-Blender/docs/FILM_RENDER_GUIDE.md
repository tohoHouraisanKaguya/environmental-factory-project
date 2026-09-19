# 水厂流程电影：跨终端渲染说明

本次交付是可渲染工程，不是已渲完的长片。17 段镜头共 6480 帧，24 fps，4 分 30 秒。默认 3840×2160、Cycles 192 samples、自适应阈值 0.015、AgX、降噪。镜头从鸟瞰沿主工艺水路推进，包含鼓风机房、泵、带水运行与隐藏水体的机构展示。中文名称由附带 PNG 叠加，无需在渲染机安装中文字体。

## 获取工程

安装 Git LFS 后克隆仓库。在仓库根目录运行：

```bash
git lfs install
git lfs pull
cd WWTP-Blender
python -m pip install -r requirements-film.txt
```

Blender 采用本次验证的 **5.2.2 LTS**。另需 Python 3.10+ 和 FFmpeg（只在合成 MP4 时需要）。`blender` 和 `ffmpeg` 可加入 PATH，或分别用 `--blender`、`--ffmpeg` 指定可执行文件。Windows PowerShell 中路径含空格请加引号。

`blender/plant_film.blend` 是电影工程；纹理与 HDR 已打包。`plant_environment_outfall.blend` 是构建输入检查点。早期 `plant.blend` 保留不动，不是本次渲染入口。新增两个文件使用 LFS；没有迁移旧文件历史。

## 先试渲

```bash
python scripts/render_film.py --blender blender --qa --device CPU
```

输出在 `renders/film-qa/`：每镜头两张 Cycles 预览、带中文字幕的图片、`contact.jpg` 和 `validation.json`。QA 用 17% 分辨率、12 samples，不能作为最终画质结论。

NVIDIA 建议先以 `--device OPTIX` 试渲；也支持 CUDA、HIP、METAL、ONEAPI。若所选后端没有可用 GPU，脚本会报错，不会静默回退到 CPU。

```bash
python scripts/render_film.py --qa --device OPTIX --output renders/gpu-qa
```

## 正式渲染与断点续跑

```bash
python scripts/render_film.py --device OPTIX
```

CPU 可用 `--device CPU`。按镜头或帧区间拆分任务：

```bash
python scripts/render_film.py --device OPTIX --shot coarse
python scripts/render_film.py --device OPTIX --start 1 --end 2160
python scripts/render_film.py --device OPTIX --start 2161 --end 4320
python scripts/render_film.py --device OPTIX --start 4321 --end 6480
```

重复同一命令会跳过已有且可解码的原始 PNG，再生成字幕版。损坏文件会改名为 `.corrupt.png` 并重新渲染。每个输出目录记录模型和参数哈希；更换模型、采样或分辨率必须改用新目录，避免混入旧帧。多台机器应分配**互不重叠的帧区间**，各自输出到独立目录，完成后汇总 `frames/`；不要让两台机器同时写同一帧。

默认原始图在 `renders/film/raw/`，字幕版在 `renders/film/frames/`。渲染程序必须经上述 Python 入口运行：直接在 Blender 按 Render Animation 不会叠加 PNG 中文标签。

降低分辨率/提高采样的例子：

```bash
python scripts/render_film.py --device OPTIX --scale 50 --samples 96 --output renders/1080p
```

## 合成视频

全部 6480 张字幕帧齐备后：

```bash
python scripts/render_film.py --encode
```

输出 `renders/film/wwtp-process-4m30s.mp4`，H.264、24 fps、CRF 17、yuv420p，无配音、无背景音乐。脚本检查缺帧和损坏图像，禁止把不完整序列冒充成片；已有 MP4 不覆盖。自定义输出目录时合成仍须带相同 `--output`、`--scale`、`--samples` 参数。

## 修改与重建

- `data/film.json`：镜头位置、目标、时长、显隐时间、演示速度。
- `data/film_hydraulics.json`：102 段管道的折点、管径、系统、工段连接关系和图纸依据。
- `scripts/build_film.py`：读取固定输入检查点，每次从头构建，不在上次结果上累加。
- `scripts/film_hydraulics.py`：生成空心连接管道、支座和土建开孔；drawing_revision.py 修正格栅、生化池方向和双长喉渠。
- `scripts/prepare_film.py`、`prepare_film_hydraulics.py`：用于重新生成默认参数；会覆盖各自 JSON，手动改过 JSON 后不要运行它们。

```bash
blender -b --factory-startup --python-exit-code 1 --python scripts/build_film.py
```

可用 `blender -b --factory-startup --python-exit-code 1 --python scripts/validate_film_drawing.py` 检查保存后的格栅角墙、计量渠实体喉宽和主线配置。

只有改字幕内容才需要 `python scripts/prepare_film.py --font /path/to/CJK-font.ttf`。已有字幕 PNG 直接可用。

## 展示假定与边界

这是课程设计的工艺演示模型。连接按用户提供的第二版总平面与管线图修正：外部主水线使用管道，格栅内部保留封闭集配水区；计量段为双长喉渠，喉宽各 1.50 m。图纸已标注 DN 的主干和支线按标注设置，未标管径及竖向标高为展示假定，尚未完成水力复算，不是施工图或 CFD。水面循环与流动材质属于视觉动画；排口是几何水流。正式水力标高统一仍需设计复核。

泵和鼓风机内部是通用叶轮示意，不能解释为 NX300 厂家真实内部。为解释动作，全部机组展示运转；不改变原设计四用两备。初沉与二沉机械动作加速并标注，旋转设备降速便于观察。隐藏水体表示观察状态，不表示无水工况允许设备实际运行。固定曝气器和管道不做不合理的整体旋转。

资产来源和修改记录见 `docs/ASSET_LICENSES.md` 与 `docs/ASSET_MANIFEST.json`。片尾保留鼓风机模型 CC BY 作者署名；再分发时须同时保留上述许可文件。

全片的最终高采样渲染、连续噪点/闪烁检查、4K 编码验收留在目标渲染终端执行。本机验证范围见随附 FILM_DRAWING_VALIDATION.json 和 film-preview 中的预览证据；不把低采样预览称为最终画质。
