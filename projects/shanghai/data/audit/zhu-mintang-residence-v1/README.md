# 朱敏堂住宅151号街门与双石狮

交付的街门宽约8.90米，包括短墙、两根门柱、外置的两尊坐狮和闭合的双扇门。左柱的绿色门牌可读作151。参考年代为2019年5月，2011年9月照片中的柱顶灯具也已记录。院内白色壁板山墙只有街道一侧能见，跨年份三角化结果不足以划定房屋边界；街门采用已有建筑之间的空地，院内4287和商业地址点所在3702等六座原楼保留。[建造记载和历年资料](../../../source/precise/xuhui-zhu-mintang-residence/reference-review.json) · [街景测点、相机与屋顶对照](../../../source/precise/xuhui-zhu-mintang-residence/street-registration.json)

四件模型包含57,736面的网页近景和原始网格、17,872面的网页远景及65个可编辑网格的Blender工程。原生文件重开后以48次采样渲染，并逐面比对原始网格。三份实际导出的模型分别通过47项独立射线检查，覆盖门柱、球顶、151牌、四格门芯、浮雕、狮首、前爪、石座和上方净空。[资产与SHA-256](../../../assets/models/candidates/xuhui-zhu-mintang-residence/manifest.json) · [原生与材质面比对](geometry-native.json) · [原生图](xuhui-zhu-mintang-residence-preview.png) · [141项几何检查](surface-checks.json)

五个公共道路机位对照两根球顶柱和两扇门的角点。柱心相距约3.80米，最大横向拟合残差约0.92米。落位后的实际模型与最近的原生近景、远景网格分别相隔3.116米、3.186米，交叠面积均为0。24个地面点覆盖门扇、门前人行道、狮座及六座保留楼。以默认78°方位、37°俯角投射到真实网格，桌面和390宽手机上自面可见的4,599和4,630个样点分别通过城市体块遮挡检查。[放置合同](final-placement-contract.json) · [近远模型净距与地面点](placement-geometry.json) · [视线检查及其范围](camera-preflight.json)

独立页在本地HTTP上实测1250×820桌面和390×844触屏。两种屏幕都实际切换了近景和远景。桌面浏览器还逐个下载四件文件并核验字节和散列。页面未报错。[浏览器记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png) · [独立页](../../../zhu-mintang-residence.html)

真实城市主图的前后态核验使用共享的独立添加建筑检查器。本目录列出专属灯牌、近景、碰撞与保留邻体采样点。[本栋配置](city-actions.json) · [检查器说明](../jixiangli-west-gate-v1/map-actions.md)

本次加入151号门和双狮后，作者版城市目录由215处增至216处。1,218份输入文件均已重新读取，目录同时登记后续三项任务。[作者版文件收据](production-snapshot.json)

正式23178→23179采用与网页相同的城市渲染和碰撞模块复验。加入门楼前后，全市仍为1,198个裁切三角面、20张宏块表，单块最多322面。两类矢量来源中的六栋邻楼原样保留，24个地面点逐点通过。[城市运行检查](runtime-overlay.json)

正式216处站点逐一返回了1,229份内容，合计1,081,317,091字节，全部与生产版本文件清单相符。[逐个HTTP地址、长度及SHA-256](release-23179-http.json)

## 城市地图中的151号街门

在215处的前一版地图里，从乌鲁木齐南路向院内看，楼前是一块空地。加入街门后，960×700桌面用鼠标点中灯牌、390×844手机用触摸点中同一地点，两端都能看到左右石狮、球顶门柱和闭合门扇。门后仍是原来的楼体。左侧近景能读到绿色的“151”门牌，也能看清狮头、前爪与石座。在另一幅近景中，南侧石狮的轮廓与门扇上的四格浮雕同时可见。[前一版的街面](city-31179/before-front.png) · [桌面](city-31179/map-desktop.png) · [触屏](city-31179/map-mobile.png) · [北狮与151号门牌](city-31179/map-northern-lion-and-151.png) · [南狮与门扇](city-31179/map-southern-lion-and-door.png)

两组原地图网格各有20栋。实际载入这两组时，院内4287、3702及其余四栋核查对象均继续挡住行人，门扇、门柱、短墙和狮座挡住行人，门前人行道和绕过狮座的地面可通行。两版各实测24个地面点。街区远景载入17,872面版本。440×380画面中位置卡覆盖中心，狮首和门扇要在57,736面的近景中查看。独立页实际保存的原始GLB、网页近景、远景和Blender工程均与各自清单逐字节匹配。[两档与四次下载](city-31179/after.json) · [近远地面](city-31179/runtime-overlay.json) · [远景取证](city-31179/map-distant.png) · [1,231项正式文件的下载校验](city-31179/all-http.json)

首次在同一浏览器连续打开两个全城视图时，取得桌面图后渲染器因内存不足退出。另一次从已加载近景切换至远景时也曾中止。正式图使用分别启动并退出的浏览器，逐次记录实际设备尺寸、相机、网格与截图的校验值。[首次中断](city-31179/initial-after-renderer-interruption/after.json) · [远景初试](city-31179/initial-distant-renderer-interruption/after.json) · [各次记录与正式地图](city-31179/release-evidence.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/c84c142a719f541f2ea801955bb287c06573815e/projects/shanghai/index.html#landmark=xuhui-zhu-mintang-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
