# 污水处理厂流程视频：1080p 快速交付版

本目录保存已完成的成片、实际渲染参数和验收证据。成片文件使用 Git LFS；克隆后运行 `git lfs pull`。

- 成片：[wwtp-process-4m30s.mp4](wwtp-process-4m30s.mp4)，380,647,127 字节。
- 1920×1080、H.264、24 fps、270 秒、6480 个输出帧，保留中文字幕和片尾 CC BY 署名，无配音和背景音乐。
- 工程：`../../blender/plant_film.blend`，来自 `c42f5eb12e210999127cc336ad3daf45ed7a2907`，本次未改模型、未重建工程。
- 用户将交付要求调整为“1080p、半小时优先”，并同意简化光影与补帧。因此采用 **EEVEE、4 samples、隔帧渲染**，不是原定的 Cycles 4K／192 samples 正式高质量版本。
- 实际渲染 3257 帧：每镜头按 12 fps 取样，并额外保留镜头末帧；在同一镜头内线性混合补齐至 6480 帧，再叠加对应的清晰中文字幕。不会跨镜头混合；这不是光流补帧，可能有重影、锯齿和低采样噪点。
- 本次设备为 RTX 4080 Laptop GPU、Blender 5.2.2 LTS、Python 3.12、Pillow 12.3。渲染约 18 分 10 秒，渲染、补帧、编码和检查合计 **1532 秒（25 分 32 秒）**。该时长是本机实测，不是其他设备的性能保证。

## 验收与证据

- `settings.json`：生成成片时保存的原始参数及模型、配置文件 SHA256。`fast_render` 中的 OptiX 降噪字段是共用 Cycles 设置；本片实际使用 EEVEE，**没有应用 Cycles／OptiX 降噪**。
- `validation.json`：全片渲染后检查；无缺失贴图、无失效驱动，93 个运动对象有变化，32 项水体隐藏检查通过。`rendered_frames` 是 3257 个实际渲染帧号，不是最终视频帧数。
- `completion.json`：去除本机绝对路径后的成片验收记录。所有字幕 PNG 的完整性检查通过；FFprobe 实际解码计数 6480 帧、270 秒、1920×1080、24 fps；FFmpeg 全片解码检查退出码 0。
- `qa/`：EEVEE 快速配置的 34 张预览联系表、参数和检查记录。QA 使用 17% 尺寸；仅用于资源和镜头检查。

## 复现与续跑

在 `WWTP-Blender` 下，安装 `requirements-film.txt`，准备 Blender 5.2.2 LTS、含 libx264 的 FFmpeg 和 FFprobe。使用独立输出目录，避免混入其他参数的帧。

```bash
python scripts/render_film.py --qa --engine BLENDER_EEVEE --device OPTIX --fast-render --scale 50 --samples 4 --frame-step 2 --output renders/film-eevee-qa
python scripts/render_film_pipeline.py --output renders/film-1080p-fast --blender blender --ffmpeg ffmpeg --ffprobe ffprobe
```

Windows 用户可将 `--output` 指向有足够空间的非系统盘；运行器会将自身及子进程的临时目录和渲染缓存重定向到该输出目录下的 `.runtime/`。本次实际输出位于用户指定的非系统盘；这里不提交个人安装路径。

也可直接分阶段执行原渲染入口：

```bash
python scripts/render_film.py --engine BLENDER_EEVEE --device OPTIX --fast-render --scale 50 --samples 4 --frame-step 2 --output renders/film-1080p-fast
python scripts/render_film.py --encode --engine BLENDER_EEVEE --device OPTIX --fast-render --scale 50 --samples 4 --frame-step 2 --encode-preset veryfast --output renders/film-1080p-fast
```

重复同一渲染命令可续跑。对于隔帧渲染，应保持相同镜头／帧区间与全部质量参数；修改帧区间可能改变采样相位，应使用独立目录。编码采用 libx264、veryfast、CRF 17、yuv420p，已有 MP4 不覆盖。

原始 `.blend`、素材、字幕 PNG、配置和构建脚本仍在各自的工程目录中。中间帧、测速输出、缓存、个人路径运行器未提交；它们不是可移植交付的一部分。资产许可及署名要求继续适用，见 [ASSET_LICENSES.md](../../docs/ASSET_LICENSES.md) 和 [ASSET_MANIFEST.json](../../docs/ASSET_MANIFEST.json)。
