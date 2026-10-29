# 西官厅文字尺寸参照候选检查（2026-10-29）

本检查验证候选文件、实际几何和独立预览可使用。文献约束是西官厅位于泮池／登云桥西侧，以及东西宽7.4米、南北长10.2米、高6.5米。没有开间数或中央入口的文字约束；三个等分立面区、中门、两窗及屋顶仍为估计。

- [几何](geometry.json)：近景28,916三角面、1,031个源构件；LOD 3,684三角面、155个源构件。源构件封闭、法向一致、正体积；导出顶点有限、无退化面，源与导出面数一致。两处格窗单元射线穿过实际间隙到达后退暗面，估计中央门关闭；踢脚端盖藏于接头内部。
- 局部X基座10.2米、Y基座7.4米，将南北长边设为朝院面是坐标解释，未验证真实门向。全部构件实际外包约11.15×8.339×6.5米，包括瓦端和边脊，不将其当作文献量测线。75.48平方米仅为文献平面尺寸乘积，原段没有列建筑面积。
- [原生重开](native.json)：Blender 4.3.2导入建筑面数与raw一致，保存并重开后的几何哈希一致。报告同时记录所用raw与最终Blender SHA256；预览舞台不计入建筑。
- 实际Cycles渲染：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)。墙角内缘衔接与踢脚首尾接头正常，未见共面黑块。
- [网页检查](browser.json)、[截图](browser.png)：西官厅独立身份与SHA256加载、近远景切换、四视角、适配相机距离、本件模型生成的室外边界，以及漫游进入/移动/Esc退出。门关闭，未开放室内。本件沿用东官厅有阴影的页面参数，最终网页截图窗边仍可见细竖线，记录为已知显示限制；同类页面的诊断见[东官厅有限诊断](../east-guanting-v1/render-diagnostics/results.json)，没有为西官厅展开新的调参试验。

几何报告中的`lod`哈希对应压缩前简化源GLB；发布LOD另由manifest和网页核对。压缩GLB保留本件身份、文献方位尺寸与明确假设的extras。

| 资产 | 文件大小 |
|---|---:|
| 原始GLB | 2.160756 MB |
| 网页GLB | 0.729632 MB |
| 远景GLB | 0.092456 MB |
| Blender | 0.908896 MB |

各文件均小于100 MB。哈希见[资产清单](../../../assets/models/candidates/chongming-west-guanting/manifest.json)，完整来源、不同修缮范围及假设见[来源说明](../../../source/precise/chongming-west-guanting/README.md)。1991、旧馆1998、1998年12月至1999年10月工程分别保留，未作为唯一修建年份或2026实况。未将航拍屋面组当整栋，未照片再分发或城市配准。

网页复测：在`projects/shanghai`运行`python -m http.server 8775`，仓库根目录执行`node projects/shanghai/data/audit/west-guanting-v1/qa-browser.cjs`，需Playwright和`/usr/bin/chromium`。结果位于`/tmp/west-guanting-browser.*`。


主代理实际查看最终斜侧、背面原生渲染及网页截图，复核四件资产大小、SHA256、GLB身份和西侧来源尺寸；见[视觉复核](root-visual-review.json)。

[固定版本在线预览](https://rawcdn.githack.com/ecojust/e-resource/ffc4510616e628d505b710b8e834f4bb3571eb8a/projects/shanghai/west-guanting.html)已实际加载，西官厅身份、28,916三角面、GLB哈希及同版本官厅来源尺寸核对通过，网页错误数为0。见[公开网页记录](public-browser.json)；仓库根目录可运行`node projects/shanghai/data/audit/west-guanting-v1/qa-public.cjs`复验。
