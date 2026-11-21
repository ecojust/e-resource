# 南昌大楼街角入口与冠饰

南端短立面的入口向内退，门扇的金属腰板上下有细直棂，门上扇形气窗藏在浅弧门额后。两侧是七层窗和临街首段凸窗，中央砖柱向上接塔状冠饰。首版的门格较粗；2019年发表的铁门近照和2023年发表的塔部近照分别用于修订。第二版射线揭示竖柱下端遮住了气窗，修订后门扇、扇形铁花和每处托块均可从街面看见。[首版](draft-review/first-corner.jpg) · [修订版](draft-review/revised-corner.jpg) · [照片与修订记录](draft-review/street-revision.json) · [身份与制作范围](../../../source/precise/huangpu-astrid-apartments-corner/README.md)

原始版及网页近景各48,624面，远景34,172面。Blender工程重开后有73个可编辑网格。三档各以135道射线检查门扇和背衬、扇形气窗、色砖、两列窗和侧翼挑窗、冠饰折带和托块、屋面及截墙，含材质和深度判定。[可编辑检查](geometry-native.json) · [三档射线](surface-checks.json)

底图建筑4415近景共有38,656个三角面，远景有28面。截取正面后，两条街翼保留近景投影的88.34%与远景投影的88.36%。地图原轮廓保留1049.1平方米。裁切限于街角，与同组最近邻网格的距离为30.98米。16个本栋点位覆盖门槛、铁门、两侧街面和内院，另核8个邻楼。原墙在接缝处闭合一段，两条长翼、院内附房及出入口均留在原位。[配准与地面点](placement-geometry.json) · [主图范围](final-placement-contract.json) · [街角视线](../../../source/precise/huangpu-astrid-apartments-corner/camera-preflight.json)

独立页、脚本和四件模型文件均已从本地服务器实际读取并核对字节数与SHA-256。[独立页](../../../astrid-apartments.html) · [HTTP记录](standalone-http.json)

对照234处和235处地图实际返回的目录，原有194条候选模型记录逐行一致。新增的两片裁切三角形只作用于4415号原楼的街角。两套矢量数据源共核18项，入口、道路和临近建筑共核24个地面位置。[前后版本比较](renderer-parent-controls.json) · [地面与源模型](renderer-runtime-placement.json)

桌面与390像素手机实测了48,624面的近景和34,172面的远景，四种下载文件与模型清单逐字节相符。正式预览服务的1,383个输入合计1,193,934,704字节，均经HTTP取回并核对。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [四项下载](viewer.json) · [逐件校验](renderer-release-http.json)


### 正式街区地图

31197原有234处，31198加入南昌大楼后为235处。桌面与390像素手机均从地标目录进入，地图加载稳定后可见南端浅色转角、中央竖向砖带和两边折回的窗墙。桌面目录面板占住左侧，手机的两枚邻楼标签贴近冠部。另在街区中用鼠标和触屏分别点中南昌大楼。远景实际切换到34,172面的模型，同时核对近远两份城市瓦片及四个下载文件。[前态](final-map-31198/before/map-before.png) · [桌面](final-map-31198/desktop/map-desktop-settled.png) · [手机](final-map-31198/phone/map-mobile-settled.png) · [远景实测](final-map-31198/distant/main-browser.json)

街面近照可见门前斜收的两侧墙、门框和深色扇形气窗。另一张高位画面可见塔冠的折线和逐级收窄的顶端。五个门面和塔冠采样点均落在画布上，避开了标签和地点卡。本楼16处及邻楼8处的实际通行结果均与底图对照相符。[门与气窗](final-map-31198/architecture/map-iron-fanlight.png) · [塔冠](final-map-31198/architecture/map-tower-crown.png) · [24处地面与两种实际点击](final-map-31198/results.json)

第一次建筑实测有两份城市资源返回502；补回原始字节后，前后两站都返回200，四张建筑实景重新拍摄。第一次远景切换时渲染进程退出，随后在同站较小视口成功拍下远景并取回四份文件。两次原始失败和对应的成功记录均保留。[两站资源摘要](final-map-31198/repaired-ready-31197-31198.json) · [原始与复测记录](archived-browser-attempts.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/f94594b3e7959bf502dbf20bd0e04d5a6485f993/projects/shanghai/index.html#landmark=huangpu-astrid-apartments-corner&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，4 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
