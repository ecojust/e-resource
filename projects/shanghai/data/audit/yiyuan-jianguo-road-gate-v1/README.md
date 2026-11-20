# 懿园建国西路南门核验

可编辑场景在Blender 4.3.2重新打开后，逐材质比对了41个网格、12种材质、47,380个三角面。远景26,988面。原生图可见小拱后方的空隙与东墙五个通孔；筒瓦的下口和檐下阴影分别可见。[原生渲染](xuhui-yiyuan-jianguo-road-gate-preview.png) · [原生及三档输入校验](geometry-native.json)

向门牌字、铸字、黑铁杆、金色卷草、拱腹、两种筒瓦和墙孔各档投射129条射线，共387次。测试同时覆盖实体和应能穿过的空隙。[逐项射线](surface-checks.json) · [照片与尺寸依据](../../../source/precise/xuhui-yiyuan-jianguo-road-gate/README.md)

底图两组近景建筑及整块远景与模型的最短净距为4.49米。底图轮廓610、3896、4886、818、2108分别保留。桌面及390像素手机相机都能看到门牌和两扇铁门。[实测网格间隔与地面](placement-geometry.json) · [相机视线](camera-preflight.json)

第一次套用封闭整道街门的步行检查，在150次中有一次走到了院内。回放该次实际脚步，20帧冲刺时沿西柱滑过去，在本地横坐标−2.73米处穿过敞开的小拱。复核保持原碰撞边界，逐步检测穿越点并加入从小拱双向步行的100次试走。250次均未穿过闭合主门；100次指定走小拱的往返均成功。[初次报告](initial-closed-leaves-walk.json) · [路径交点](initial-side-passage-trace.json) · [双向复核](gate-and-side-passage-walk.json)

独立模型页在桌面和390像素触屏上切换两档，并点开全部四件下载，实际文件与清单吻合。较暗的网页背景会降低铁栅竖杆对比度。[近景桌面](viewer-desktop-full.png) · [近景手机](viewer-mobile-full.png) · [下载校验](viewer.json) · [图像与目视记录](visual-review.json)

最终渲染站在22157与22158之间从194处增加到195处。全站1,053个实取文件合计986,973,850字节，逐件与冻结签名相符。原裁剪仍为1,005个三角，新增弄门的底图碰撞和近远下载分别核对。[逐件HTTP](renderer-release-http.json) · [城市运行回放](runtime-overlay.json) · [原站输入](map-action-inputs-before.json) · [新站输入](map-action-inputs-after.json)

正式地图从194处增加到195处。在前后的同一街面机位上，原先空出的街墙位置可见小拱、铁栅主门和东侧五孔矮墙。桌面鼠标和390像素手机触屏均通过地图标记选中懿园；两端默认画面中的主拱筒瓦、铁门、西侧通道、竖题名、绿色弄牌和东墙通孔均落在视窗内，避开面板和其他标记。街面初选的54°高倍率镜位被前景楼房遮满，已保留作对照。重新从普通地点卡进入，改用27°、32°街侧机位，均可看见敞开的小拱、关闭的双扇铁门及右墙五孔。32°图可辨竖排“懿園”；绿色弄牌的小字以独立页近景为准。远景只定位楼门所在街段。前后两代各复核19个地面采样，五栋邻房保留。首次键盘测试把前栋名称写作“中南新村”；按地点卡的“中南新邨”重试后，可用键盘切往9号再返回懿园。[原街面](city-28158/before-front.png) · [桌面默认](city-28158/map-desktop.png) · [手机默认](city-28158/map-mobile.png) · [32°近看题名和侧拱](city-28158/street-name-and-side-arch.png) · [原54°遮挡图](city-28158/map-name-tablet-and-side-passage.png) · [回访及下载记录](city-28158/after.json)

28158正式站共实读1,058件、987,022,720字节。该站沿用原24158的门楼定位、碰撞、源地块及模型文件，三档屏宽的本栋相机参数逐值相等。独立页面四件下载均已实际保存并复核。[全站读取](city-28158/28158-all-http.json) · [两代输入与相机](city-28158/city-28158-signed-inheritance.json) · [原始 GLB](../../../assets/models/candidates/xuhui-yiyuan-jianguo-road-gate/xuhui-yiyuan-jianguo-road-gate-raw.glb) · [网页近景](../../../assets/models/candidates/xuhui-yiyuan-jianguo-road-gate/xuhui-yiyuan-jianguo-road-gate-web.glb) · [远景](../../../assets/models/candidates/xuhui-yiyuan-jianguo-road-gate/xuhui-yiyuan-jianguo-road-gate-lod.glb) · [Blender 工程](../../../assets/models/candidates/xuhui-yiyuan-jianguo-road-gate/xuhui-yiyuan-jianguo-road-gate.blend)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/d1d52bf6ca2e0610490ef1b48246bab05ff5522c/projects/shanghai/index.html#landmark=xuhui-yiyuan-jianguo-road-gate&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
