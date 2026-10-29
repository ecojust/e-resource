# 崇圣祠正殿候选检查（2026-10-29）

这是博物馆文字引导的独立外观候选，未照片核验、未城市配准，未计入40处原址漫游或逐栋精细复原验收。

- [几何检查](geometry.json)：近景141,776三角面、2,356个源构件；远景23,768三角面、696个源构件。导出顶点有限、三角面无退化，模型最高11米；逐源构件封闭、法向一致、正体积，导出面数与源一致。按材料合并的相交构件不宣称为单一封闭布尔实体。
- [Blender保存重开](native.json)：Blender 4.3.2，模型141,776三角面，重开几何哈希一致；舞台不计入建筑。
- [原生正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)：实际Cycles渲染，已人工检查。
- [网页检查](browser.json)：Chromium + Playwright，本地HTTP加载校验SHA256、近远景切换、相机操作及模型室外行走；[浏览器截图](browser.png)。不替代照片对照或地理配准。

网页复测：在`projects/shanghai`运行`python -m http.server 8765`，另在仓库根目录执行`node projects/shanghai/data/audit/chongsheng-shrine-v1/qa-browser.cjs`，需Playwright及`/usr/bin/chromium`，输出在`/tmp/chongsheng-browser.*`。几何复测与构建命令见[来源目录](../../../source/precise/chongming-chongsheng-shrine/README.md)。网页源码复用既有大成殿查看器及共享候选漫游模块。

原始GLB、网页GLB、远景GLB及Blender各自小于100 MB；字节、SHA256和面数见[资产清单](../../../assets/models/candidates/chongming-chongsheng-shrine/manifest.json)。建筑源码、公开来源URL、响应哈希、尺寸矛盾及估计范围一并保存；未再分发原网页或引用他人照片。
