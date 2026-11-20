# 裕华新村3号临弄院门与楼面模型核对

2026年11月20日按2014年署有3号门牌的实照建立门墙和可见楼面。原始与近景 GLB 各15,386个三角面；远景7,256个。Blender 4.3.2 重开原生文件，逐材质核对60组可编辑网格、19种材质与原始定向三角面。压缩近景和远景分别独立解码并比对。[文件清单](../../../assets/models/candidates/jingan-yuhua-new-residential-quarter-03/manifest.json) · [原生及网格比对](geometry-native.json) · [原生预览](jingan-yuhua-new-residential-quarter-03-preview.png)

45条射线分别命中绿色门牌与凸起的数字3、门扇、门柱、各层真实玻璃窗、砖带、超檐竖片以及后退半圆窗。正面宽窗的左侧开口距离超过右侧玻璃约0.47米，两侧均由金属横栏守住。[门窗材质与深度验证](opening-rays.json)

城市中的881号是门牌落点所在的小段粗模；19级航影显示完整住宅屋面明显伸出该粗体。照片范围的窄段裁剪保留近景64.51%、远景64.93%。同文件其他13个所有者均无几何重叠，最近独立建筑是2号住宅的2844，离裁剪边界13.57米。五处地面核对包含院门、临弄公共路面和门内前院间隙。正对原生2号的镜头会挡住低门牌，127°的斜向视线可避开该栋。[源面及门牌证据](../../../source/precise/jingan-yuhua-new-residential-quarter-03/footprint-review.json) · [实际近远源与碰撞](footprint-review.json) · [配准合同](final-placement-contract.json) · [相机视线](overview-sightlines.json)

从上海项目目录运行；MACRO为14-13719-6695原始宏区目录，WORK为空目录。

    python -B data/audit/yuhua-residence-03-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/yuhua-03/placement
    python -B data/audit/yuhua-residence-03-v1/check-openings.py --work "$WORK" --report /tmp/yuhua-03/rays.json

### 单体页面

桌面和390×844手机的近、远档都显示完整入镜的临弄门墙、双窗砖带、砖竖片与退台半圆窗；手机面板位于画布下方。原始、网页、远景及Blender四个链接实际下载后均与清单一致。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机远景](viewer-mobile-lod.png) · [分辨率、下载及字节记录](viewer.json)

### 105处上海主图

在包含新版多伦路镜头及共享模型加载修正的105处目录，从上海主图的建筑目录进入裕华新村3号。桌面、手机分别查到实际近景，远处切到简化模型。一层院门、中央砖竖片和后段粗体都各有近景，实测足迹保留门前可通行区域。桌面默认标题覆盖部分高处，近门细读受发光点影响，可在独立页看清3号牌。[桌面](main-desktop.png) · [院门](numbered-gate.png) · [砖片](brick-blade.png) · [保留原生后段](retained-source.png) · [远景](distant.png) · [手机](main-mobile.png)

同一份初始目录在第一次加载时遇到25秒网络超时，退回粗分块；重新请求详细目录后，首轮仍在近瓦片完全绘出前达到观察时限。完整保留该轮的控制台、HTTP字节和恢复时相机参数。第二轮从正常目录重新进入，桌面初始使用详细来源，无需手动修改视角。实际验证的同源运行与登记文件共140项，另有4项生成输入。[首轮状态与HTTP](preflight/revised-first-load.json) · [最终浏览器报告](main-map-browser.json) · [文件哈希](main-map-inputs.json) · [逐图记录](main-map-visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/22bb76d9866d472d8ce7ba4ebf06f42c757e4e79/projects/shanghai/index.html#landmark=jingan-yuhua-new-residential-quarter-03&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
