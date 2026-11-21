# 丁香花园一号楼拱廊与露木山墙

在2013年庭院原片中，门廊右墩上可辨金色的“1”。门洞上方一排小拱与出挑窗下的木托在不同年份的照片中反复出现。建筑实体单按一号楼研究；另有带“3”号牌的水刷石住宅及园外住宅。[影像、地方志和市表](../../../source/precise/xuhui-dingxiang-garden-main-house/reference-review.json) · [原片、测算及实物区别](../../../source/precise/xuhui-dingxiang-garden-main-house/numbered-buildings-review.json)

原始GLB和网页近景均为17,820面，远景为8,700面。重开Blender核对65个可编辑网格，网格有12种材质。首版转角端盖与正面重叠，渲染出现黑线。现有侧墙止在正墙内皮，窗下有两重嵌板，出挑窗的短上亮与大窗扇分开。三档各以107条真实射线核对拱与小洞、石肩、可穿过的侧廊、后门、木窗、烟囱、瓦行及瓦缝。[折角修复前后](draft-review/reference.json) · [重开记录与渲染](geometry-native.json) · [首达面逐项结果](surface-checks.json)

有一号门牌的立面由拍摄磁方位和正交消失线估算朝向约330°，落位采用1353西北向328.6°的折边。沿墙方向的位置仍为估计值，保护名录给的是主楼门牌。切除仅覆盖入口前段和短返回，原模型近、远景分别保留92.0%和92.1%的占地。与其他源网格的最小净距为3.49米。近、远原网格在接缝上的差距为0.072米，后部按原楼高度收口。两侧拱洞和台阶的通行面与门扇、墙墩分别核对。[源体、邻体与地面](placement-geometry.json) · [定位合同](final-placement-contract.json) · [照片方位](../../../source/precise/xuhui-dingxiang-garden-main-house/facade-orientation.json)

209处和210处正式站点的前169条增补目录一致。裁切仅在原楼1353的图块中加入2个三角形。13座相邻楼体均保留原轮廓和地面碰撞。两套矢量源共核对28条结果，另检查29处地面与邻楼。新版本逐项实取1,181个HTTP文件，共1,053,902,325字节。[实站相邻版本](renderer-parent-controls.json) · [运行时矢量与地面](runtime-placement.json) · [实际下载清单](renderer-release-http.json)

独立页在桌面及390像素手机上均可切换近、远景，并可下载原始、近景、远景和原生模型。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [四件下载](viewer.json)

## 普通地图入口与两端实拍

从前一版的209处地点切换至210处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31173/map-before.png) · [返回本楼](city-31173/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31173/map-mobile-same-camera.png) | 390×844 | 9/9 |
| [桌面稳定画面](city-31173/map-desktop-same-camera.png) | 870×620 | 8/9 |
| [手机公开加号](city-31173/map-mobile-public-zoom.png) | 390×844 | 6/9 |
| [细看立面](city-31173/map-street-facade.png) | 620×465 | 6/9 |
| [屋面](city-31173/map-roof.png) | 620×465 | 6/9 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。公开站整读1,183个文件，地面通行及周围楼房合计29个采样。前态、手机、街面与屋面、远景均正常退出。宽桌面的目录选中、鼠标选标和跨区切换通过，最后回到丁香时渲染进程退出，未生成回返帧。随后以620×465桌面从虹口重复公开键盘切回，补得回返实图并正常退出。[远档](city-31173/map-distant.png) · [各视图与遮挡位置](city-31173/default-screen-coverage.json) · [完整签收](city-31173/result.json)

[单体与下载页](../../../dingxiang-garden-main-house.html) · [原始GLB](../../../assets/models/candidates/xuhui-dingxiang-garden-main-house/xuhui-dingxiang-garden-main-house-raw.glb) · [网页近景GLB](../../../assets/models/candidates/xuhui-dingxiang-garden-main-house/xuhui-dingxiang-garden-main-house-web.glb) · [远景GLB](../../../assets/models/candidates/xuhui-dingxiang-garden-main-house/xuhui-dingxiang-garden-main-house-lod.glb) · [Blender工程](../../../assets/models/candidates/xuhui-dingxiang-garden-main-house/xuhui-dingxiang-garden-main-house.blend)


[第一次桌面退出记录](city-31173/initial-desktop-return-crash.json) · [独立回返复查](city-31173/return-browser.json)


郭棣活住宅西楼相距约189米。切到郭宅时，两栋楼分别保留自己的模型与既有楼体的裁切。再切至虹口东大名路378号，丁香花园的模型与裁切才退出；切回后重新出现。[切至郭宅时的现场](city-31173/map-neighbor-guo.png)

390×844手机默认图里可辨正面的露木山墙、前突窗与底层拱门。870×620桌面的本楼标牌压住山墙顶的一个采样点。街面近图可见门廊卷拱和侧翼窗，屋面近图可辨红瓦坡面及木构山墙，底层窗位有地点卡遮挡。门墩“1”的字形结合2013年原照和独立模型核对。[手机稳定画面](city-31173/map-mobile-same-camera.png) · [街面](city-31173/map-street-facade.png) · [原图与编号复核](../../../source/precise/xuhui-dingxiang-garden-main-house/numbered-buildings-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/1f58410adc0eca6008b23769168efeac3441eb94/projects/shanghai/index.html#landmark=xuhui-dingxiang-garden-main-house&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
