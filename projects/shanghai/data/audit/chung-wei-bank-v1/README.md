# 中汇大楼

模型重建延安东路143号现存楼体。北端六级退台、金属桅杆、河南南路长街面的连续浅色窗带和阳台按2015与2024年照片估绘。全模型含45,204个三角面，Blender场景有114个可编辑网格。远景保留窗洞、外框和水塔轮廓，合并窗扇小分格后为35,552面。原始、网页与远景模型各实测84条射线，覆盖七层主要窗带、阳台扶手、北门、塔楼开口及桅杆。[照片、建筑沿革与估计范围](../../../source/precise/huangpu-chung-wei-bank-building/README.md) · [三档模型实测](surface-probes.json) · [可编辑模型核验](geometry-native.json)

原生地块为14-13720-6694的830号。近景同组的1445号建筑保留，替换边界与其实际原网格相隔33.352米。西侧96号地块的最小间隙为1.140米。另一底图把银行和约785米外的一块建筑合入同一41米高记录，实际裁切只去掉银行，保留远处面积和相邻5米高建筑。地理编码另将德士古大楼定位在东北侧约319米处。[原生三角面与碰撞实测](placement-geometry.json) · [另一底图裁切](vector-source-checks.json) · [放置合同](final-placement-contract.json)

156处原场景的已登记替换轮廓及早期模型保守包围范围都在中汇地块以外。距离最近的是德士古大楼（延安东路110号弧形街墙及入口），两者最小间距319.01米。[登记前156处轮廓复核](existing-map-coverage-156.json)

正式157处场景的独立页面在1250×820桌面及390×844触屏下显示弧形端部、连续横窗和分级退台塔顶。两档均可切换，四个下载的长度、文件名和散列都与资产清单一致。[网页与下载复查](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

156处旧场景在银行原址载入830与邻楼1445，两者均未裁切。157处正式主图从目录选中中汇大楼，1280×800桌面与390×844手机均能看到北端红色逐层退台、桅杆和河南路横窗带。三张近景载入了这两栋的真实原生组，仅830应用替换，10个实地点、四件实际下载、167个场景资源及4个目录生成文件通过。远景切换到35,552面模型。[旧场景](map-before.png) · [桌面](main-desktop.png) · [手机](main-mobile.png) · [北塔近景](north-stepped-water-tower.png) · [屋顶](filled-central-roof.png) · [远景](distant.png) · [浏览器记录](main-map-browser.json) · [输入签名](main-map-inputs-verify.json)

首轮河南路单独放大的视线穿过保留邻楼1445，图里只能看到前方建筑的灰色网格窗。已按原生轮廓和高度算出路内镜位，可从街道一侧看到红色窗间墙及浅色横带。[遮挡对照](henan-road-window-bands.png) · [五个窗位的视线计算](henan-street-camera-probes.json) · [逐图目检](main-map-visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/618d997f6e77a47116c229fe85705e69134956c3/projects/shanghai/index.html#landmark=huangpu-chung-wei-bank-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
