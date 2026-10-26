> 历史阶段说明：下文仅适用于 52a49d → 77a72f 的玻璃深度修正，不是当前照片形态修正版的全范围不变声明。当前版使用 README 与 check_visual_refinement.py；旧 check_glass_fit.py 不属于本版发布白名单。

# 玻璃嵌框候选

这是原 Bund07 冻结源码的独立候选，修正估计的玻璃构造深度。普通 / T / 18片照片玻璃前面从 d=-0.32 移到 -0.18 m；后面为 -0.20 m。它们仍在真实墙洞内，只从格框后方空隙移入格框厚度。两椭圆眼窗按独立格条的位置改到 `[.155,.175]` m。玻璃前面距对应格条前面20 mm、厚20 mm，均是构造估计。

源轮廓、层高、窗洞、框、格条、山花、屋顶、其他全部构件及材料不改；照片控制点、UV、原JPEG不改。冻结 `../common/photo_architecture.py` 未修改。普通窗口在本地调用原工具后只移动生成的玻璃 solid，保持原连续片拓扑；T窗和注册照片分片沿各自法向移动。

```bash
python build_model.py
python check_photo_uv.py
python check_glass_fit.py --baseline-dir /path/to/original/bund07
python make_source_package.py
```

`--baseline-dir` 必须指向包含原 `output/bund07.glb`、部件清单和照片证据的完整修前目录。原 raw SHA-256 为 `52a49d3f1b2dddb78ddb5a86e4e1c28d8502238eaaaa9fcb0129c998f6bbcec9`。核查实际 GLB 数组，不以模型声明替代检查。证据见 `output/glass-fit-invariance.json` 和 `output/photo-uv-check.json`。重建脚本、公共依赖和原始照片全部相对引用；发布白名单为 `source-package-files.json`。

未生成新的 native 或预览，未替换生产资产。同相机视觉验收仍待 root 执行。保留原 README 的历史形态/来源说明，本候选深度变更以本文件为准。
