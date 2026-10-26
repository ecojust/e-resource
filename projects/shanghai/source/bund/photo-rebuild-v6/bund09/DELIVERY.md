# 外滩9号单体模型交付

最终roof-v3单体已完成原生实际渲染、压缩native有界校验和Blender重新打开验证；网页接入仍待后续验收。

- [原始GLB](../../../../assets/models/bund/bund09.glb)：76,875,072字节。
- [网页版GLB](../../../../assets/models/bund/web/bund09.glb)：30,117,188字节。
- [Blender原生文件](../../../../assets/native/bund/bund09.blend)：42,678,476字节（Blender原生无损压缩）。
- [远景模型](../../../../assets/models/bund/lod-v4/bund09.glb)：8,429,340字节。

[实际预览](../../../../assets/previews/bund/bund09-v6.png)及[针对性视觉核对](../../../../data/audit/precise-buildings-v6/bund09/native-compressed/appearance-review.json)对应本批文件。可见南坡连续瓦片、底层石券缝和阳台角柱已修正；后缘支承坡、隐藏后屋顶与部分栏杆数量仍为推定，不作为照片已验证的形体。

[封装记录](../../../../data/audit/precise-buildings-v6/bund09-packaging.json)记录原图和四套资产SHA；[实际Blender重开](../../../../data/audit/precise-buildings-v6/bund09/native-compressed/reopen-check.json)核得996,983三角形、边界差0、原图字节完全一致。文件本身严格低于100,000,000字节，解压后的内存数据大小不是Git仓库文件大小。
