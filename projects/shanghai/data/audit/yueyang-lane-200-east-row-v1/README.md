# 岳阳路200弄住宅临街锯齿立面

市房管局第二批2D029登记「住宅」，地址岳阳路200弄。2013年3月照片能辨白墙角窗的转角柱、挑出的混凝土窗头、窗外两道晾衣杆及斜撑、墙载窗机和铁栏黄柱。沿岳阳路2013年10月与2020年2月的街景拍到同一排住宅与园墙。这里只制作东端沿街排屋明晰可查的中央五个折角窗段，内侧14、16号附近的另一排、其余门牌和红瓦建业里分开保留。[2013年照片](sawtooth-2013.jpg) · [摄影署名](photo-credits.md) · [官方名录、两期街景和追踪细节](../../../source/precise/xuhui-yueyang-lane-200-east-row/registration-and-photo.json)

## 窗墙、园墙与原生文件

无遮挡的2016年屋照能沿东缘读出五段连续折角，并在西侧屋缘估计该截段约13.2至14.5米的深度。2018至2020年的部分发布图层重复了同一原始影像。三个居住层的窗台和上沿按实照比例估算，截面背墙保持素面。五折段长约22米，三个楼层分别制作独立窗洞、玻璃、框梃和窗头；近档包含已观察的窗外支架、空调机箱、风扇和部分栏杆。前院保留可通行的空间，屋内和未查明的房户均留待进一步资料。[窗位和屋面转折坐标](../../../source/precise/xuhui-yueyang-lane-200-east-row/source/parameters.json) · [早晚屋面图源](../../../source/precise/xuhui-yueyang-lane-200-east-row/roof-sources.json)

在 Blender 4.3.2 中独立重开207个网格、19种材质、21,456个有向三角面。原始、近景和远景各检验148个首达表面，包含转角窗、挑檐滴水、窗锁或远档玻璃、晾衣杆、临街铁栏及前院空隙。980×735像素原生图从街道南侧观察，四周余量依次为68, 132, 168, 128像素。[原生渲染](xuhui-yueyang-lane-200-east-row-preview.png) · [原生和材质逐面比对](geometry-native.json) · [三档射线记录](surface-probes.json) · [查看与四件下载](../../../yueyang-lane-200-east-row.html)

| 文件 | 字节 | 三角面 | SHA-256 |
| --- | ---: | ---: | --- |
| 原始 GLB | 1,467,104 | 21,456 | `a7fa4cf1cb52db7d762b2913e98d881ad1432a93f903a3e7b6d1ea7b1641901f` |
| 网页近景 | 664,968 | 21,456 | `8f304176a7d2c30cd1c8a9aa721942b35da95dd748ed502203f25651c54ce95a` |
| 网页远景 | 258,928 | 8,720 | `c016ea40b34dd6f3c903b4cbec636f383f156f73fa64b9a830dc683e51519425` |
| Blender 原件 | 294,740 | 21,456 | `2d909e4f5e1d291529bc78b65fbcaedfe673632c813d27cf7217dc487d64401f` |

## 现有城市原件与局部接缝

14-13719-6695宏块的4352号来自东亚建筑数据，原模型27.4米高度来自单一十米栅格观测。低层住宅在源图中仅得到局部罩盖。纳入五折窗墙所对应的纵向截段，保留原模型南北两端；近档留下39.07平方米，远档留下37.21平方米。近档13,148面属4352，其余九个地物合计101,894面，距裁切边界至少5.65米。住宅和铁栏单独计算碰撞，分别为310.59及5.25平方米。内侧4575、1858号门口小屋和北侧5547各自保留。14个点检查了原屋两端、园地、道路、实墙及铁栏。默认俯瞰在桌面和手机取景中检查了八处构件，已登记邻近屋顶的最小净空为8.55米；照片对位与原始数据均属近似定位。[实际三角网、保留范围及园墙](footprint-review.json) · [源底图与独立邻居](../../../source/precise/xuhui-yueyang-lane-200-east-row/registered-front.json) · [街侧相机与屋顶核验](../../../source/precise/xuhui-yueyang-lane-200-east-row/camera-preflight.json) · [四件与单体页HTTP](standalone-http.json)

正式城市图22154与22155分别收录191处、192处入口。两版151条早先候选记录一致。新版本逐项下载并核验1029份输入，共978,478,527字节。在正式运行模块中，4352号增加两个裁切面，原坐标内侧6米处确认从旧轮廓中移出，南北两端留下实体。两套矢量源分别核查本栋和九个邻居，共20项。原地与邻界共23个地面点通过。[正式目录变更](renderer-parent-controls.json) · [正式HTTP字节](renderer-release-http.json) · [运行时地面、邻户与剩余轮廓](renderer-runtime-placement.json)

22155的独立单体页在1250×820桌面和390×844手机上分别切换了近、远两档。近景21,456面，远景8,720面，五折窗墙与前园围栏在两种屏幕上均完整入画。四个下载控件保存的三种GLB和Blender文件逐字节匹配清单。[单体交互及四件下载](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)

整理城图记录时发现，早期清单中去除发布提交后的队列摘要与同一份清单指向的队列文件不一致。逐一从九个实际站点取回该文件，九份字节完全一致。保留原始清单，只重新计算这个派生摘要。原有39项提交记录、目录和全部文件摘要均通过核对。[原始清单](queue-fingerprint-review/original-snapshot.json) · [九站逐份核对](queue-fingerprint-review/verified.json)

在实测的191处前态，同机位可见未裁切的原楼。192处后态从街面可见五折窗墙、浅色层檐和前园铁栏，背后的原有长屋延续至两端。桌面、手机默认视角及键盘切换回本栋后，窗台、檐口和园柱八个见证点都在屏幕内，标签与界面均未遮挡。手机点一次放大后，南端一层窗点出了画面，西檐端点落入图例；另两张街面与屋顶近照中，侧栏和地点卡遮住了部分低处构件。远景切换、街面与屋顶细节和23个地面点均已现场核对。两代主图均无页面或请求错误。[主图前后实测](final-map-24155/results.json) · [桌面默认](final-map-24155/map-desktop.png) · [手机默认](final-map-24155/map-mobile.png) · [街面窗列](final-map-24155/map-street-facade.png) · [逐点屏幕检验](final-map-24155/screen-control-points.json) · [正式站1034个文件](final-map-24155/155-all-http.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 47 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/88ae16a73a68170009b803558aa667aeaa6d6b8a/projects/shanghai/index.html#landmark=xuhui-yueyang-lane-200-east-row&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 47 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
