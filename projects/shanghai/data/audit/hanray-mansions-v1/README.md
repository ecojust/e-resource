# 亨利公寓淮海中路立面

淮海中路1162号沿街入口退在两面弧墙之间。二层以上的中央竖带一直接到顶部浅弧冠，两翼各有成排横窗，七、八层的圆角露台逐层收进。首版把中心放得过深，露台贯穿了中轴。比对街面和高位照片后，重做了从二层到屋顶的中央窗列、竖带、帽顶和露台交接。窗高与露台半径按照片比例估计。[实景资料](../../../source/precise/xuhui-hanray-mansions/reference-review.json) · [首版](draft-review/first.jpg) · [修订版](draft-review/revised.jpg) · [修订记录](draft-review/revision.json)

近景模型有31,512个三角面，远景有22,220个。Blender工程重新打开后有105个可编辑网格，几何与原始GLB相符。原始、网页近景和远景版本各检查127个位置，包括玻璃与金属窗框的深度、门槛、两层露台的开放面、中央竖带和高窗。[工程检查](geometry-native.json) · [三档材质和射线](surface-checks.json)

地图原始建筑3240的近景有17,712个三角面，远景有72个。仅裁去沿街前部，保留近景屋面投影的59.49%和远景的59.64%。最近的同组邻楼距离裁线4.72米。核对了17个街面、门口与楼体点位，以及8栋邻楼。[配准](placement-geometry.json) · [街面机位](../../../source/precise/xuhui-hanray-mansions/camera-preflight.json)

独立页提供网页近景、远景、原始GLB与Blender工程四种下载。[查看模型](../../../hanray-mansions.html) · [HTTP核验](standalone-http.json)

独立查看页经本机43433端口直接提供制作目录原件。1250×820桌面和390×844手机均通过页面上的三个按钮切换临街正面、斜向露台和俯视，再切换远档，留下八张画面。正面能看到中央竖带分开两翼横窗，俯视可辨七、八层退台和端部圆角。桌面上的原始、近景、远景及Blender四个下载均取得完整文件。随后从收录241处地标的25204正式测试站重新读取独立页面、清单、查看器脚本、样式和四项模型，八份内容与实测使用的原件逐字节相同。[两端实测与下载](viewer.json) · [桌面正立面](viewer-desktop-full.png) · [手机露台俯视](viewer-mobile-full-above.png) · [作者站输入](viewer-parent-inputs.json) · [正式站复核](viewer-release-inputs.json)

第241处地标登记后，正式测试站的1,435项输入共1,235,220,744字节，全部与签名相符。城市运行时复查了底层碰撞和保留地块。最初落在弧墙端点的一处点位受坐标投影精度影响，两套算法结果不同；把左右检查点移到各自弧墙中段后，从3.51米高度向下都在2.99米处击中浅色石墙。原地面障碍轮廓保持同一份摘要，正式运行时的17个本栋位置和8栋邻楼核验一致。[完整HTTP实取](registered-241-http.json) · [运行时配准](runtime-placement.json) · [弧墙检查点](draft-review/entrance-endpoint.json)

## 淮海中路1162号城市地图实测

从收录240处地标的前一版到收录241处的版本，在同一地点、角度和440×380画幅中，沿街底模换为中央内凹、两翼横窗的亨利公寓。390×844手机可见门框至上部退台，普通桌面展开目录时右上退台受地标牌部分遮挡。另在东湖七号楼画面，以鼠标和触屏各点一次亨利公寓的实地灯牌，均进入本栋详情并读到31,512面的网页近景。[前后同机位](city-31204/paired-street-view.json) · [手机](city-31204/phone/map-mobile.png) · [桌面](city-31204/desktop/map-desktop.png) · [鼠标](city-31204/physical-mouse/main-browser.json) · [触屏](city-31204/physical-touch/main-browser.json)

门口斜照能区分两边返墙、玻璃下扇、门槛和铺地，上亮的一部分被牌遮住。右端近照能读到前后两道曲线退台，底部中央有资料卡遮挡。远视距实际载入22,220面的模型，地标牌与街区在此视距更显眼。街面检查还逐点核对了25处入口、楼体和邻屋地面。桌面、手机分别从正式独立页切换近远档，四个下载控件保存的文件与发布清单一致。原先较窄的画幅和中断的浏览过程均保留了原始字节及校验值。[入口](city-31204/threshold/map-entrance-and-door-threshold.png) · [退台](city-31204/terraces/map-stepped-curved-terraces.png) · [远景](city-31204/distant/map-distant.png) · [实点](city-31204/street/main-browser.json) · [四次下载](city-31204/standalone/viewer.json) · [原始尝试](city-31204/previous-attempts/archive-index.json)
