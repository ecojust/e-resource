# 乍浦路桥的模型验收

桥体长71.94米，两端短跨各17.68米，中跨36.58米。2010年与2014年的原图可对照三孔、两处墩头、梁下缘和上游四块绿色桥名牌。近景的“乍浦路桥”四个字均有独立几何，远景保留牌面。四种文件的472条射线分别检查了每个桥孔、栏墙、人行道、可见墩头和桥名牌。原生文件重开后有80个可编辑网格。[模型范围与实物照片](../../../source/precise/huangpu-zhapu-road-bridge/README.md) · [四种成品的实物射线](bridge-surface-checks.json) · [原生预览](huangpu-zhapu-road-bridge-preview.png)

桌面和手机均通过桥头、河岸斜视及俯视入口，四种下载按文件长度和SHA256比对。在河岸画面中，最长的中央桥孔与两侧短孔可辨，两个墩头从梁缘向河面收分。地图定位沿具名道路和桥面轮廓，已用周边近远景和相邻两座已建桥的三角面确认桥区相互分离。[桌面河岸视角](viewer-desktop-oblique.png) · [手机河岸视角](viewer-mobile-oblique.png) · [俯看桥面](viewer-desktop-above.png) · [查看器实测](viewer.json) · [邻近网格与河面记录](retained-neighbor-clearances.json)

在267处入口的开发主图上，重新读取近、远两档桥体和地图当前使用的矢量瓦片。沿乍浦路桥的两侧人行道和车道往返共12次，54处模型采样中，行人脚底与实际桥面的最大差为0.41毫米以内。另与四川路桥、外白渡桥一起检查三桥切换，在16组近远档及加载组合中逐一检验576个位置和道路编号，桥外保留原道路与水域。[桥上行走](signed-stations/walk.json) · [共用人行道编号](signed-stations/shared-sidewalk-id.json) · [漫游起点与朝向](walk-entry.json) · [地图与模型版本](signed-stations/summary.json)

随后在同一267处入口的开发版本中，从单体页面完成桌面和手机八个画面、四个下载的复核。上游斜视可分辨三孔与两处墩头，俯视可见车道两侧抬起的人行道及栏墙。[桌面上游视角](viewer-28230/viewer-desktop-oblique.png) · [手机俯看桥面](viewer-28230/viewer-mobile-above.png) · [已查看画面与下载](viewer-28230/observed-review.json)

可用 Python 和 Node.js 在相同模型版本上重跑行走检查。在本地提供该版上海站点后，运行 `python signed-stations/replay.py http://localhost:8000/`，网址指向含 `index.html` 的上海项目目录。程序核对目录和运行模块的 SHA256，再读取六个桥模并比较三桥的实际通行结果。[复验脚本](signed-stations/replay.py)

用桌面键盘 Enter 和手机触控分别从按区目录打开“室外漫游”，浏览器两次都到达乍浦路桥的漫游网址。前一版本的266处目录保留作对照。这项复验记录的是目录跳转，桥面高度与通行另见上面的运行记录。[键盘与触屏跳转](directory-28230/actual-link-actions.json)

### 正式全城地图与独立页

上一期原站宽屏图中可见原河面与道路。[第229期地图实景](city-31230/before-wide/old-water-and-road.png)　正式站的地点目录从266处增至267处。桌面用鼠标、手机用触屏，从普通目录和地图灯牌打开乍浦路桥。两端都实测了进入、离开和返回；操作记录保留在各自的步行报告中。正式相机另对两处墩头、两块桥名牌、梁底、桥面及人行道共九个位置核对了屏幕边界与周边楼体。[桌面和手机取景记录](city-31230/ordinary-cameras.json) · [手机目录选择后的桥景](city-31230/phone/map-phone.png) · [桌面灯牌选择后的桥景](city-31230/mouse/map-mouse.png) · [前一版本的同址河面](city-31230/before/map-before.png)

从虎丘路一侧西人行道出发，桌面在660×410的紧凑窗口内用键盘走到北岸，手机用触控摇杆在桥上移动。过桥实拍使用原地图的低分辨率渲染，桥面斑纹与远处楼体细节较模糊。把真实行走轨迹逐点投到当时加载的近景或远景桥面三角形，两端最大高度差为0.0005米。已归档的三桥通行条件还在此次正式站上复验了36次通行、162个桥面位置及576项道路归属。[桌面到达北岸](city-31230/walk-desktop/map-north-bank.png) · [手机桥上行走](city-31230/walk-phone/map-touch-walking.png) · [桥面三角形与实际轨迹](city-31230/sessions/walk-desktop/real-city-mesh.json) · [三桥运行复验](city-31230/replayed-signed-navigation.json)

独立页分别在桌面和手机切换近远档、上游斜视与桥面俯视，两端共八幅图，四个文件均通过页面下载并校验。正式站共读取1,650份文件、1,356,372,864字节。21幅常规图与一幅前期宽屏补图均逐张核验。[桌面上游斜视](city-31230/standalone/viewer-desktop-oblique.png) · [手机俯视桥面](city-31230/standalone/viewer-mobile-above.png) · [逐图观察](city-31230/visual-review.json) · [全量读取](city-31230/all-http.json) · [正式收件与四个下载](city-31230/slot-released.json)
