# 扬子大楼外滩26号临江东立面

市房管局第三批优秀历史建筑名录3A001登记扬子大楼、扬子水火保险公司，地址黄浦区中山东一路26号。南邻24号横滨正金银行、北邻27号怡和洋行。1927年出版的外滩街景能在两栋之间看见26号的五轴窗列、六层柱廊与两侧屋顶窗体。1908年拍下的是同址三层前身。区志与建筑专志的年份有出入，分别列在制作说明中。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [1927年照片](https://commons.wikimedia.org/wiki/File:Shanghai_of_Today,_Plate_12_-_Bank_of_China,_Bank_of_Yokohama,_Messrs_Jardine,_Matheson,_%26_Co,_Glen_Line.jpg) · [日期与照片资料](../../../source/precise/huangpu-yangtze-insurance-bund-front/README.md)

模型按近年临江实照绘制。下部门洞和券窗有真实进深。五层窗头与外挑檐口、六层三间双柱廊与后窗、七层两侧高窗和中部退台分别建模。街面门牌可与现行OSM建筑177931019的26号及2014、2025年街景对照。行名字样取现状，构件尺寸及雕花为外观估算。南北侧面、西侧后部、屋顶设备与早期三层旧楼分列。[现状正面](https://commons.wikimedia.org/wiki/File:Yangtze_Building_The_Bund.JPG) · [三楼同框](https://commons.wikimedia.org/wiki/File:Yangtze_Insurance_Building_20251127.jpg) · [单体页面及四件下载](../../../yangtze-insurance-bund-front.html)

地点采用具名源面2937的东侧轮廓与原近、远网格。核对源面、现行OSM、三期航片和相邻已建楼的部分替换边界。切面位于街墙后3.88米，南北通道及后部原楼保留。回退矢量116367860合有28个多边形。复核程序分别测量26号东侧变化、同一对象其余27个多边形、24号与27号的既有状态。[轮廓对照](../../../source/precise/huangpu-yangtze-insurance-bund-front/footprint-review.json) · [航片来源](../../../source/precise/huangpu-yangtze-insurance-bund-front/roof-reference.json) · [共享地块校验程序](check-vector.mjs)

底图自身的近景包含13,908个三角面，最高22.40米，立面为重复矩形窗格。按同一坐标投影，现状正立面的顶层双窗亭、柱廊及两侧入口均有独立构件，旗杆顶按照片估至37.92米。图中的左侧是既有近景，右侧是本次表面模型；左侧统一着色以比较轮廓和实际几何。[同尺度东立面对照](original-and-proposed-elevations.jpg)

## 成品几何、地面与实拍

原始与网页近景各23,240个三角面，简化远景14,568个，Blender工程重开后核对147组可编辑构件。首次重开时两处六层栏杆的组件名超过Blender的63字节上限，改短名称后重新导出四件并再度重开。三份交付网格各以77条射线复核石券、门窗、柱身、后窗、屋顶和两侧巷口。[原生核对](geometry-native.json) · [三档构件射线](surface-checks.json)

地面验了21处，另核12座邻楼。原近、远景保留的源面比例分别为87.68%、87.85%，切面只生成一道端盖。街道视角与屋顶视角各9处采样可以看到目标构件。独立页在1250×820桌面与390×844手机上都实拍正面、斜面及远档俯视，近远模型都完整入框；五轴窗墙、上层的退台和两侧高窗在手机竖屏仍可分辨。四件均经实际下载并核对散列。[地面与原网格](placement-geometry.json) · [视线抽查](overview-sightlines.json) · [实拍与下载凭据](viewer.json) · [桌面正面](viewer-desktop-full-front.png) · [手机斜面](viewer-mobile-full-oblique.png)

[原始GLB](../../../assets/models/candidates/huangpu-yangtze-insurance-bund-front/huangpu-yangtze-insurance-bund-front-raw.glb) · [网页近景](../../../assets/models/candidates/huangpu-yangtze-insurance-bund-front/huangpu-yangtze-insurance-bund-front-web.glb) · [远景](../../../assets/models/candidates/huangpu-yangtze-insurance-bund-front/huangpu-yangtze-insurance-bund-front-lod.glb) · [Blender工程](../../../assets/models/candidates/huangpu-yangtze-insurance-bund-front/huangpu-yangtze-insurance-bund-front.blend)

正式地图归档含276个地点。31239服务按生产清单实取1,722件、1,402,450,793字节，并核对范围读取。黄浦区的扬子大楼卡片唯一，可进入临江东立面的单体页，也可进入普通地图总览。[整站回执](production-31239-all-http.json) · [地点卡、页面和目录](final-layer-http.json)

[正式地图与单体页的脚本、样式及分段请求核对](formal-31239-runtime/README.md)

## 外滩26号在第239期正式城区中的实测

正式目录由275处增至276处。普通目录和地图灯牌分别用桌面鼠标和390像素手机触屏点选。外滩东面街景核对南北入口、中央三轴窗、通高壁柱、阳台与退后阁楼，21处街面与12栋邻屋逐点复查。远近档和四次资产保存均读回至本机，12张城图与6张独立页图分别记录实际可见内容。[真实退出与逐段报告](final-map-31239/slot-released.json) · [逐图观察](final-map-31239/visual-review.json) · [地面和专项取景](final-map-31239/architecture/main-browser.json) · [全站实取](final-map-31239/all-http.json)
