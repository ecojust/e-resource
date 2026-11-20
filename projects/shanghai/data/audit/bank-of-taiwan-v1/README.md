# 外滩16号台湾银行大楼

2014年1月的街角照片可辨外滩东面的四根圆柱，以及九江路一侧六根方柱间的七开间。首版原生图中，入口基座没有接到相邻柱座，门背面也有一条石线穿过门扇。修订版补上两边的连续石基、中断门前石线，并把两面檐线接成完整斜角。[初版原生图](preflight/before-plinth-and-corner.png) · [修订版原生图](huangpu-bank-of-taiwan-building-preview.png) · [原始照片、保护名录和区志](../../../source/precise/huangpu-bank-of-taiwan-building/reference-review.json)

重开Blender后逐面核对99个网格、13种材质。网页近景54,008个三角面，远景26,008个。三档各检查88处真实首交点，涉及四根圆柱、六根方柱、七组三联高窗、门扇、檐角和2014年的招牌位置。[原生与两档解码比较](geometry-native.json) · [264次三维取样](wall-checks.json) · [逐点复查程序](check-street-elevations.py)

16号地块位于14-13720-6694宏块，对应228号源，当前底图的招商银行轮廓与之交并比98.88%。沿两条街切取164.61平方米以容纳立面，原近景保留776.29平方米，原远景保留770.98平方米。该近景组六栋中另外五栋的实际几何距裁切边10.79米。外滩15号、17号的独立精细网格分别与新模型保持8.31米、3.89米间距。三个收边墙段取自原远景与裁切边相交的位置。地面检查覆盖中央阶梯、石基、退入的门扇、九江路人行道和保留的西部。[地块与照片尺度复核](../../../source/precise/huangpu-bank-of-taiwan-building/footprint-review.json) · [配准参数](final-placement-contract.json) · [完整网格和11个地面探针](placement-geometry.json)

用实际地标相机拟合与两栋独立银行、同组近景及周边远景实网格试算桌面和手机。在−62°／37°的登记取景下，11,725个街面采样中，从模型自身可见的部分均未被邻体挡住。[各角度采样](camera-preflight.json)

在独立模型页上，桌面、手机均通过真实浏览器打开近景并切换远景，桌面还从下载入口逐一取得四件文件并校验散列。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [浏览器收据](viewer.json)

153处城市输入中的689项和4个实际底图文件共693项HTTP请求均匹配。原模型678个裁切三角分布于14个宏块纹理，单纹理最大263。两种矢量来源保留原楼后半及五个邻体，中央门阶与门后阻挡分别核对。[完整HTTP收据](frozen-http.json) · [生产运行时检查](runtime-placement.json)

原153处目录的首次手机画面中，建筑长灯牌遮住了东门厅两根柱身；展开目录的桌面画面四根都受到遮挡。独立对照站将取景放在四柱与街角，保留九江路成排窗带，并将灯牌移到石柱外。三个实测画面中，四根轴身与姓名牌的重叠均为0像素。[首次画面、修订对照及归档说明](final-map/four-columns/README.md) · [旧153处实图与地面](final-map/original153/main-browser.json) · [23115签名资源的HTTP正文](final-map/four-columns/accepted-http.json)

23115正式默认手机与桌面均完整露出四根柱身，街角和九江路一侧也在画面内。手机放大一级后右端出屏39个柱身像素，左柱有1,532个像素落入地点卡范围，四根柱子与姓名牌的重叠仍全部为0。[两端默认、触控放大与邻楼选中收据](final-map/four-columns/formal-23115/accepted.json) · [正式双端覆盖与首轮断言说明](final-map/four-columns/README.md)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/70830a591b5ccbe575c1f2a09a9363f3144f46da/projects/shanghai/index.html#landmark=huangpu-bank-of-taiwan-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 12 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
