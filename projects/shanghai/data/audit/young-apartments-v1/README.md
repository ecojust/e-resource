# 永业大楼 · 淮海中路、雁荡路圆角

市房管局在黄浦区 2C003 条登记永业大楼，银行博物馆记载原名杨氏公寓，1932 年委托设计。本次按建成旧影、2006 年实照、2014 年上传的署名照片和街景，制作交叉口的石砌银行门面、弧形铁栏、两侧红砖窗组、日光室和重檐瓦顶。两条长翼的远端、院落、室内及现代店招仍留作后续。[出处、年代及局部范围](../../../source/precise/huangpu-young-apartments/README.md) · [独立模型](../../../young-apartments.html) · [网页文字与资料核对](viewer-caption-source-check.json)

近景 41,484 个三角面，远景 18,756 个。Blender 工程重开后有 180 个可编辑网格。四个文件共 4,888,101 字节。原始、网页及远景模型各测 63 项，涵盖五个外圆角分区的钢框与玻璃、三层栏杆、屋顶坡面、小鼓座顶、侧翼露台和临街地面。实照中中央石框横跨一整开间，据此修正了预览模型中央多出的一道竖框。[三档网格](surface-checks.json) · [原生重开](geometry-native.json) · [原生预览](huangpu-young-apartments-preview.png) · [清单](../../../assets/models/candidates/huangpu-young-apartments/manifest.json)

地图仅裁去底图 2824 的东北圆角。近景保留 88.67%，远景保留 88.67%。后侧沿原楼 19.2 米屋面高度封口，并保留街区内原有的两条长翼。六个相邻地块与新模型裁区分离，原城几何视线检测显示，桌面和手机的默认机位均对准七处街角构件。下表记录了真实页面控件造成的遮挡。弧形半径及屋顶高度取自图像比例，精度限于街景取像条件。[原有地块及周边](placement-geometry.json) · [放置与碰撞](final-placement-contract.json) · [两种屏幕的视角](overview-sightlines.json)

25214 本地冻结版有 251 处入口。已逐件读取 1,516 个文件，共 1,291,581,040 字节，哈希均与该版签名相符。目录卡、独立页及城市登记使用同一楼栋标识，独立页中的 1932 年指委托设计。运行时检测覆盖 19 个地面位置和 14 个向量来源状态。[建筑与文字复核](city-25214-caption-sources.json) · [251 处的运行时检查](runtime-placement.json) · [完整传输记录](city-25214-all-http.json)

独立查看器在 1250 × 820 桌面和 390 × 844 手机上实测。鼠标和触摸分别打开正面、斜视及俯视，六张画面中均可辨认外圆角与重檐轮廓，手机上单根铁栏较细。桌面实际保存的四件文件与清单一致。[浏览器与下载](viewer.json) · [六图目视复核](standalone-visual-review.json) · [手机正面](viewer-mobile-full-front.png) · [桌面斜视](viewer-desktop-full-oblique.png)

26214 版继承上一栋四行大楼的说明修订。实取旧版和修订版后，四行大楼页已写明虹口四川北路、1932 年及北端阳台。其余 1,515 个签名文件保持同一哈希，永业大楼的城市登记、目录卡和独立页再次实取通过。[新旧说明字节](city-26214-parent-viewer.json) · [永业大楼三项文字核对](city-26214-caption-sources.json)

在26214正式站重新通过HTTP读取全部1,516份输入，共1,291,581,143字节。与25214逐项比对，四行大楼独立页是唯一发生字节变化的文件。[26214逐件回执](city-26214-all-http.json)

## 普通地图入口与两端实拍

从前一版的250处地点切换至251处。手机从地点目录触屏选中并点击地图标牌，桌面从目录用鼠标选中，随后以键盘切换和返回。每次切换都核对模型、裁切范围和页面给出的地点名。[前一版同机位](city-31214/map-before.png) · [返回本楼](city-31214/map-returned.png)

下表按实际画面中各构件采样点的位置，统计位于画幅内且避开标牌和页面控件的点。单个点只代表该构件选定位置。

| 实拍 | 画幅 | 露出的采样点 |
| --- | --- | --- |
| [手机稳定画面](city-31214/map-mobile-same-camera.png) | 390×844 | 7/7 |
| [桌面稳定画面](city-31214/map-desktop-same-camera.png) | 900×650 | 6/7 |
| [手机公开加号](city-31214/map-mobile-public-zoom.png) | 390×844 | 6/7 |
| [细看立面](city-31214/map-street-facade.png) | 700×550 | 6/7 |
| [屋面](city-31214/map-roof.png) | 700×550 | 3/7 |

浏览器分别签收近景与远景模型，核对原有近、远底图，并实取四份文件。31214正式本地站整读1,516个文件，地面通行及周围楼房合计19个采样。对照、手机、桌面、键盘切走并返回、街面与屋面、远景六个独立会话均已结束，退出码均为0。[远档](city-31214/map-distant.png) · [各视图与遮挡位置](city-31214/default-screen-coverage.json) · [完整签收](city-31214/result.json)

[单体与下载页](../../../young-apartments.html) · [原始GLB](../../../assets/models/candidates/huangpu-young-apartments/huangpu-young-apartments-raw.glb) · [网页近景GLB](../../../assets/models/candidates/huangpu-young-apartments/huangpu-young-apartments-web.glb) · [远景GLB](../../../assets/models/candidates/huangpu-young-apartments/huangpu-young-apartments-lod.glb) · [Blender工程](../../../assets/models/candidates/huangpu-young-apartments/huangpu-young-apartments.blend)

正式31214单体页面在桌面与手机分别实拍正立面、斜侧和远档俯视，六张图均保留原始像素与散列。四个下载按钮实际保存原始、近景、远景及可编辑工程，下载字节与模型清单逐件吻合。[六张实拍与四件下载](city-31214/standalone/viewer.json) · [两代城区与相机](city-31214-signed-inheritance.json) · [六个地图会话的退出凭据](city-31214/214-map-slot-released.json)


### 地图实拍中的可见范围

手机地点目录和900×650桌面都能看清两条街交会处的弧形窗带、浅色楼层横带和顶层圆亭。街面近景的七处采样有六处露出，屋面取景能分辨下层圆形红屋面和上层小圆顶。窄桌面410×370的回返截图能读到已重新选中永业大楼，但七处采样均被页面遮盖。488×362的远景也有相同限制。两帧分别记录地点恢复和远档载入，建筑细部可对照手机实拍及独立页。[手机放大](city-31214/map-mobile-public-zoom.png) · [街面](city-31214/map-street-facade.png) · [屋面](city-31214/map-roof.png) · [逐点遮挡](city-31214/default-screen-coverage.json)

前态有五次未通过，回返有两次未通过。首次回返在切走及切回后渲染进程中止，第二次回返在验收程序限制并发请求时出现近景文件载入超时。第三次回返使用正常网络并发，初始地图记录过一次目录超时，随后在真实公开地点地址重新载入，选中状态、裁切范围和近景原件均通过复核。七次未通过的运行保留了各自的输出和退出状态，可与成功报告逐项对照。[七次运行的原始记录](city-31214/failed-attempts/index.json) · [回返实测](city-31214/segment-return.json) · [远档实测](city-31214/segment-distant.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/9309e6e5023e353664f87bd384090240ca5df359/projects/shanghai/index.html#landmark=huangpu-young-apartments&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
