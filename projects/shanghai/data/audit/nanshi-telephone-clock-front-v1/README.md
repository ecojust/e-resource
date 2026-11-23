# 上海电话局南市总局中华路钟楼立面

市房管局第三批3A024登记中华路734号。实物铭牌记1920年竣工；2017年街照中，主楼正面的大钟、钟台与深色穹顶均在原位。2019年发表的近照可辨方台正面四根柱、钟面指针、穹顶短平顶及第三层半圆窗两侧花饰。[照片和市表](../../../source/precise/huangpu-nanshi-telephone-exchange/reference-review.json) [单体查看](../../../nanshi-telephone-exchange.html)

以2019年近正面的塔檐宽201像素、金属屋顶高62像素校正穹顶。修正前的屋顶较尖，修正后的穹顶高度约1.73米。细杆顶高约24.86米，为照片推算值。前后模型保留在同机位对照图中。[照片坐标](clock-roof-proportions.json) [同机位首次推算](first-clock-study.jpg) [依正面校正](revised-clock-study.jpg) [地块及视高区间](../../../source/precise/huangpu-nanshi-telephone-exchange/source/frontage-registration.json)

近景30,826面，远景22,470面。三档各有130条实际射线，检查钟面、双指针、四正柱、半圆窗分隔与券肩、金属穹顶水平截面、街翼窗格及门前石阶。[实际网格](surface-checks.json) [原生重开](geometry-native.json)

按带名街坊图与两角度街景，将约22.12米宽的中央街面匹配到较长的东楼1473。原楼后部、东西街翼以及较短的西楼942保持原貌。局部替换后，远景保留476.27平方米，近景保留482.26平方米。31处地面探针检查临街墙身、石阶及可通行的沿街地面。[近远裁切](source-cut.json) [接墙与地面](placement-geometry.json) [两套矢量与邻屋](vectors/initial-correspondence.json)

站在街对面最高的1890号普通楼前投影时，旧候选角度使十处建筑识别点都被挡住。调整后的方位158°、俯角42°从巷口看向街面，两个视口的十处识别点均有可见视线。[比较两端视线](camera-sightlines.json)

正式31261和31262分别登记296、297处地标。新版的1,914份输入逐件下载，共1,557,845,429字节。对照两种矢量底图，钟楼局部在两份底图各裁去约90.27平方米，同一聚合内另外13块和周围20幢独立原楼保留。[两代运行时](final-renderer-31262-http.json) · [两个底图的逐件比较](vectors/final-261.json) · [完整HTTP记录](31262-all-http.json)

桌面和手机独立页各操作了近、远两档，四个按钮下载的文件均与原件一致。钟面、方台立柱、收分穹顶，以及长檐下的中央半圆窗在四幅图中可辨。街景原照的树冠遮住底层中部，门洞下半部的形状仍按模型来源说明的推算范围记录。[桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [实测与下载](viewer.json)

## 正式城市地图复核

在加入中华路734号钟楼之前，296处建筑的目录中没有南市电话局。旧城同位置可见平屋面和周边窗排。加入后，桌面与手机分别从297处建筑的目录进入，另各从地图上的楼名实际点入。手机画面中钟楼处于密集街屋之间，桌面可同时辨出邻近的清心堂标签。四次进入均显示中华路钟楼立面对应的资料卡。

街面斜视可见三层窗排、中央半圆窗与上方方形钟台。屋顶视角可见弧顶、顶端逐层收小的饰件和方形底座。钟面近图可辨指针、圆周刻度和左右柱。中央拱窗近图可辨上部半圆及竖梃，左右各一扇直窗。页面原有的模式按钮与资料卡遮住部分窗框和钟面，随各场保存的 WebGL 原帧可连贯查看这些细部。

在东西七个位置，逐排检测临街人行处、墙线、街面楼身及后部保留的原建筑，并单测门阶、门阶两边通行处和内部楼面。32个本址点及20个邻栋点均符合原图层，七段局部墙线保持可见。邻栋的落点仍命中各自的原楼。

远景拍摄时，实际摄像机距钟楼866.30米。本站登记的远档切换距离为755米。画面中可辨中华路的弯线、周边街块和建筑编号，钟楼缩到街区尺度。同期浏览器记录确认已载入22,470个三角面的远景文件。[远景原帧](city-31262/actual-browser-phases/distant/map-distant-webgl.png)

独立页面在桌面1250像素和手机390像素宽度各查看正面、斜向及俯看，一共六幅。两端均可辨入口台阶、中轴拱窗和屋顶钟座。四个下载经页面实际保存并复读，原始GLB为1,740,040字节，网页近档643,804字节，远档457,660字节，可编辑Blender文件512,002字节。[六幅照片逐张记录](city-31262/current-standalone/manual-visual-review.json)

[实机、地面与四种下载](city-31262/process-exits.json) · [旧城对照](city-31262/map-before.png) · [中华路钟楼正立面](city-31262/map-zhonghua-clock-street.png) · [钟面与角柱](city-31262/map-clock-face-and-columns.png) · [远档](city-31262/map-distant.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/b019d0cee4158dc0c1e42662b94d101d34fc2572/projects/shanghai/index.html#landmark=huangpu-nanshi-telephone-exchange&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
