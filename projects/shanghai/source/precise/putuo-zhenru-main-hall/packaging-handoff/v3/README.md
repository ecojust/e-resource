# 真如寺 geometry-v2 的独立注册适配

本目录由源码交付代理独占维护；作者独占 `geometry-v2/` 模型构造源码与 renderer。原 `packaging-handoff/v1`、`v2` 和历史报告均不修改。本目录仅准备新辅助工具，没有执行注册、验收、staging、安装或发布。

选定模型源码为 `zhenru-main-hall/geometry-v2`，作者冻结 SHA 为 `02929a28105be0fa9765a9d0e3105279c6e41f67d6aa7667c570cd405ea25056`。实际生成目录为 `zhenru-main-hall/run-geometry-v2/{raw,native,package}`。`packaging-input.json` 明确标识 geometry-v2；高度来自已生成新 raw 的实际边界，仍是建筑尺度估计。解码器与上一版原字节相同，但执行时必须传入当前 run 和当前源码，不能复用旧解码结果。

## 两组 raw 证据的边界

历史 raw SHA 为 `b9d4c8981740c19a22ced43d825e643b04fb42960cb113b13ae605e02e3106f9`。历史原始 roles/contact FAIL、全局 PCA 截面 FAIL、实际瓦端平面8500对 PASS、root 有限接触解释、旧结构和旧原生报告各自固定其原始文件 SHA；它们不会被改写为新 raw。

当前结构必须另行 PASS，并精确绑定当前作者冻结。B 的当前证明必须将新/旧 raw 分开，证实只允许144构件变化：140斗拱臂和垫座、4斜山脊。其余全部构件的实际三角形、法线和材料保持不变，并证明140木构支承链与未穿出屋面。只有 B 明确记录所有屋面/瓦片几何与材料字节未变、且引用历史8500对报告的真实 SHA，才允许将其瓦片接触结论沿用到新模型。摘要明确 `8500_pair_test_reexecuted_on_current_fullraw:false`，不伪称重跑，也不把旧全 raw SHA 当成新值。

A 的当前证明单独检查4斜山脊：4组高坡屋面接触、8组脊间连接、2组山墙保留、4组陶质垂帘投影以及实际 full/rear 相机下的山墙可见性。所有列表项须有真实 `passed:true`，相机项必须包含明确的 `camera_role:full/rear`。这不代替新的三张原生图、root 实际观看，以及新 raw/web/LOD 的实际解码检查。

原生与浏览器阶段独立。此注册适配器只能在上述实际证据齐备后生成 model-only 注册草稿；`browser_proof` 必须保持 pending。有限几何容差及支承准则以真实报告为准，不宣称每点接触、无碰撞或工程承载认证。

## 运行接口

打包使用本目录新 spec。实际 decoder 命令：

```sh
node /absolute/packaging-handoff/v3/check_decoded_package.mjs /workspace/shanghai_project /absolute/run-geometry-v2 /absolute/geometry-v2
```

注册器参数均需真实存在的最终文件；当前新证明/原生/包未齐备时不得调用生成输出：

```sh
python3 /absolute/packaging-handoff/v3/prepare_registration.py \
  --run /absolute/run-geometry-v2 \
  --model-source /absolute/geometry-v2 \
  --native-report /absolute/run-geometry-v2/native/native-render-report.json \
  --native-review /absolute/current-root-native-visual-review.json \
  --structure-proof /absolute/actual-raw-structure-geometry-v2.json \
  --preservation-proof /absolute/actual-final-B-preservation-proof.json \
  --ridge-proof /absolute/actual-final-A-ridge-gable-proof.json \
  --historical-structure-proof /absolute/actual-raw-structure-v1.json \
  --historical-contact-proof /absolute/actual-roles-contacts-v1.json \
  --historical-pca-contact-proof /absolute/actual-cover-pan-intersection-v1.json \
  --historical-lip-contact-proof /absolute/actual-cover-pan-intersection-v2.json \
  --historical-contact-review /absolute/historical-root-finite-contact-review.json \
  --historical-native-report /absolute/run-v1/native/native-render-report.json \
  --navigation /absolute/navigation-proposals/putuo-zhenru-main-hall.json
```

历史接触算法报告后缀 v2 仍属于旧 geometry-v1；模型修订目录 geometry-v2 是不同概念。最终 B/A 证明文件由实际检查者交接，不能仅按文件存在或文件名后缀认定通过。

`prepare_registration.py` 检查原作者冻结中的私有研究字节。公开源码可通过独立事实摘要裁去长楹联，但该摘要不能冒充原研究 SHA；原始验收重放需要原私有研究记录。模型 raw/native 构建本体不依赖这些研究引文。
