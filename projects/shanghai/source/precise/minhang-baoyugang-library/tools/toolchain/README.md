# V11 现代建筑打包与注册准备

两个目标是 `jiading-shanghai-auto-museum`（嘉定区）和 `minhang-baoyugang-library`（闵行区）。本目录独立于作者工作源、MAIN 和全部 V10 文件。当前目标清单是 **pending 模板**；没有实际 raw、原生场景或模型验收，不得拿模板用于发布。

`upstream-lock.json` 记录原通用打包器、封装核心、测量器和项目 GLTFLoader / MeshoptDecoder 的真实 SHA。前四份原件保存在 `upstream/`，没有改写原件。`external-tool-lock.json` 还绑定实际 gltfpack 1.3.0 的 CLI、JS/WASM、版本与许可文件。`modern-packager.patch` 是新封装器相对通用原件的显式差异。

`package_modern.py` 使用原 `-cc -noq -km -ke` 压缩参数，保持 Float32 位置，不使用统一 QEM 减面。博物馆先压缩完整 raw，必须如实注明没有几何减面；图书馆允许使用作者明确删去 `fine-tile-joints-*` 的 authored LOD。其他构件不可删改。打包器只证明文件、尺寸、元数据及基础包络；不会自行给模型或浏览器通过结论。

`check_decoded_modern.mjs` 使用项目真实 GLTFLoader 和 MeshoptDecoder 做 CPU 解码：

- raw / web 的世界坐标有向三角形、材质归属与重复次数完全相同；每角法向误差不超过既有 0.05° 上限。
- 核对实际材质的透射、折射率、体积厚度、衰减颜色与距离、透明模式，以及普通 PBR 属性。图片与外部 URI 均不允许；这两栋楼采用自有几何，不嵌入参考照片。
- raw 与 authored LOD 的实际分件逐一比较，保留 `[label, material, ordinal]`，不将同名的断开构件合并；只允许清单内微细接缝分件消失。
- authored LOD 与最终压缩 LOD 再做实际解码等价比较。web 包络差不超过 0.0001 m；LOD 包络差严格小于 0.35 m。包络不是完整轮廓或 Hausdorff 证明。
- 对压缩资产按实际三角形重新建立语义，不能把 raw 的索引范围直接套在优化后网格上。有限开口、接触、框/玻璃深度和负控由 `independent-modern-review` 的同一套几何引擎执行；不沿用古塔、瓦、斗栱或火焰窗检查。

有限检查用实际解码的 ENU Float64 数组作为临时输入，每块不超过 64 MiB。默认逐角色检查完只删除本工具自己创建的临时二进制，保留原 GLB、解码器和检查器 SHA、重建方法、块 SHA/字节及实际报告；这些块会明确标记为非持久文件。失败可保留以排查，重跑必须使用新输出路径。实际解码由 root 排程，与 Blender 不并行。本轮准备只运行小型语法、比较政策和 pending 拒绝控制。

未来在作者冻结源、真实 raw/native 及证据齐全后，复制 pending 模板为新的 ready 清单并填写实际 `{source, bytes, sha256}`，保留原模板。不能只把 `status` 改成 ready：缺任一实际文件、SHA 不匹配、白名单或验收未完成都会拒绝后续交付。

```sh
python package_modern.py --target READY_TARGET.json \
  --project /workspace/shanghai_project \
  --gltfpack /workspace/shanghai_tools/node_modules/.bin/gltfpack \
  --output NEW_RUN/package

node --max-old-space-size=4096 check_decoded_modern.mjs /workspace/shanghai_project \
  READY_TARGET.json NEW_RUN/package NEW_RUN/decoded-package-check.json
```

注册器在 `registration/` 单独维护严格契约。它必须绑定四个实际资产、当前独立 raw 审核、解码/有限检查、原生三图报告与 root 三图实看记录、导航证据和最终源码依赖白名单。最终仍生成 `browser_accepted:false` 的 draft，HTML 验收属于后续独立工作。原生三图是全景、细节、背面/屋面，不宣称相机标定。

所有文件严格小于 100,000,000 字节；45 MB raw、20 MB web、30 MB native 是作者工程目标，不可冒充用户硬限制。未授权官网、设计方和厂家图片/PDF仅在研究区，不得复制到公共源码包或作为纹理。公开参考只使用作者白名单中许可明确的文件。

有限检查桥接使用已冻结的独立引擎 V2，精确副本与原件由 `independent-engine-lock.json` 绑定。V2 修复了零/负实心阈值、NaN/空射线以及空尺寸约束可能导致的错误通过；原始结构报告、几何算法和 0.001° raw 法向标准均未重标或放宽。

源码工具清单见 `tool-source-freeze.json`，整体交接见 `handoff.json`，注册子工具独立交接在 `registration/handoff.json`。这些清单表示工具版本与小型控制已检查，**不表示实际模型已经通过解码、有限检查、原生或浏览器验收**。真正 ready target 必须在打包前固定，后续不能为注册改动它的字节；其中 `registration_allowed:true` 只允许尝试严格证据校验，不是验收结论。
