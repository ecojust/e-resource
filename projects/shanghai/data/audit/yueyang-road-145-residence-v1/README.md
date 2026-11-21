# 岳阳路145号花园住宅南立面与折檐红瓦屋顶

从花园看，玻璃廊顶是一整块露台。上面两侧白墙突出，中央小老虎窗嵌在红瓦坡面之间。1948年街坊图给出主宅位于花园北端的位置。2023年俯拍的右侧露出永嘉路501号住宅的锥形塔尖，使两栋住宅的相对位置可交叉核对。市房管局名录的2D024和2D028均印作岳阳路145号，两栋分别保留工作登记和建筑证据。[名录、房管资料与照片](../../../source/precise/xuhui-yueyang-road-145-residence/reference-review.json) · [建筑范围](../../../source/precise/xuhui-yueyang-road-145-residence/README.md)

原始和网页近景均有37,177个三角面，简化远景为22,184个。Blender工程重开后，43个可编辑网格与13种材质逐面核对。对三份实际GLB各发射89条射线，检验花园玻璃窗、中央门、两组前凸、两层遮阳篷、露台栏杆、老虎窗、五组烟囱、弯折鱼鳞瓦及露天地面。最终渲染还核对了缓坡上的交错瓦行和花园玻璃廊两端的浅色饰带。[原生渲染](xuhui-yueyang-road-145-residence-preview.png) · [近远与原生文件](geometry-native.json) · [267条表面检查](surface-checks.json) · [首版屋面](first-roof-preview.png) · [屋面与饰带修订](visual-review.json)

主宅庭园侧宽约22.1米，最高的烟囱约14.5米。地块2048原有的32.367米矩形旧体在两档城市网格中均完整替换。东邻340和北邻4888用实际三角面分别对照。主宅模型距两处原近景分别为13.36米、2.15米。保留园路、草地、门前台阶和独立附属楼。比例与开口来自公共照片，树后部分和背面墙体作简化处理。[现存地块和两期航片](../../../source/precise/xuhui-yueyang-road-145-residence/footprint-review.json) · [原生城市网格、地面及附近五栋](placement-geometry.json) · [桌面和手机默认视线](overview-sightlines.json) · [独立模型页](../../../yueyang-road-145-residence.html)

1250像素桌面和390像素手机都从「花园南面」实际切换近、远档。两档均可见三层立面及五组烟囱，原始GLB、网页近景、简化远景和Blender工程四项下载的字节与SHA-256均通过。[桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png) · [实际浏览及下载](viewer.json)

与永嘉路501号圆塔住宅各自最终GLB解码后，两栋网格最近相距12.22米，两个底图裁片相距12.39米。地图登记继承同组原来27片，本栋加入2片。[两座模型的实体间距](adjacent-villas.json) [地图测试样例](map-case.json) [205处冻结签名](production-snapshot.json)

用实际23167与23168服务复取关键字节。后态1140项输入与签名一致，运行时同组27片增到29片，地面与邻栋共核对16个点，现场两种矢量源均按约定保留其他建筑。[两端HTTP收据](signed-23k-http.json) [运行时验收](runtime-placement.json)

## 205处正式整城实测

由31167的204处切换至31168的205处，前版同机位可见原有高矩形体。后版从公开地点目录点进岳阳路145号，390×844手机图能辨红瓦折檐、正中老虎窗和南花园凸窗。公开加号放大后，花园玻璃廊、两侧上层窗和露台铁栏更清楚。762×568桌面目录保留了本楼和12.22米外永嘉路501号的标牌，本楼标牌覆盖了玻璃廊、东侧上层窗和中央门三个采样点。900×640桌面以普通鼠标从目录选中，使用公开加号和拖动，一次停稳时有六处采样点避开界面与标牌，花园玻璃廊点落在本楼标牌处。最终图可见红瓦、老虎窗、两翼窗和右侧玻璃廊。玻璃廊与栏杆两个检测点落在地点卡下，屋脊烟囱点落在图例内，四处采样点完整露出。宽桌面首图拍于目录刚载入时，地块的原有简模尚在；正式街面和屋面以载入完毕的近图核验。[前代对照](city-31168/map-before.png) · [手机目录](city-31168/map-mobile.png) · [手机放大](city-31168/map-mobile-public-zoom.png) · [窄桌面目录](city-31168/map-desktop.png) · [宽桌面初次载入](city-31168/map-wide-directory.png) · [鼠标放大和拖动后](city-31168/map-public-mouse-garden.png)

键盘先选永嘉路501号，两栋住宅的真实模型和各自的裁切继续生效。切至虹口东大名路378号后，岳阳路模型与裁切退出；返回岳阳路后重新载入。16个地面和邻楼采样全部符合现场预期，网页近景和远景都由实际场景下载并核对散列。街面与屋面会话实际加载原有近景分组，远档会话另外实取该近景文件核对字节；原有远景底图及原始、网页、远景、Blender四件也逐项核对。正式站整读1,142项。两次系统内存不足留下的失败记录分别对应最初的前态和第一次远档检查。随后一次检查读错目录内网页模型散列的字段名，记录中保存了正确的真实近景散列；改用登记字段web后重新打开现场检查。对照、触屏、鼠标、近景与地面、远档五次正式会话均正常退出。附加桌面在取下截图及各点坐标后主动关闭，未达到其自设的七处同时无遮挡条件。原退出记录为 passed=false、exit=1，SHA-256 为 dabf66195f04df27ccfb13979c064eedb0ac31e32a0f320aa8ac3514912c7cc0。[下载原退出记录](city-31168/public-desktop-closed.txt) · [查看截图时的七处坐标](city-31168/map-public-mouse-garden.json)[切邻楼](city-31168/map-neighbor-501.png) · [切回岳阳路](city-31168/map-returned.png) · [屋面](city-31168/map-roof.png) · [远档](city-31168/map-distant.png) · [各段与四件签收](city-31168/result.json) · [首次前态](city-31168/first-control-oom.json) · [首次远档](city-31168/first-distant-oom.json)

[单体与下载页](../../../yueyang-road-145-residence.html) · [原始GLB](../../../assets/models/candidates/xuhui-yueyang-road-145-residence/xuhui-yueyang-road-145-residence-raw.glb) · [网页GLB](../../../assets/models/candidates/xuhui-yueyang-road-145-residence/xuhui-yueyang-road-145-residence-web.glb) · [远景GLB](../../../assets/models/candidates/xuhui-yueyang-road-145-residence/xuhui-yueyang-road-145-residence-lod.glb) · [Blender工程](../../../assets/models/candidates/xuhui-yueyang-road-145-residence/xuhui-yueyang-road-145-residence.blend)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/635294fe827d0bc8cb5b5191375405723df9e8ea/projects/shanghai/index.html#landmark=xuhui-yueyang-road-145-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
