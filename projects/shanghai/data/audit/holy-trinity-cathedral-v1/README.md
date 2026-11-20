# 圣三一主堂制作与核验

第48项为九江路的红砖主堂与东侧花园门廊。公开资料给出的主堂长度约46.3至47米；模型依花园入口、南北敞廊、横翼和西端圣所的照片轮廓定位，独立钟塔与旧校舍保留在各自范围内。首批名录编号1A025，旧址门牌201号，现宗教机构联系地址219号。[制作说明、外观来源与下载](../../../source/precise/huangpu-holy-trinity-cathedral/README.md)

| 检查 | 结果 |
| --- | --- |
| 模型文件 | 网页137,604面，远景72,644面。三种GLB均实际解码或读取，Blender场景重开142个可编辑网格。[资产清单](../../../assets/models/candidates/huangpu-holy-trinity-cathedral/manifest.json) · [原生表面对照](geometry-native.json) |
| 形体 | 每档40项射线，合计120项。检查入堂门扇、开敞廊、窗列、花窗、交叉屋顶与西部半穹形屋顶。修正首稿过于平直的西端体量。[原始检查](surface-checks.json) · [西端修订](preflight/apse-review.json) · [三个视图及哈希](author-visual-review.json) |
| 城市原体 | 完整替换宏块14-13720-6694内的587。其近景20,074面和远景52面被裁切，邻近66,492个近景三角面与主堂仍有至少6.265米净距。东入口和南北侧廊三处留通行。[地图收据](../../../source/precise/huangpu-holy-trinity-cathedral/footprint-review.json) · [配准实测](placement-geometry.json) · [正式合同](final-placement-contract.json) |
| 运行时 | 94处城市目录实际经过逐组裁剪及双套矢量底图检查。原体所在绘制组采用12个裁剪三角形，确认旧校楼、塔位等周围建筑保留。[运行时报告](runtime-placement.json) · [冻结页面与文件指纹](production-snapshot.json) |
| 独立查看器 | 1250×820桌面和390×844手机分别切换两个细节档位；4个实际下载逐个核验字节和SHA-256。[浏览器报告](viewer.json) · [四张截图目视核验](viewer-visual-review.json) |

首版94处视角从东面望向主堂，保留的花园侧原体挡住了东门廊。实景试拍后，默认相机改为从东南侧朝285.41°方向、俯仰45°观察。站点锚点、原模型和底图裁剪合同中的空间数据均未改动。[原视角与93处前态](preflight/original-camera/review.json) · [三张实景与唯一两项相机修改](preflight/camera-study/review.json)

使用仓库根目录中的以下命令重查模型射线及配准。配准脚本需要能读取收据中冻结的 Git 对象。

```sh
python -B projects/shanghai/source/precise/huangpu-holy-trinity-cathedral/source/check_surfaces.py --out /tmp/trinity-rays.json
python -B projects/shanghai/data/audit/holy-trinity-cathedral-v1/verify-placement.py \
  --manifest projects/shanghai/assets/models/candidates/huangpu-holy-trinity-cathedral/manifest.json \
  --work /tmp/trinity-placement --out /tmp/trinity-result
```
