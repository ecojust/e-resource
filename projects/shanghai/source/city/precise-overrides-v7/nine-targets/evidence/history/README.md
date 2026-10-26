# 增量精确替换：旧七目标 + 北大街208—212号

`eight-targets/precise-buildings-v6.json` 已通过源归属、实际解码几何及运行时 owner 检查。这里处理城市基线的精确分组；`complete:true`不代表茶楼精模、原生图、浏览器或目录已经验收。没有安装到主项目或正在运行的129候选。

只新增青浦宏 `14-13701-6700` 的 `-3_2-s0-s0`：28个原要素中，将 `local25` / `building:02c5c111-b4e8-4339-a8fd-b93b88bf65ea` 单独分组，保留27个邻楼。该源轮廓来自 Zenodo / East Asian Buildings，经 Overture 汇编；不是OSM楼体。它与222号同宏、不同near。

新增文件 `assets/city-overrides-v6/14-13701-6700/-3_2-s0-s0.glb.gz` 为102,662B，SHA256 `71dcb8b7dd1ee130bcb5f97f130b6485b37188583d1cb388eb6fbe7be2ed43fb`；解压318,004B、76,252三角形。旧五块沿用原字节，不重新生成。合并后3宏、6块near、8目标、93个保留邻楼；gzip合计526,061B，全部文件严格小于100,000,000B。

新near使用实际 Three GLTFLoader/MeshoptDecoder 检查实例矩阵后的 Float64 位置、材料、绕序、重数、目标组及27邻楼，缺失/额外三角均0。法线存在1,828个三角的逐位差异，最大分量差2.01649e-8、方向差1.45766e-6度，均在原阈值1e-7/1e-5度内。对实际解码后的茶楼目标组仅改一个法线分量0.01的负控，被正确拒绝；不声称法线字节相同。

旧五块复用已通过的几何报告，并重新核对当前源输入、完整目标feature、原near、stored/decoded字节与SHA；本轮未为这五块再做逐三角几何比较。合并后的运行时测试重新实际解码3个far宏共9,309个要素和全部6个near，检查每个目标独立显隐、全部显隐、邻楼保持、near卸载、mask恢复和destroy释放。它不是WebGL画面或材质验收。

主要交付：

- `eight-targets/handoff.json`：最终范围与几何/运行时报告绑定。
- `eight-targets/asset-files.json`：6个gzip及registry的明确路径、字节和SHA。
- `new-b/geometry-validation.json`：本轮新near实际解码报告和目标法线负控。
- `eight-targets/geometry-validation.json`：明确区分新检查与旧证据复用的合并报告。
- `eight-targets/runtime-owner-validation.json`：对完整8目标候选重新运行的实际Three owner检查。
- `input-review-b.json`：第二位审查者只读核验冻结输入与真实基线。

本候选特意没有 `ordinary_catalog`。旧青浦 accepted 目录只含222号，与这里包含222及新茶楼的完整宏不一致，不能直接接上。新精模静态验收阶段应明确停用旧目录入口；所有目标取得实际验收后，按宏重新签完整 index/replacement，再测目录生命周期。不能把待验茶楼标为accepted来避开门槛。

## 重建与后续目标

`tools/build_precise_overrides.py` 保留v6原字节。`verify_override_geometry.mjs`只将既有法线负控的目标选择改为输入的 `negative_control_target_ids`，几何与法线标准不变。`verify_override_runtime.mjs`保留v6原字节并导入项目实际运行时。输入及工具SHA见 `tool-input-freeze.json`、`source-files.json`。

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
python tools/build_precise_overrides.py \
  --project /workspace/shanghai_project --output FRESH_NEW_B \
  --geometry-input-root inputs --ids qingpu-beidajie-208-212 \
  --gltfpack /workspace/shanghai_tools/node_modules/.bin/gltfpack \
  --asset-prefix assets/city-overrides-v6/14-13701-6700
```

生成的比较输入中显式设置 `negative_control_target_ids:["qingpu-beidajie-208-212"]`，再运行 `node tools/verify_override_geometry.mjs FRESH_NEW_B/geometry-comparison-input.json`。Node参考路径为 `/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node`，gltfpack是既有npm1.3.0 CLI。

```bash
python compose_incremental.py --project /workspace/shanghai_project \
  --prior-root /workspace/shanghai_expansion/building-by-building-v6/next/all-seven-integration-review/overrides \
  --fresh-root FRESH_NEW_B --inputs inputs --output FRESH_EIGHT
node tools/verify_override_runtime.mjs /workspace/shanghai_project FRESH_EIGHT/precise-buildings-v6.json
```

输出必须是本隔离stage内全新目录。武康210冻结后可另起九目标修订；若它与129同near，重新生成该near时必须包括所有原目标，合并器会拒绝丢失既有owner。旧候选和报告保留。大型城市基线、work中间GLB和本机绝对路径比较输入不是网页发布包。
