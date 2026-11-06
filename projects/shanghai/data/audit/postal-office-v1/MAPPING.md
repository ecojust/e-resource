# 邮政总局定位与结构碰撞复验

本轮限定地图主源 `1959`（`14-13720-6693`，`99edb5ad-b642-4040-a923-4f4375eeeac8`，OSM `w11629370@10`）。西南相接源 `3148` 保留，不给其指定未经核验的建筑年代或完整名录归属。原地图外框为整块无内洞轮廓；U 形内边界及 2010 参照弧罩平面是作者估计，详见[单体合同](../../../source/precise/hongkou-general-post-office/footprint-contract.json)。

南面沿北苏州路、东面沿四川北路、北面沿天潼路，已对照有限范围 OSM 道路几何。完整下载响应与未定拍摄日期的私存卫星图不随库发布。OSM 派生事实／几何：© OpenStreetMap contributors，ODbL-1.0；不把地图推估高度当作测量值。

## 源显示替换

近景共享组的四个源是 `[1780,814,3148,1959]`，13 个 mesh 没有逐顶点源 ID。即使登记目标 owner 为 `1959`，这组近景仍会共同收到六行裁剪；仅检查 owner 字段不足以保护邻体。

本轮在主外框外扩 0.12 米后，明确扣除相接 `3148` 外框的 0.12 米保护带，保留主源窄接缝。生产 Float32 三角纹理与实际近／远景投影分别检查，邻体交叠为零；不能将主源描述为完全清空。远景原有逐顶点 owner 过滤继续保留。数量、残留面积和有限分类精度见 [源裁剪记录](clip-geometry-review.json) 与 [材料作用范围](source-scope-verification.json)。

六行新增裁剪使全局达到 307／320；没有修改公共容量或校验器。材料钩子复验覆盖 Standard、Depth、Distance，实际浏览器画面另行验收，不能把此处 CPU 检查称为 GPU 像素测试。

## 实际模型与碰撞

先从原始、压缩网页、远景 GLB 的真实索引、节点／实例矩阵和材质解析三角面，再计算全高投影与结构低位投影。最终合同必须绑定最终 manifest 及三项 GLB 的确切哈希。

院内薄底板是简化可见铺地：`dark stone`，高度 0–0.16 米，四边形平面严格对应作者内院。每个资产恰好 12 面按材质、高度和院内平面共同识别并单独排除；U 形基座延至 0.18 米，墙、柱等结构仍保留。不能把全部 0–2 米投影或屋盖投影当作建筑障碍填满内院，也不能因此宣称开放了室内路线。

结构三角面精确截取至 0–2 米，并集经有限简化与保守余量后，必须仍覆盖所有实际结构、避开保留源，并满足现有单环 256 点限制。内院小范围墙柱余量的面积与剩余净空单独记录；不是用全场凸包替代碰撞。生产 `checked_geometry`、`validCandidateGeometry` 与真实地面点再核对序列化结果。

[最终定位合同](footprint-review.json)绑定修复后 raw `92912c58…`、web `05d1bb2f…`、LOD `ab39cc6b…`，三份均重新解码并完整计算投影。结构低位并集 4581.125748 平方米，经 0.13 米简化后加 0.12 米保守余量，形成 254 点单环碰撞，面积 4639.415297 平方米，实际结构漏盖为零。内院仍有 1762.156093 平方米不在结构碰撞内；墙柱余量占用内院 24.141391 平方米，不能误称完全无余量。17 个保留源、三项实际近景邻体以及近／远主源保留接缝均无模型或碰撞交叠。

[生产几何语义检查](collision-runtime-verification.json)通过八个地面点和五个源替换点。钟鼓侧面小窗修复前的实际三角形证据保存在 [revision-82a935ab](revision-82a935ab/README.md)，不替代修复后的验收结果。

## 重放入口

依赖：Python 3、NumPy、Shapely 2、支持 `node:module.registerHooks` 的 Node，以及仓库内 Three／GLTFLoader／MeshoptDecoder。运行前确保四个冻结 Git blob 在本地可读取；若为部分克隆，先按准确路径补齐。不要对全市资产运行本项解码。

以下在仓库根目录运行，`POSTAL_MAPPING_WORK` 必须是仓库外的可写目录。源阶段仅核源显示替换；不能据此声称新模型已经验收。

```sh
export POSTAL_REPO="$PWD"
export POSTAL_MAPPING_WORK=/tmp/postal-map-recheck
python projects/shanghai/data/audit/postal-office-v1/map-extract-source.py --repo "$POSTAL_REPO" --work-dir "$POSTAL_MAPPING_WORK"
node projects/shanghai/data/audit/postal-office-v1/map-decode-source.mjs
python projects/shanghai/data/audit/postal-office-v1/map-analyze-source.py
node projects/shanghai/data/audit/postal-office-v1/map-verify-source-scope.mjs
python projects/shanghai/data/audit/postal-office-v1/map-review-clip.py
```

[已执行的源阶段独立缓存重放](source-replay.json)绑定五项实际脚本与结果。新增模型解码入口为 `map-decode-delivered.mjs`，之后运行 `map-analyze-delivered.py`；默认读取本件正式资产目录，草稿检查可显式指定目录。`--reuse-full-projection` 仅允许复用相同资产哈希的既有全高投影，并在结果中注明；最终三资产验收不使用该选项。

`map-finalize-placement.py --manifest <正式清单>` 使用已保存的实际源、资料和模型几何报告生成最终合同；`map-verify-collision.mjs` 核对其生产语义。两者须在最终三资产、源报告和实际 QA 输入齐备后执行，不用于凭空生成“通过”记录。完整最终报告、浏览器结果和公开发布状态见本目录交付说明。

```sh
node projects/shanghai/data/audit/postal-office-v1/map-decode-delivered.mjs
python projects/shanghai/data/audit/postal-office-v1/map-analyze-delivered.py
python projects/shanghai/data/audit/postal-office-v1/map-finalize-placement.py --manifest projects/shanghai/assets/models/candidates/hongkou-general-post-office/manifest.json
node projects/shanghai/data/audit/postal-office-v1/map-verify-collision.mjs
```

上述命令只写指定仓库外缓存。[最终模型投影执行记录](final-projection-execution.json)与[碰撞合同执行记录](final-placement-execution.json)保存实际命令、脚本哈希与退出状态；正式合同冻结后，浏览器若发现需要改动的几何，须更新版本并重新绑定目录，不在原记录上偷换资产哈希。
