# 望德堂西入口与南侧山墙

从院内看，入口有六级石阶、深圆拱和门上悬挑的小阳台。转过西南角，则能看到较宽的圆窗山墙、三扇高低不同的小拱窗和临北京西路的窗列。2016、2017年院内照片提供了门廊和悬挑阳台的依据。2021年2月两个街景拍摄点确定了南侧长墙的位置。[模型与重建说明](../../../source/precise/jingan-wangdetang-augustinian-office/README.md) · [照片与门牌记录](../../../source/precise/jingan-wangdetang-augustinian-office/reference-review.json) · [航片、街景与地块](../../../source/precise/jingan-wangdetang-augustinian-office/site-and-roof.json)

中国地方志记载的奥斯定会办事处地址为北京西路1220号。市房管局保护名录把望德堂列在1220弄2号。方志所记1894年指该会在沪设立办事处。2016年图文把这处住宅的建造时间记作1930至1932年，院内账房与祈祷室的位置仍待档案确认。平面依据已定位的建筑边线，西侧约12.55米。楼层、栏杆、弧窗和檐口尺寸由照片估算。住宅东部、院落其余房屋和室内陈设另行留待有据时制作。[市级名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [《上海宗教志》](https://web.archive.org/web/20131219141831id_/http://www.shtong.gov.cn/newsite/node2/node2245/node75195/node75203/node75283/node75297/userobject1ai91966.html)

近景与原始GLB各含23,672个三角面，远景15,596个。可编辑文件保留102个具名网格。三种GLB各自验证49个表面或留空点，含入口拱顶与两肩、圆窗和弧边窗帽、高低不同的三扇拱窗、临街横窗及外侧留空。匾下短线脚在拱口之外，拱顶与两肩可从正面直接看到后退门廊。[四件清单](../../../assets/models/candidates/jingan-wangdetang-augustinian-office/manifest.json) · [原生重开及几何对照](geometry-native.json) · [147项实物检测](surface-checks.json) · [券门细部](western-portal.jpg) · [拱顶实图检查](native-visual-review.json) · [原生预览](jingan-wangdetang-augustinian-office-preview.png)

本栋落在冻结地块786。新几何仅覆盖旧房的西入口及南墙西段。原近景保留190.47平方米、远景保留187.87平方米，约占各自原投影的七成。相邻773、404在两档内均无裁剪。原房31.25米高的余部与新几何之间采用中性剖面衔接。16个地面见证涵盖门前、建筑本体与原楼保留部分。在周围原生楼体保留的条件下，方位8°、俯角31°的预选相机在桌面取得1,496条可见射线、手机1,539条，各自全部通过。两端各有48条落在门廊、240条落在双山墙、20条落在侧面扇窗。[落位合同](final-placement-contract.json) · [源三角面和地面测量](placement-geometry.json) · [相机预检](camera-preflight.json)

正式228处地图中，本栋在源近景组只向786号原楼分配4个裁剪三角形。全城1,242个裁剪三角形分属20个宏块，最大表322个。两类矢量底图与保留邻楼也分别检查。正式服务1,327个输入合计1,131,457,280字节，全部经HTTP重新取回并核对SHA-256。独立模型页在1,250像素桌面及390像素手机分别展示近远两档，四种下载都与清单匹配。[地图运行时](runtime-placement.json) · [全站输入](release-23191-http.json) · [独立页画面与下载](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

## 西入口与北京西路转角的地图实测

从227处的前一版打开原址，再从228处的正式目录进入望德堂，桌面与390像素触屏均能选中同一地点。默认视角可辨双山墙和南侧相接的窗墙。西入口的圆拱、门上小阳台与南侧窗列在院内近景中更容易分辨。西面照片保留了前景相邻构筑物，临街视角下方仍有地点卡。两张近景使用同一地图中的既有几何。[原址对照](city-31191/before/map-before.png) · [桌面](city-31191/after/map-desktop.png) · [手机](city-31191/after/map-mobile.png) · [西入口](city-31191/courtyard-detail/map-entrance-porch.png) · [南侧山墙](city-31191/courtyard-detail/map-south-gable.png)

近远切换、四件文件与18个地面探点均已实测。仅786号旧楼进入本栋裁剪，保留的旧楼体从屋面视角可见，773和404号邻楼仍在。早期两次加载遇到本地底图缓存空间不足。按原始数据的哈希恢复后，重开浏览器取得前后态、桌面与手机画面及近远档记录，各轮退出码为零。[屋面](city-31191/after/map-roof.png) · [远景](city-31191/after/map-distant.png) · [前后态与地面见证](city-31191/after/main-browser.json) · [原始失败与恢复记录](city-31191/recovery) · [逐场退出记录](city-31191/separated-sessions/six-session-exits.json) · [入口近景记录](city-31191/courtyard-detail/main-browser.json)
