# 东官厅文字尺寸参照候选检查（2026-10-29）

本检查验证候选文件、实际几何和独立预览可使用。文献约束是东官厅位于泮池／登云桥东侧，以及东西宽6.5米、南北长10.1米、高6.5米。没有开间数或中央入口的文字约束；三个等分立面区、中门、两窗及屋顶仍为估计。

- [几何](geometry.json)：近景28,916三角面、1,031个源构件；LOD 3,684三角面、155个源构件。源构件封闭、法向一致、正体积；导出顶点有限、无退化面，源与导出面数一致。两处格窗单元射线穿过实际间隙到达后退暗面，估计中央门关闭；踢脚端盖藏于接头内部。
- 局部X基座10.1米、Y基座6.5米，将南北长边设为朝院面是坐标解释，未验证真实门向。全部构件实际外包约11.05×7.443×6.5米，包括瓦端和边脊，不将其当作文献量测线。65.65平方米仅为文献平面尺寸乘积，原段没有列建筑面积。
- [原生重开](native.json)：Blender 4.3.2导入建筑面数与raw一致，保存并重开后的几何哈希一致。报告同时记录所用raw与最终Blender SHA256；预览舞台不计入建筑。
- 实际Cycles渲染：[正面](native-front.png)、[斜侧](native-oblique.png)、[背面](native-rear.png)。墙角内缘衔接与踢脚首尾接头正常，未见共面黑块。
- [网页检查](browser.json)、[截图](browser.png)：东官厅独立身份与SHA256加载、近远景切换、四视角、适配相机距离、本件模型生成的室外边界，以及漫游进入/移动/Esc退出。门关闭，未开放室内。独立网页窗边仍有很细的竖线，Cycles原生渲染未出现对应几何黑块。限定渲染诊断中，normalBias=0、仅plaster启用flatShading、临时关闭阴影及直接加载raw均复现，不能再归因于阴影偏移或仅压缩打包；具体成因未确定。保留有阴影的基线版本。对照见[诊断结果](render-diagnostics/results.json)及同目录五张截图。

几何报告中的`lod`哈希对应压缩前简化源GLB；发布LOD另由manifest和网页核对。压缩GLB保留本件身份、文献方位尺寸与明确假设的extras。

| 资产 | 文件大小 |
|---|---:|
| 原始GLB | 2.271100 MB |
| 网页GLB | 0.745404 MB |
| 远景GLB | 0.091572 MB |
| Blender | 1.056841 MB |

各文件均小于100 MB。哈希见[资产清单](../../../assets/models/candidates/chongming-east-guanting/manifest.json)，完整来源、不同修缮范围及假设见[来源说明](../../../source/precise/chongming-east-guanting/README.md)。1991、旧馆1998、1998年12月至1999年10月工程分别保留，未作为唯一修建年份或2026实况。未将航拍屋面组当整栋，未照片再分发或城市配准。

网页复测：在`projects/shanghai`运行`python -m http.server 8774`，仓库根目录执行`node projects/shanghai/data/audit/east-guanting-v1/qa-browser.cjs`，需Playwright和`/usr/bin/chromium`。结果位于`/tmp/east-guanting-browser.*`。

主代理实际查看最终斜侧、背面原生渲染及网页截图，并复核四件资产大小与SHA256；见[视觉复核](root-visual-review.json)。网页细竖线保留为已知显示限制。
