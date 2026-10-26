# Bund12 汇丰银行：右翼六窗照片阶段（墙修复前）

> **阶段归档说明：** 本目录生成的是墙拓扑修复前的六窗照片阶段。当前发布模型必须随后执行 [wall-v4.4](../wall-v4.4/README.md)。本页230,205三角形及原有“未选中几何不变”报告只对应中间阶段，不能作为当前墙修复后218,805三角形模型的保留声明。原JPEG、30块照片pane与39个实体主框未被墙修复改变。

这是现有汇丰完整模型的局部修改副本，处理面向黄浦江正立面北侧翼楼第 2–4 窗轴、两排共六窗。没有替换整面墙，也没有把照片中的树、路灯或行人投到建筑上。本包记录局部生成与静态、Blender验证；网页运行验证另见项目发布报告。

## 本阶段重建输出（非最终墙修复版本）

- `bund12-photo-raw.glb`：完整近景模型，230,205 个三角形；其中新增六窗使用 30 块独立校准的玻璃面与 39 个实体主框构件。
- `bund12-photo-web.glb`：同几何、同原图，meshopt 压缩；POSITION/NORMAL 保持 FLOAT32，不使用 KHR_mesh_quantization。
- `bund12-photo.blend`：可编辑完整模型，原照片已打包。基线墙、柱、穹顶、窗洞、石缝及所有未选中窗均保留。
- `bund12-geometry-lod.glb`：基于修改后几何生成的远景版本，145,059 个三角形；不含照片、不含任何 image/texture。玻璃保留普通蓝灰色 `(0.075, 0.14, 0.16)`，不是去掉 map 后的白片。
- `bund12-geometry-lod-source.glb`：无图、未简化的远景生成源。
- `six-window-front.png`、`six-window-oblique.png`：Blender 实际正视与斜视渲染。`six-window-before.png` 用相同相机、光照和采样展示基线。`calibration-preview.png` 是六个窗四角 UV 的校准渲染，用于量取主框位置，不是另行生成的纹理。

所有照片窗面共用唯一一张 JPEG 和唯一一个纹理。5184×3456 RGBA 加 mip 的估计 GPU 占用为 95,551,488 B；远景模型不重复占用此纹理。运行端应在远景切换并卸载近景模型时释放该纹理。此目录没有修改运行端的资源生命周期。

## 原图与授权

Suicasmo，2025-05-01，**CC0-1.0**。

- 文件页面：<https://commons.wikimedia.org/wiki/File:HSBC_Building,_Shanghai_20250501-1.jpg>
- 许可：<https://creativecommons.org/publicdomain/zero/1.0/>
- 5184×3456 原 JPEG：`hsbc-20250501-original.jpg`，7,580,249 B。
- SHA256：`bbb15e71ba67f99daab1aa2827494db9c6af6f9b349a2f4ccea6f6609c9ec684`。
- `photo-source.json` 含原下载 URL、作者、许可、源 metadata 哈希、EXIF IFD/GPS IFD；EXIF Orientation=1，Canon EOS M2，DateTime=2025:05:01 08:51:18。
- `photo-upstream-metadata.json` 保留既有 Commons imageinfo 原记录。

原 JPEG 没有改像素、旋转、裁切、缩放或重新压缩；近景 raw/web 的 GLB 内嵌 image bufferView 字节 SHA 与原 JPEG 完全一致。校准预览是从原图 UV 渲染的检查图，未作为纹理使用。GLB `asset.copyright` 及照片节点 extras 同时保留来源；压缩后已重新写回归属信息，因为 gltfpack 默认不保留 asset.copyright。

## 观察、实现与推定

照片中六窗无遮挡。每窗有中央双扇主框；上排有一个接近上方三分之一处的粗横框，下排有两个主要横框。可辨识细装饰格栅、浅色帘布和不同的玻璃反射。原模型使用三等分竖框与统一 0.48/0.77 横档，未对应这些观察。

`calibration.json` 记录每窗四个原像素角点以及照片粗框中心线估计；`panes.json` 记录每块玻璃的四个原像素角点和实体窗口内的归一化范围。每个玻璃小面各自做透视映射，粗框像素留在取样范围之外，再以真实几何补上主框，避免两套明显错位的粗框。玻璃面采用 6×6 网格逼近逐面投影，嵌于原有 0.57 m 深度的窗洞中。玻璃实体厚 45 mm；窗框延续原模型的深度范围。

实际测量范围仅是照片中的像素。窗洞实体尺寸、0.105/0.12 m 框宽、0.11 m 横框高与主横框的归一化位置仍属现有尺度上的近似，不是现场测绘。窗体的全楼位置不做摄影测量声明。细装饰格栅和室内帘布仍是照片细节，**没有宣称全部格栅或室内均已建成三维**。照片反射固定为拍摄时状态，没有另加全场环境反射。

所有新材质以 `PhotoFacade_` 开头；近景照片玻璃 roughness=0.76、metallic=0、specular IOR level=0.10，不使用自发光。运行端应跳过通用石材 grain、再次 UV 重映射和额外玻璃环境反射。其余原材质名保持不变。

这一样板只改六窗。局部石墙照片映射暂不实施，因为现有真实石缝需要另行逐块配准；没有将不对齐的照片石缝覆盖到墙上。2025 年照片只能证明拍摄时的帘布、玻璃与使用状态；未核验此后是否换窗或翻修。主体历史建筑体量沿用已有模型来源。

## 验证

`model-validation.json` 来自 Blender 的实际原生网格比较：141,647 个基线顶点坐标逐项不变，仅移除六窗的 336 个原玻璃/细框面，114,106 个其余面顶点顺序与材质索引逐项不变，所有结构面保留。

`export-validation.json` 另从原始 raw GLB 和新 raw GLB 解析世界坐标，比较全部未选中三角形，包括未选中的玻璃和窗框；坐标比较精度为 10 微米。另核验近景原图字节哈希、单 image/texture、远景无图且玻璃有明确底色、三角形数、边界差、FLOAT32 属性和每文件低于 100,000,000 B。`geometry-uv-validation.json` 还从新 raw 解析 3,038 个替换顶点，确认全部落在六个原窗洞范围内、深度不超原范围、照片正面法线朝外；逐格检查 UV 投影逼近误差最大 0.0661 个原图像素。只报告静态及 Blender 验证，未声明浏览器通过。

## 可公开取得的基线与重现

已发布基线 commit 为 `13fa900f8559b1c38154178d3af54e4d0591a5d3`，仓库 `ecojust/e-resource` 中的项目位于 `projects/shanghai`。本源码不复制基线的大文件；两个固定下载地址已用 HTTP HEAD 核验返回 200，记录见 `baseline-url-check.json`。

- [基线 raw GLB](https://raw.githubusercontent.com/ecojust/e-resource/13fa900f8559b1c38154178d3af54e4d0591a5d3/projects/shanghai/assets/models/bund/bund12.glb)，SHA256 `6b60b1d06932d8ddb2a46fafbc62bff50c07dcdfe5bbf401f4a870eb383444d2`。
- [基线 Blender](https://raw.githubusercontent.com/ecojust/e-resource/13fa900f8559b1c38154178d3af54e4d0591a5d3/projects/shanghai/assets/native/bund/bund12.blend)，SHA256 `0b2b427c25ae49fb18a303718c4ba679f913a3ad8e8721d07f5acb84a13cb9e2`。

`baseline-source.json` 保存完整机器可读 URL 与 SHA。生成器在读入前强制核对两项基线 SHA，避免对已替换的照片版重复施加修改。近景资产集成后，应使用这里的固定基线，不能再把当前项目内的 bund12 作为旧模型输入。

发布源码目录为 `source/bund/classical_bank/photo-v4.4/`；原 JPEG 单独保存在项目的 `assets/references/bund/hsbc-20250501-original.jpg`，源码不再重复复制此 7.58 MB 文件。原图路径可以用 `--photo` 指定；不指定时，生成器会先探测 `--project` 的上述引用目录，再尝试源码目录旁同名原图，兼容独立 staging 包。

在本源码目录运行，下列 `PROJECT_ROOT` 指向项目目录而非仓库最上层：

```sh
PROJECT_ROOT=/absolute/path/to/e-resource/projects/shanghai
BUND12_BASELINE=/tmp/bund12-pinned-baseline
mkdir -p "$BUND12_BASELINE"
curl --fail --location 'https://raw.githubusercontent.com/ecojust/e-resource/13fa900f8559b1c38154178d3af54e4d0591a5d3/projects/shanghai/assets/models/bund/bund12.glb' --output "$BUND12_BASELINE/bund12.glb"
curl --fail --location 'https://raw.githubusercontent.com/ecojust/e-resource/13fa900f8559b1c38154178d3af54e4d0591a5d3/projects/shanghai/assets/native/bund/bund12.blend' --output "$BUND12_BASELINE/bund12.blend"
python measure_panes.py --photo "$PROJECT_ROOT/assets/references/bund/hsbc-20250501-original.jpg"
blender -b --python build_sample.py -- --project "$PROJECT_ROOT" --baseline-native "$BUND12_BASELINE/bund12.blend" --baseline-raw "$BUND12_BASELINE/bund12.glb" --render
python finalize_assets.py --project "$PROJECT_ROOT" --baseline-raw "$BUND12_BASELINE/bund12.glb" --gltfpack /absolute/path/to/gltfpack
python check_sample_geometry.py --project "$PROJECT_ROOT"
```

`--project` 是必填参数，不使用任何 `/workspace` 默认路径。`finalize_assets.py` 的 `--gltfpack` 也是必填。生成器只在本源码目录输出副本，不覆盖主项目 assets。Blender、Python+numpy/Pillow 与 gltfpack 是重建依赖；Blender 原生文件已打包照片，无需依赖作者机器上的绝对图片路径。渲染是检查材料，不能据此声明摄影测量级准确度。

## 发布文件对应

上述输出名是照片阶段中间产物；必须经wall-v4.4处理后，才对应下列最终发布位置。源码目录不重复保存最终模型：

| 生成输出 | 项目相对路径 |
|---|---|
| bund12-photo-raw.glb | assets/models/bund/bund12.glb |
| bund12-photo-web.glb | assets/models/bund/web/bund12.glb |
| bund12-photo.blend | assets/native/bund/bund12.blend |
| bund12-geometry-lod.glb | assets/models/bund/lod-v4/bund12.glb |

bund12-geometry-lod-source.glb为可重建的中间产物。原照片在assets/references/bund/hsbc-20250501-original.jpg，仅保存一份外部源图；近景GLB与Blender内部另外嵌入原图。
