# 崇明学宫戟门候选检查（2026-10-29）

依据博物馆文字和两张2005年照片制作的独立候选。正面材料与开间关系有照片依据，背面、截面、尺寸端点与门扇细分仍是估计；未照片定标或城市地理配准，不计入40处原址漫游或逐栋精细复原验收数量。

- [几何检查](geometry.json)：近景143,632三角面、2,048个源构件；远景25,520三角面、412个源构件。顶点有限、三角面无退化、法向一致，逐源构件封闭且正体积，源与导出面数一致。两个高度的贯通射线验证中央门洞没有被填死。最高8米，含瓦当的模型外包约18.70×8.26米。材料合并后的相交构件不宣称为整体布尔实体。
- [Blender重开](native.json)：Blender 4.3.2保存重开模型几何哈希一致；舞台不计入建筑。
- 实际Cycles渲染：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)。已对照2005年院落照片检查连续瓦顶、中央开口、红门/白墙布局；屋端和后墙是估计。渲染检查发现匾额边框穿过屋面后已下移，最终预览与资产相符。
- [网页检查](browser.json)、[截图](browser.png)：SHA256校验模型加载，完整/远景/完整切换，四个相机按钮，模型室外漫游进入、前进和Esc退出。中央几何门洞开放，外围碰撞仍禁止穿门，不提供室内漫游。

网页复测：在`projects/shanghai`运行`python -m http.server 8766`，仓库根目录运行`node projects/shanghai/data/audit/ji-gate-v1/qa-browser.cjs`，需Playwright与`/usr/bin/chromium`。输出到`/tmp/ji-gate-browser.*`。其余构建/验证命令见[来源目录](../../../source/precise/chongming-ji-gate/README.md)。

原始、近景、远景GLB及Blender均严格小于100,000,000字节；字节/哈希记录于[资产清单](../../../assets/models/candidates/chongming-ji-gate/manifest.json)。照片未再分发或嵌入模型，来源URL、作者、许可、下载哈希与尺寸解释一并保留。
