# 05、06、14 号玻璃嵌框修订

本次以保持既有窗框的前后面和形状为约束，将同类窗构造的玻璃前表面移到框前脸后 **20 mm**，玻璃厚度仍为 20 mm。这是为合理表达嵌框关系而采用的构造估计，不是现场测绘值。原先玻璃位于框后较深的位置，在斜射光下产生过强的实体框遮挡。

| 建筑 | 仅玻璃向外位移 | 移动玻璃实体 | 三角形总数保持 | 当前原始模型 SHA256 |
|---|---:|---:|---:|---|
| 05 | 0.140 m | 324 | 146,056 | `a125c8e72bfe8f4eb8abb7c402d9789e01387d2d16f3eee045bf6f7c3aaf5212` |
| 06 | 0.085 m | 644 | 91,111 | `641bc6f0b747df3a7405bda467b65311f9758493f6b32d6d463d18cb94eed0a6` |
| 14 | 0.095 m | 1,388 | 77,324 | `dcd09ce14eaa59ac016e66dffd7a672360e2a8cff6c5af6d8ae051142e8c7bdf` |

三份逐实体比较：[05](bund05/glass-depth-difference.json)、[06](bund06/glass-depth-difference.json)、[14](bund14/glass-depth-difference.json)。检查确认非玻璃位置与法线、展开三角形顺序和总数、全部照片 UV、材质定义和嵌入的原始 JPEG 字节保持；玻璃只沿其所属立面法线平移。同种框结构的普通玻璃一并修正。05 普通窗保留原连续玻璃薄板构造；14 的 5 件独立入口/门玻璃保持原构造，未作为普通窗移动。

当前构建闭合/UV/原图检查、网页模型实际解码比较以及原生固定机位预览核对均已有对应证据。三份 `native-preview-review.json` 记录主审实际查看的范围；新的预览位于 `assets/previews/bund/*-v6.png`。**最终生产网页同视角和场景复验仍待完成**，原生预览不替代网页验证。这些数值检查也不代表整栋所有不可见细节均有照片依据。

`portable-rebuild-check.json` 等已有历史证据仅适用于其内部记录的原始 SHA；新的 `historical-source-restore-check.json` 只验证修订前源码输入可逐字节恢复，没有重复生成旧模型。每栋源码下 `glazing-depth-history` 保留旧输入清单、修改前文件与恢复工具。当前修订与旧证据的 SHA 对应关系见各栋 `glazing-depth-revision.json`。后续精细建模范围见 [DETAIL_STANDARD.md](DETAIL_STANDARD.md)。
