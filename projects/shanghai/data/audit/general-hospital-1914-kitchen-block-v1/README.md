# 1914年公济医院后勤楼的几何复核

本次源模型的三个实际导出都检查了嵌入纹理、三角面、实体封闭和有向表面。北面、东街门、朝院一面、屋檐、石额和庭院阳台各有近景机位。网页上的远景保留了街口轮廓、钢窗、石额和檐托。

| 导出 | 文件字节 | 三角面 |
|---|---:|---:|
| 原始 GLB | 13,754,296 | 210,304 |
| 网页近景 | 5,291,336 | 210,304 |
| 网页远景 | 2,441,844 | 109,228 |

每个原始几何部件均闭合且带正体积。近景有4,318个部件、2,076组可编辑标签，远景有1,902个部件、1,741组标签。网页压缩后分别解码，对照各自输入的有向三角面。程序生成的同一幅红砖纹理用于外墙和屋顶抬高砖体，贴图与网格分别校验。[导出清单](preflight/manifest.json) · [有向表面比较](preflight/decoded-surface-comparison.json) · [纹理坐标](preflight/render-uv.json)

街照和院照一共选取54个固定像点，其中51个在各档首先命中预期材质。初稿有四处跨层石板底衬露砖。修订后这四处全部命中石材，另外三处的材质差异仍留在原像点记录中。逐窗检查另有87个照片像点，其中84点命中；余下三处均为街照中的窄开口。[54点记录](preflight/geometry-rays.json) · [窗扇复核](windows/registered-window-study.json) · [窗及石裙渲染](windows/registered-window-study.jpg)

檐口与屋面有34束模型剖面射线，每档均命中。独立照片中的屋面像点在街照命中38/39、院照命中27/28，两处轮廓差异保留在三份实网结果中。石额按街角照、近照和2019年三个独立街站塑形。[屋面逐档结果](roof-cornice/three-released-meshes.json) · [檐口与院侧女儿墙](roof-cornice/roof-cornice-two-elevations.jpg) · [石额构件](stone-cartouche/north-stone-cartouche.jpg)

任务的建筑身份、地面交会及研究照片见对应源码目录。[楼体与范围](../../../source/precise/hongkou-general-hospital-1914-kitchen-block/README.md) · [照片与许可](../../../source/precise/hongkou-general-hospital-1914-kitchen-block/SOURCES-LICENSE.md)
