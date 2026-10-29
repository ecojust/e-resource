# 六目标精确替换候选，仅 staging

`overrides/precise-buildings-v6.json` 包含05、06、07、09、14及青浦北大街222号六个独立 owner。`complete:true` 仅代表本目录的分组几何审计通过，不代表222的照片模型已通过视觉验收或这些资产已经装入生产。此次没有修改主项目、既有城市基线或前一轮五目标候选；未运行浏览器或 Blender。

| 宏块 / near | 原要素 | 目标 | 保留邻居 | gzip（MB） |
| --- | ---: | --- | ---: | ---: |
| `14-13701-6700 / -3_2-s1-s0` | 28 | 北大街222 | 27 | 0.11 |
| `14-13720-6694 / 3_-4-s1-s1` | 6 | 14 | 5 | 0.055 |
| `14-13720-6694 / 3_-3-s0-s1` | 10 | 07、09 | 8 | 0.074 |
| `14-13720-6694 / 3_-3-s1-s1` | 11 | 05、06 | 9 | 0.090 |

四个 near 共55个原要素，6个完整目标组和49个保留邻居，405,246个展开三角形。四个 gzip 合计0.33 MB；最大解压 GLB为0.48 MB，全部严格低于100 MB。

222只新增 `14-13701-6700/local502` 的目标组，完整键为 `building:3fdcd081-70df-4c5d-a08c-2f553289c25b`。同块27栋的完整几何、材料、绕序和重复计数保留，不进行半径删除。新 near SHA为 `fb6e5bed1fb7071d2687171ffe7793a6483fcd31469ae2a10ca3990d8450084d`。

原三个 near 的 gzip 与解压 SHA全部与五目标候选逐字节一致。由于这次覆盖两个宏块，工具将发布路径按宏分目录防止短文件名碰撞；内容不变，registry路径须和复制目录一致。

## 来源及生成契约

`inputs/` 保存六份原冻结几何字节；222另含原 `mapping-report.json`。222为 Overture 的 Zenodo / East Asian Buildings 来源，明确非 OSM 建筑轮廓，不伪造 way。复制版生成器新增这一来源分支：先确认 mapping report 的几何 SHA与目标 key、宏及localID，再验证其原 feature-table、READY、ownership 的实际字节和 SHA；随后核对完整 effective feature、唯一 near owner、原始高度与轮廓。目标存在未映射parts、残余或有据屋顶时拒绝，不静默删除。

原 OSM 分支未放宽检查。冻结引擎 SHA `dd9124f4e8d57ed0991d82793e0471264d6f3700cb363f86647ffa7505f4535c`、全城config SHA `bc00ae98308d26661b45dd7dab7b5098cab3ca4c7c7f9c1490122212af5e9956`保持。生成器仍使用完整宏邻居进行原始开孔决策，不重采高度、不重分块、不改源足迹。

## 复现

使用同一已冻结项目及 gltfpack，在本目录运行；输出必须是全新隔离目录：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
python build_precise_overrides.py \
  --project "$PROJECT" --output "$NEW_OUTPUT" \
  --geometry-input-root ./inputs \
  --ids bund05 bund06 bund07 bund09 bund14 qingpu-beidajie-222 \
  --gltfpack "$GLTFPACK" \
  --reuse-registry ../integration-review/overrides/precise-buildings-v6.json \
  --reuse-asset-root ../integration-review/overrides

node verify_override_geometry.mjs "$NEW_OUTPUT/geometry-comparison-input.json"
node verify_override_runtime.mjs "$PROJECT" "$NEW_OUTPUT/precise-buildings-v6.json"
SHANGHAI_PROJECT="$PROJECT" python test_precise_generator.py -v
```

`--geometry-input-root`仍可重复，但同一ID出现在两个根会拒绝。`--reuse-asset-root`用于明确读取前一轮staging资产；不指定时沿用项目内既有发布文件。三组未变化的owner必须重建到相同 SHA，才能继续生成候选。工具拒绝向项目或不可变城市symlink的真实目录输出。

## 实际解码与负控

使用主项目真正的 Three GLTFLoader 和 MeshoptDecoder 展开实例矩阵。原near、候选、逐源feature、目标完整组和保留邻居的位置 Float64、材料名、三角绕序及重数全部精确相同。四块没有缺失或额外三角。

法线允许范围保持之前批准的分量差≤1e-7且角差≤1e-5度。222的最大分量差为2.06332e-8，最大角差1.49769e-6度，通过；其5,944个三角在Float64法线比较有逐位差异，Float32比较仍有1,216个。报告完整记录bitdiff，未宣称法线逐位相同。原三块结果与上一轮相同。

实际解码负控只将222候选的一个 NORMAL 分量增加0.01，位置保持精确不变，法线最大角差约0.311度，审计正确拒绝；随后恢复内存属性，不改文件。输入契约7项测试通过，包括伪造mapping-report绑定、篡改ownership SHA、未映射parts、重复与歧义ID拒绝。

运行时验证实际加载两个宏的5,152个far要素和四个near。六目标逐个可见、全部可见、全隐藏时，只切换对应owner组，邻居保持可见；near卸载后只保留精细模型的far引用，精细模型隐藏后far mask/reference全部恢复0，destroy清理引用。证据在 `overrides/runtime-owner-validation.json`。这不是WebGL截图或精细建筑视觉测试。

## 交接

发布候选只需 registry及四个`.glb.gz`，见 `handoff.json` 和 `asset-files.json`。`work/`、未压缩`.glb`和绝对路径的比较输入是本地核验中间物，不是运行时发布资产。源码及冻结输入清单见 `source-files.json`。222最终形态/材质视觉验收由主代理另行安排。
