# 美伦大楼西楼南京东路西北转角

南京东路161号西楼既见于第三批3A007美伦大楼，又见于第五批5A030美伦大楼（西楼）。南京东路151号东楼单列5A029。2013年的施工照片、2018年的石作细部和2019年的转角全景用于确认此次制作的三面街墙。[来源登记](../../../source/precise/huangpu-meilun-west-nanjing-corner/reference-review.json) · [来源与范围说明](../../../source/precise/huangpu-meilun-west-nanjing-corner/README.md)

南京东路一侧取紧邻转角的两间店面，沿墙12.8米，江西中路一侧约7米。斜角两端从具名底图量得5.52米。入口玻璃退进，斜面两侧窄窗夹着中间宽窗，上下分别作三角楣与屋顶山花。檐口有分层石线，侧面留有石栏杆。层高、店面退进和石作尺寸来自照片比例。更远的弧面柱廊、南楼、151号东楼、后退加层及玻璃穹顶各保留原有范围。[独立模型](../../../meilun-west-nanjing-corner.html) · [制作源码](../../../source/precise/huangpu-meilun-west-nanjing-corner/source/meilun_facade.py)

## 文件和双端观察

近景14,444个三角面，远景5,236个。重新打开Blender文件后逐件比较了编辑网格及材质。对原始、近景和远景各测67条射线，覆盖石墩、入口玻璃、窗格、退进深度、两处山花及上方净空。桌面和390像素触屏实拍各三个机位，实际保存原始GLB、网页GLB、远景GLB和Blender四个文件，核对每份的长度和SHA-256。[网格与重开记录](geometry-native.json) · [201条射线](surface-checks.json) · [六图和四次下载](viewer.json)

## 地图落位

替换原底图具名西楼1562的三小段街面，保留近景原始俯投影的97.39%与远景的97.48%。检查23个街面探点，覆盖两条马路旁的人行空间、四间入口玻璃之前的浅门槛、石墩和原有封闭店面。对侧电力大楼235及其余15个邻体均保留。两档原屋面高20.75米。图中可见保留的后部高于新建的历史石檐，未取证的后退加层沿用原有底图外形。六条切口立面在近远两版间的最大平面距离约0.07米。[同机位网格对照](original-and-proposed-corner.jpg) · [对照所用源面](corner-mesh-comparison.json) · [近远与地面检查](placement-geometry.json) · [落位参数](final-placement-contract.json)

OpenMapTiles将这一街角归在高5米的多部件对象106284410。与前代目录比较，西楼部分裁掉51.08平方米。检查相邻的九个矢量对象，以及同一对象中其余1,788个原始部件。矢量运算会归并互接的原始轮廓，检查以实际覆盖面积为准。手机、桌面状态分别复算11条视线，机位朝向132°，俯仰38°，覆盖三面店面、上层窗、山花及街侧石栏杆。[矢量差异](initial-vector-comparison.json) · [相机与邻楼](overview-sightlines.json)

第一次Blender重开70个可编辑网格后完成48采样渲染。会话恢复时逐字节比对原有模型与输入，第二次Blender独立重开同一工程并核对面与材质。渲染原图、降噪预览与工程的对应关系、桌面与手机六图的目视记录和实际进程退出时间均可复查。[原生及双端退出凭据](native-and-viewer-exits.json) · [真实前一版的矢量比较](vector-on-predecessor.json)

正式本地整城版本含280处地点。逐项读取1,778个文件、共1,483,686,106字节并校对签名。独立页与地点目录都指向黄浦区南京东路161号西楼，下载项对应同一组已验模型。[完整HTTP校验](production-31245-all-http.json) · [目录卡片、直达与页面实取](final-layer-http.json)

另从31245正式服务逐件读取独立页、浏览模块、清单和四个下载，与桌面和手机实拍会话的输入校对散列。[正式服务与双端会话的文件对应](standalone-31245-bindings.json)

Three.js核心、GLTF加载器、网格解码、旋转控制与其依赖和样式均可由31245相应地址完整读取。八项均与冻结源文件逐字节相同。[独立页实际运行依赖](standalone-31245-runtime.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/fefff8c028f10fb75f1ff0343e350aa4267dac6a/projects/shanghai/index.html#landmark=huangpu-meilun-west-nanjing-corner&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
