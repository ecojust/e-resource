# 江南制造局旧址总办公楼外立面

原生近景和网页近景均为57,420个三角面，远景为27,460个。Blender 4.3.2 重开文件后取得107个可编辑网格，按材质比较通过。斜俯视原生图能看见与两期航片吻合的北开院三翼，并可辨龙华东路正面的两个方柱平顶门廊、窄窗行列和檐线。树后窗数、院内窗格和屋顶标高均为估算。[原生图](huangpu-jiangnan-historic-general-office-preview.png) · [网格及源文件校验](geometry-native.json) · [原始资料](../../../source/precise/huangpu-jiangnan-historic-general-office/README.md)

第一次射线复核时，近景一根落水管遮住了同一开间的上下两扇窗。最终模型把外墙落水管移到实墙窗间。原始、近景、远景各用123条射线检查凹入的玻璃、木窗与灰泥立柱、门扇、门廊柱、檐下、踏步、三处瓦坡和北院敞口，合计369项均通过。[实测结果](surface-checks.json) · [独立检查程序](../../../source/precise/huangpu-jiangnan-historic-general-office/source/check_surfaces.py)

独立页在 1250×820 桌面和 390×844 手机上分别用鼠标、触屏选取龙华东路正面、门廊斜视与三翼屋顶。六张实图中，正面可见两处门廊和两层窗列，斜视可辨门廊投影，俯视能看清北院敞口。窄屏全楼正视时单窗很小。浏览器逐一保存四件文件并核对摘要，网页近远景各材质的三角面数也与解码结果一致。[真实浏览器收据](viewer.json) · [桌面门廊](viewer-desktop-full-oblique.png) · [手机屋顶](viewer-mobile-lod-above.png)

底图近景与远景原先把1335号历史办公楼绘成22.17米高的简化体量。两档均实测同栋被完整替换，最近邻楼与裁切边缘的净距超过8.2米。18个本栋地面点和6个邻楼点分别检查门廊、街面、三翼及朝北开口的院落。正式总览相机的桌面与手机计算各能看见两座门廊、正面街门、上层窄窗和屋脊等七处特征。[原始地块及四个源文件](../../../source/precise/huangpu-jiangnan-historic-general-office/footprint-review.json) · [近远景几何与地面](placement-geometry.json) · [相机视线](overview-sightlines.json)

正式26219目录共256处，总办公楼有一张黄浦区地点卡。正式独立页的栋名、沿革和龙华东路街廓与资料一致。实取的原始模型、网页近远景和Blender工程四个文件均与真实下载的摘要相符。全站1,558个签名文件逐一经HTTP读回，共1,313,030,332字节。城市裁切在22个宏区中共有1,586个三角面，最大宏区336面。[正式地点卡和独立页](city-26219-viewer-and-card.json) · [实取清单](city-26219-all-http.json) · [运行时裁切与地面](runtime-placement.json)

## 普通地图入口与两端实拍

从前一版的255处地点切换至256处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31219/map-before.png) · [返回本楼](city-31219/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31219/map-mobile-same-camera.png) | 390×844 | 7/7 |
| [桌面稳定画面](city-31219/map-desktop-same-camera.png) | 900×650 | 7/7 |
| [手机公开加号](city-31219/map-mobile-public-zoom.png) | 390×844 | 6/7 |
| [细看立面](city-31219/map-street-facade.png) | 700×550 | 7/7 |
| [屋面](city-31219/map-roof.png) | 700×550 | 4/7 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。公开站整读1,558个文件，地面通行及周围楼房合计24个采样。对照、手机、桌面、键盘切走并返回、街面与屋面、远景六个独立会话均已结束，退出码均为0。[远档](city-31219/map-distant.png) · [各视图与遮挡位置](city-31219/default-screen-coverage.json) · [完整签收](city-31219/result.json)

[单体与下载页](../../../jiangnan-historic-general-office.html) · [原始GLB](../../../assets/models/candidates/huangpu-jiangnan-historic-general-office/huangpu-jiangnan-historic-general-office-raw.glb) · [网页近景GLB](../../../assets/models/candidates/huangpu-jiangnan-historic-general-office/huangpu-jiangnan-historic-general-office-web.glb) · [远景GLB](../../../assets/models/candidates/huangpu-jiangnan-historic-general-office/huangpu-jiangnan-historic-general-office-lod.glb) · [Blender工程](../../../assets/models/candidates/huangpu-jiangnan-historic-general-office/huangpu-jiangnan-historic-general-office.blend)

## 江南制造局旧址总办公楼的实拍判读

手机和桌面的普通目录实拍可辨两层浅色外廊、长条红屋顶与两端返翼。屋面专项显示U形布局。 [桌面](city-31219/map-desktop-same-camera.png) · [手机](city-31219/map-mobile-same-camera.png)

回返与远景保留了底部打开的地点卡，可见建筑采样均为0/7。公开放大后的手机为6/7、屋顶为4/7。 [回返](city-31219/map-returned.png) · [远景](city-31219/map-distant.png) · [采样位置](city-31219/default-screen-coverage.json)

两端的独立页面均拍到完整正面、斜面及U形屋顶。正面可看到两层连续门窗和两端较宽的入口。 [桌面正面](city-31219/ordinary-viewer/viewer-desktop-full-front.png) · [手机斜面](city-31219/ordinary-viewer/viewer-mobile-full-oblique.png) · [屋顶与返翼](city-31219/ordinary-viewer/viewer-desktop-lod-above.png) · [六幅图及四项下载](city-31219/ordinary-viewer/viewer.json)

初次独立页与控制试拍的记录、同一时段其他建筑的开发测试均已留档。六段城市实拍与本栋正式独立页各自附有原始报告。 [早期尝试及开发回单](city-31219/attempts/index.json) · [人工判读与逐图校验值](city-31219/manual-visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/67035bcf984053c0e2ef8b54e04ce74ef00bcda4/projects/shanghai/index.html#landmark=huangpu-jiangnan-historic-general-office&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
