# 淮海中路1634号花园住宅院内柱廊与错层入口

市房屋管理局登记号2D009对应淮海中路1634号花园住宅，登记时由市科技情报所使用。两篇专题中的四个图片文件来自相同的两幅院照。院内总景可辨方柱、花铁围栏和红瓦坡屋，近照可辨高石阶、入口双扇门和右侧低门。门边小牌文字及屋后开口缺少可读资料。[来源与门牌](../../../source/precise/xuhui-huaihai-road-1634-residence/README.md) · [照片、航片与编号](../../../source/precise/xuhui-huaihai-road-1634-residence/reference-review.json)

该工程重新打开后有82组可独立编辑的网格与12种材质。原始及网页近景各有26,824个三角面，远景有10,732个。三个GLB各通过38条表面射线，核到方柱、石阶、栏杆、门扇与屋面。模型长度约18.74米，宽14.59米，高7.39米，均按院照和航片估算。 [原生重开](geometry-native.json) · [模型预览](xuhui-huaihai-road-1634-residence-preview.png) · [三档表面核验](surface-checks.json) · [与原照对读](visual-review.json)

冻结地物2222直接继承有门牌及保护编号的OSM建筑495925675第4版，两轮廓的交并比为97.98%。院侧裁面以外，近景保留151.04平方米、远景保留146.63平方米的原楼体。最靠近的邻栋1670在近、远两档分别离裁面1.47米、1.57米。其余1167、2055、3654三栋与替换边界也没有交集。13个地面点分别覆盖石阶、围廊基座、院地、台阶旁空处及西北原楼。两段剖切面以源楼原高6.40米封合。[地块及邻楼来源](../../../source/precise/xuhui-huaihai-road-1634-residence/footprint-review.json) · [近远档与地面](placement-geometry.json) · [接入参数](final-placement-contract.json)

初次裁切在南侧栏杆前方留下一条狭长底图墙。依据院照把南裁面移至原地物南侧边界以外，四邻仍完整保留。复核桌面和手机视线，均能从庭院看见高低门、石阶、扶手、两根廊柱和南栏、屋脊八处。[初次视线](preflight/first-city-sightlines.json) · [修正后视线](camera-sightlines.json)

[单体查看与四件下载](../../../huaihai-road-1634-residence.html) · [交付文件签名](../../../assets/models/candidates/xuhui-huaihai-road-1634-residence/manifest.json)

独立查看器的桌面和手机各实拍了正面近景、庭院斜视和正面远景。正面可辨方柱开间与花铁栏杆，庭院斜视能同时看到基座上的柱廊、高台阶双门及右侧低门。窄屏全貌里最细的铁花和小牌难以辨读。四个下载均由实际按钮保存后核对文件长度和SHA‑256。[查看器实拍与下载](viewer.json) · [桌面庭院](viewer-desktop-courtyard.png) · [手机庭院](viewer-mobile-courtyard.png)

初始253和254处场景沿用同一版旧裁切实现，完整载入全市裁面时都超过了该版上限。继承分页实现后，26217渲染站的全市裁面从1,578增至1,580，共使用21张分区纹理。两个矢量来源均取到2222的保留轮廓，10个矢量项目和17个地面样点通过。四个派生站分别以实际HTTP核对了查看页、下载和依赖共15个文件。[原始两站的同项记录](preflight/raw-parent-and-candidate-runtime.json) · [最终渲染检查](city-26217/runtime-placement.json) · [渲染输入](city-26217/direct-runtime-inputs.json) · [四个派生站的查看器与下载](served-viewer-and-downloads.json)

四条服务线全部逐项取回后，23217站1,536项、24217站1,538项、25217站1,540项、26217站1,540项的SHA-256均与各自的发布签名一致。[逐站传输量和签名](all-renderer-http.json)

最终相机更新后，分别在253处和254处两个地图版本复查了目录、相机模块和原始近远景网格。第254处的单体页面、查看器脚本、模型清单和四个下载均与原实拍所用文件一致。最终站逐项读取1,540个文件、1,303,544,339字节，五组范围请求均返回206。[前后站HTTP实测](city-28217/real-28k-predecessor-and-new-building.json) · [最终站完整核验](city-28217/after-all-http.json)

正式地图先从253处旧城取图，再经普通地标目录打开254处新城。手机默认图能看见整座住宅，桌面能认出红瓦坡顶和外廊。庭院近景能辨方柱与栏杆。东入口的专项视角受屋顶和地点卡遮挡，只露出部分门墙。独立页庭院视角保留柱廊与错层门墙的相对位置。17个地面与邻屋点、鼠标和触屏选择、近远档切换均已复核。桌面捕获曾三次发生渲染进程中止，第四次成功，并保留前三次的原始日志与退出记录。[逐图观察](final-map-31217/manual-visual-review.json) · [正式地图结果](final-map-31217/results.json) · [桌面庭院斜视](viewer-desktop-courtyard.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/be01bf87212410bb03f92607650c3c158c473043/projects/shanghai/index.html#landmark=xuhui-huaihai-road-1634-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
