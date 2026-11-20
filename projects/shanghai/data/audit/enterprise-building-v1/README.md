# 企业大楼 · 原中国企业银行大楼

四川中路33号在市房管局第二批名录2A046登记为企业大楼，公布时使用单位为轻工业局。项目工作表写作“创业大楼”，沿街门牌也是这四字。上海市文化和旅游局与上海市银行博物馆资料记载，这座八层办公楼于1931年建成，中国企业银行于当年11月12日开幕。银行使用一层，上层由不同机构使用。地图标签和部分二手记录另有1920年、九层之说。[来源、门牌和年代](../../../source/precise/huangpu-enterprise-building/reference-review.json)

七开间的东面沿四川中路展开。两层通高的银行营业层以上，六排普通办公层各有七组三联窗。黄褐面砖、竖向壁柱、双折纹窗裙、后退的中央入口、阶梯女儿墙及南侧露出的转角由照片交叉确定。尺寸、砌缝和屋顶服务体量为估计；现有资料没有覆盖背部全貌及历史营业厅内部。[范围与证据](../../../source/precise/huangpu-enterprise-building/README.md) · [门头细部](street-door.png) · [阶梯冠部](stepped-crown.png) · [原生总览](huangpu-enterprise-building-preview.png) · [像素复核](native-visual-review.json)

原始模型与网页近景各80,680个三角面，远景45,904个。Blender重新打开原生文件后，逐材质核对51个可编辑网格的面。三份GLB各独立检测173条射线，共519项，涵盖办公窗、营业层玻璃、门洞、窗裙和街道外空域。[原生核验](geometry-native.json) · [三档表面记录](surface-checks.json)

冻结城市图中，目标为宏块14-13720-6694的874号源，面积约1,060.14平方米。实测近景23,840个目标面和远景20个目标面均覆盖在裁剪范围。同组的48,532个近景邻面和88个远景邻面完整保留。地面检查包含中央门槛、闭合的玻璃门、南侧凹口、北侧通道和西侧服务空间。[源面及邻界](../../../source/precise/huangpu-enterprise-building/footprint-review.json) · [落位合同](final-placement-contract.json) · [近远景及地面核验](placement-geometry.json)

在1250像素桌面及390像素手机上，实际打开四川中路立面并切换近远两档。独立页的原始GLB、网页近景、远景与Blender原生文件均下载并比对字节及SHA-256。[独立模型页](../../../enterprise-building.html) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [浏览器与四项下载](viewer.json)

企业大楼加入后的城市目录共138处。运行时实际分配581个裁剪三角面，分布在13个宏块，单块最多219个。本楼新增四片；同组其余建筑在原有边界内保持完整。[运行期裁剪与地面结果](runtime-placement.json) · [138处登记及输入指纹](production-snapshot.json)

真实地图在前态137处与后态138处分别加载。四川中路同一机位的前照记录了874号原生源。交付后，从手机目录卡进入时可看清七开间立面与中央门厅；桌面默认的相邻标签遮住首层局部。收起侧栏后的街面近照可辨六排窗、竖向砖柱与内凹门廊。另核对了屋顶及简化远景、本楼10个地面点和5个邻楼点。两端原生远近瓦片、正式模型四项下载与浏览器错误记录均已核验。[前态原始视图](map-before.png) · [137处前态记录](control-browser.json) · [手机首屏](map-mobile.png) · [桌面街面](map-street-facade.png) · [屋顶](map-roof.png) · [远景](map-distant.png) · [138处实景及通行检查](main-browser.json)

两版目录通过真实HTTP逐项比对。原有97个候选行保持相同，增至98个候选行，并与40处既有入口一同列入新版目录，成品的相机与裁剪等于审计合同。[17项共享入口、四项下载与目录收据](137-138-preflight.json) · [复验程序](check-release-inputs.py)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/fefc6f56bc8c24cd5cd310ef239aa116a5dde7b8/projects/shanghai/index.html#landmark=huangpu-enterprise-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
