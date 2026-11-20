# 沪江大学大学礼堂

1937年建成的大学礼堂位于军工路516号。二批2G002的登记地址同时列礼堂和实验楼。大学主礼堂与北侧思魏堂呈L形，本文模型取其中长37.20米、宽约17.08米的主厅以及可以核实的交接。1949年起两厅都可以称为思魏堂。1956年风灾和次年修缮有校档记录。现存东北山墙的五联窗、两枚圆窗与早期照片可相互核对。北侧小堂、实验楼归属和另行命名的格致堂均见单独的边界记录。[校史、实照和保护名录](../../../source/precise/yangpu-hujiang-university-auditorium/README.md) · [建模参数与资料精度](../../../source/precise/yangpu-hujiang-university-auditorium/source/parameters.json)

近景和原始GLB各56,708个三角面，远景20,004个，重新打开Blender得到70个可编辑网格。三种GLB分别验证31条射线，辨别东北山墙的十个采光格、通层石带、圆窗玻璃和石框、双扇门、前后山墙和瓦顶。东南长墙较远的窗距、西南端门窗细分和屋面高度按照片比例估计。[原生文件核验](geometry-native.json) · [93次射线检查](opening-rays.json) · [原生模型渲染](yangpu-hujiang-university-auditorium-preview.png) · [模型清单](../../../assets/models/candidates/yangpu-hujiang-university-auditorium/manifest.json)

固定宏区14-13723-6691的2357号源同时覆盖主厅和北侧思魏堂。沿主厅西北交界裁出一条直线截面，分别保留近景258.95平方米（28.16%）、远景255.17平方米（28.07%）的原生投影。共用截面至两个原生边缘的最大偏差约5.8厘米。另五个同组源均保持完整。八个地面点检查两侧草坪、门阶、厅内与小堂位置。按固定底图高度验证默认视角的六个目标，可见门洞、五联窗、两扇圆窗、尖券窗和山墙顶。[三档轮廓与原生接缝](footprint-review.json) · [放置合同](final-placement-contract.json) · [两种屏幕高度的视线](overview-sightlines.json)

在上海项目目录中，以来源收据指定的宏区和一个空工作目录复核。

    python -B data/audit/hujiang-university-auditorium-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/hujiang-audit
    python -B data/audit/hujiang-university-auditorium-v1/check-openings.py --work "$WORK" --report /tmp/hujiang-audit/opening-rays.json
    python -B data/audit/hujiang-university-auditorium-v1/check-overview-sightlines.py --feature-table "$MACRO/feature-table.json.gz" --contract /tmp/hujiang-audit/final-placement-contract.json --report /tmp/hujiang-audit/overview-sightlines.json

正式城市目录从173处增至174处。两个实际HTTP服务返回的目录字节与各自冻结树一致，原有133个候选记录保持相同。[正式输入及SHA-256](production-snapshot.json) · [前后目录HTTP核对](predecessor-controls.json)

在实际174处站点的单体页，桌面与手机分别切换近、远模型，四种文件完成下载并核实SHA-256。两种屏幕能完整看见东北山墙屋尖、两排五格和门阶，远景保留窗框之间的浅色石带。[单体页](../../../hujiang-university-auditorium.html) · [四个实际视图及下载记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

## 173处前态与174处主地图

在173处前态，同一位置显示原有粗模。174处从目录选择主礼堂后，900×650桌面和390×844手机的默认画面都能看见红瓦、东北端五联窗和长墙。两端各在本页记录六个立面位置，均在视窗内，未被文字灯牌与控制面板覆盖。门前发光标记靠近门阶。原生近景组有六栋，仅2357使用两个裁剪三角面，北侧小堂的粗模保留在精模旁。[前态实图](city-24136/map-before.png) · [桌面默认](city-24136/main-desktop.png) · [手机默认](city-24136/main-mobile.png)

东北端近景可见五联窗上部和砖石轮廓，选中灯牌遮住下部门券附近。长墙图可辨相连的尖券窗、石带及两枚圆窗。保留源视图可见新旧屋面在小堂交接位置的高度差。缩至15.45级时，场景切换至20,004面的远景档，礼堂在城市总图中只占数个像素。门前小径和两侧草坪可通行，门阶、厅内与北侧小堂等八处实际碰撞返回均符合预期。[东北山墙](city-24136/northeast-five-lights.png) · [东南长墙](city-24136/long-wall-roundels.png) · [北侧小堂交接](city-24136/retained-source.png) · [城市远景](city-24136/distant.png)

前态实取并复核121项、76,247,758字节，后态实取并复核115项、42,364,003字节。四个模型文件按SHA-256复核；单体页已有近远双档和四次下载，与本版十三个文件逐件相同。桌面和手机默认取自同一正式版本的前次会话。执行器两次提前终止后态进程，最后一个会话核对原有图像哈希，并另存四个专题镜头、近远两种实瓦片及八处地面复核；全部浏览器已退出。[原始首轮](city-24136/interrupted-first-run.json) · [双端原始记录](city-24136/interrupted-defaults.json) · [完整实测](city-24136/main-map-browser.json) · [173处HTTP](city-24136/http-135.json) · [174处HTTP](city-24136/http-136.json) · [单体页跨版复核](independent-viewer-24136.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/28cc98f3bcfe88230cfb596dd8bbaa7e907d289f/projects/shanghai/index.html#landmark=yangpu-hujiang-university-auditorium&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
