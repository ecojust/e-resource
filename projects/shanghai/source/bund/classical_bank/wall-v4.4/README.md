# 汇丰与华俄道胜银行：v4.4 连续结构墙壳

> **15号当前发布须在本墙阶段后继续运行 [curtain-v4.4](../curtain-v4.4/README.md)。本包15号的94,288 / 46,138三角及原SHA仅为墙阶段输出。结构保留证明截至该阶段仍成立；后续C单独记录580个窗帘三角朝向修正和1,440个内部穿插fold三角删除，不将新哈希冒充墙阶段输出。**

本阶段修正既有墙体由闭合盒体拼接造成的内部反向重合面与 T 接缝。只替换可在原生成器中精确识别的结构墙壳，不做全楼布尔、不删整条窗洞侧壁，不改变建筑定位和设计尺寸。两栋修后模型的实际浏览器同机位比较由项目发布流程另行记录；本包的 JSON 检查报告分别列出静态、原生文件和导出验证范围。

**12号顺序必须是：固定13fa基线 → [photo-v4.4六窗采样](../photo-v4.4/README.md) → 本目录墙壳修复。** 六窗脚本直接使用固定基线，不能在墙壳修复后再次运行并当作最终结果。

**15号最终顺序是：固定13fa原生基线 → 本目录墙壳修复 → [curtain-v4.4](../curtain-v4.4/README.md)。** 本阶段不增加照片纹理，不改变原窗帘、玻璃、窗框、柱或拱饰。

## 精确范围与方法

生成器 `../build_classical_banks.py` 的 `Builder.bay` 先创建四片围绕开孔的结构墙，再创建窗、窗框与装饰。捕获器在 `bay` 开始到第一次 `window` 调用前取得结构面；另捕获 `roof_and_other_walls` 中 .62m 厚的无窗短墙和15号的侧墙顶部扩展。每个被选面都必须与输入原生网格的顶点和面序精确匹配，否则终止。材质同名的石柱、鼓座装饰、檐口和其他物件不因此被盲目选中。

按相同立面方向、前平面与墙厚分组，取原有正面区域的二维并集，保留矩形与曲线洞口。使用 1e-8m 精度网格与带约束 Delaunay 三角剖分；前后表面共用完整节点，仅沿三角网格真正的边界边挤出侧壁。因此相邻实墙之间不再生成内部侧面，真实外边和孔边仍有厚度。不同退进深度不合并，15号中央三开间的 .32m 退进保留。

- 汇丰：530个带窗墙单元、15段无窗短墙，26个平面/深度组；531个开孔包括530个窗/门洞及中央柱廊的大开口。13,023个旧结构墙面替换，101,083个其余原面和141,647个原顶点逐项保留。六窗的30块照片玻璃与39个主框构件在独立对象中保持顶点、面、材质与UV不变。
- 华俄道胜银行：96个带窗单元、3段侧墙顶部扩展，5个平面/深度组，96洞。3,032个旧结构墙面替换，48,025个其余原面和57,572个原顶点逐项保留。拱窗曲线、柱廊、原窗帘和窗框不变。

二维并集与原墙区域的最大对称差为汇丰1.88e-6㎡、华俄道胜8.01e-7㎡，来自1e-8m精度处理；坐标写入原生文件仍为FLOAT32。所有新墙组闭合、边方向一致，体积与区域面积×原厚度一致。墙体射线检查分别为1,590次和288次，修前修后都不遮挡原洞口。实际raw的墙深度组反向内部接触对分别从10,158与1,836降为0；此统计只指捕获的结构墙组，不表示所有装饰构件都没有接触或交叠。

## 当前资产与历史报告

| 建筑 | 近景 raw / web 三角形 | 远景三角形 | 当前发布位置 |
|---|---:|---:|---|
| 12号 | 218,805 | 130,375 | `assets/models/bund/bund12.glb`、`assets/models/bund/web/bund12.glb`、`assets/models/bund/lod-v4/bund12.glb`、`assets/native/bund/bund12.blend` |
| 15号（仅墙阶段） | 94,288 | 46,138 | 中间输出；最终发布另见 curtain-v4.4 |

本墙阶段的结构保留证明为本目录 `bund12-native-preservation.json` / `bund15-native-preservation.json`，以及 `bund12-wall-clean-validation.json` / `bund15-wall-clean-validation.json`。导出、图片、FLOAT32属性、尺寸与SHA见 `bund12-export-clean-validation.json` / `bund15-export-clean-validation.json`。本目录不重复复制最终模型文件。

`../photo-v4.4/model-validation.json`、`export-validation.json`、`geometry-uv-validation.json` 是**墙修复前的六窗阶段历史证据**。其中“未选中三角形全部不变”、230,205三角形和旧GLB/native SHA只适用于该中间阶段，不能继续作为当前最终模型的保留声明。照片像素坐标与30块pane UV仍有效，本阶段没有修改原JPEG、照片UV或主窗框。

汇丰近景仍只嵌入Suicasmo的5184×3456 CC0原JPEG，SHA `bbb15e71ba67f99daab1aa2827494db9c6af6f9b349a2f4ccea6f6609c9ec684`；完整来源与EXIF见前置照片包。原图位于 `assets/references/bund/hsbc-20250501-original.jpg`，源码不重复复制。汇丰远景不嵌照片，玻璃明确为蓝灰底色；15号所有变体都没有图像纹理。full web采用 `-cc -noq -km -ke`，远景另加 `-si 0.35 -se 0.002 -sp`；压缩后恢复GLB归属元数据。所有文件低于100,000,000B。

## 重建

验证环境：Blender 4.3.2、Python+numpy、Shapely 2.2.0（需要 `constrained_delaunay_triangles`）、gltfpack 1.3。不同版本可能改变三角剖分顺序或Blender序列化结果，应重跑检查而非宣称文件SHA必然相同。辅助脚本均通过显式路径参数工作，不依赖 `/workspace`。

先按[照片阶段说明](../photo-v4.4/README.md)生成汇丰的 `bund12-photo.blend` 与 `bund12-photo-raw.glb`。照片阶段使用固定13fa基线的公开下载URL与SHA；请勿用已经修复的当前发布原生文件替代旧基线。

在项目根目录执行，`WALL_WORK` 可换成任意输出目录：

```sh
PROJECT_ROOT="$PWD"
WALL_SRC="$PROJECT_ROOT/source/bund/classical_bank/wall-v4.4"
PHOTO_SRC="$PROJECT_ROOT/source/bund/classical_bank/photo-v4.4"
WALL_WORK=/tmp/bund-wall-v4.4
mkdir -p "$WALL_WORK/bund12" "$WALL_WORK/bund15"

blender -b -t 1 --python "$WALL_SRC/capture_wall_shells.py" -- --project "$PROJECT_ROOT" --building bund12 --input "$PHOTO_SRC/bund12-photo.blend" --output "$WALL_WORK/bund12/captured-wall-shells.json"
python "$WALL_SRC/union_wall_shells.py" --capture "$WALL_WORK/bund12/captured-wall-shells.json" --output "$WALL_WORK/bund12/wall-union-mesh.json"
blender -b -t 1 --python "$WALL_SRC/apply_wall_union.py" -- --input "$PHOTO_SRC/bund12-photo.blend" --capture "$WALL_WORK/bund12/captured-wall-shells.json" --union "$WALL_WORK/bund12/wall-union-mesh.json" --output-dir "$WALL_WORK/bund12" --credit-glb "$PHOTO_SRC/bund12-photo-raw.glb"
blender -b -t 1 --python "$WALL_SRC/export_geometry_lod_source.py" -- --input "$WALL_WORK/bund12/bund12-clean.blend" --output "$WALL_WORK/bund12/bund12-clean-lod-source.glb"
python "$WALL_SRC/finalize_clean_assets.py" --project "$PROJECT_ROOT" --gltfpack /absolute/path/to/gltfpack --directory "$WALL_WORK/bund12" --building bund12
blender -b -t 1 --python "$WALL_SRC/verify_native_preservation.py" -- --before "$PHOTO_SRC/bund12-photo.blend" --after "$WALL_WORK/bund12/bund12-clean.blend" --capture "$WALL_WORK/bund12/captured-wall-shells.json" --output "$WALL_WORK/bund12/native-preservation.json"
python "$WALL_SRC/audit_wall_contacts.py" --project "$PROJECT_ROOT" --raw "$WALL_WORK/bund12/bund12-clean-raw.glb" --capture "$WALL_WORK/bund12/captured-wall-shells.json" --output "$WALL_WORK/bund12/all-wall-contacts-after.json"
```

15号固定原生基线的SHA为 `9b3a576b10d69202666be4bb8e5e4089739a279f9f471afc38e508065121b76b`，raw基线为 `46b4b1f9c35c4afaa15d11f037d3a23651fdb23f47aea3c2a892464b65208027`；下载URL也记录在 `baseline-source.json`：

```sh
curl --fail --location 'https://raw.githubusercontent.com/ecojust/e-resource/13fa900f8559b1c38154178d3af54e4d0591a5d3/projects/shanghai/assets/native/bund/bund15.blend' --output "$WALL_WORK/bund15/baseline.blend"
curl --fail --location 'https://raw.githubusercontent.com/ecojust/e-resource/13fa900f8559b1c38154178d3af54e4d0591a5d3/projects/shanghai/assets/models/bund/bund15.glb' --output "$WALL_WORK/bund15/baseline.glb"
blender -b -t 1 --python "$WALL_SRC/capture_wall_shells.py" -- --project "$PROJECT_ROOT" --building bund15 --input "$WALL_WORK/bund15/baseline.blend" --output "$WALL_WORK/bund15/captured-wall-shells.json"
python "$WALL_SRC/union_wall_shells.py" --capture "$WALL_WORK/bund15/captured-wall-shells.json" --output "$WALL_WORK/bund15/wall-union-mesh.json"
blender -b -t 1 --python "$WALL_SRC/apply_wall_union.py" -- --input "$WALL_WORK/bund15/baseline.blend" --capture "$WALL_WORK/bund15/captured-wall-shells.json" --union "$WALL_WORK/bund15/wall-union-mesh.json" --output-dir "$WALL_WORK/bund15" --credit-glb "$WALL_WORK/bund15/baseline.glb"
python "$WALL_SRC/finalize_clean_assets.py" --project "$PROJECT_ROOT" --gltfpack /absolute/path/to/gltfpack --directory "$WALL_WORK/bund15" --building bund15
blender -b -t 1 --python "$WALL_SRC/verify_native_preservation.py" -- --before "$WALL_WORK/bund15/baseline.blend" --after "$WALL_WORK/bund15/bund15-clean.blend" --capture "$WALL_WORK/bund15/captured-wall-shells.json" --output "$WALL_WORK/bund15/native-preservation.json"
python "$WALL_SRC/audit_wall_contacts.py" --project "$PROJECT_ROOT" --raw "$WALL_WORK/bund15/bund15-clean-raw.glb" --capture "$WALL_WORK/bund15/captured-wall-shells.json" --output "$WALL_WORK/bund15/all-wall-contacts-after.json"
```

源码不自动覆盖正式assets。若输入已清理或与源生成器不同，精确面匹配会失败，不能忽略该失败继续导出。空间源数据、照片与原有几何解释仍遵循上游包的许可与精度限制；本次墙拓扑修复没有补充测绘精度或未观察的建筑细节。
