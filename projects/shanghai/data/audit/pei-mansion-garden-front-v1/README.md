# 贝宅花园侧主楼制作核验

| 资产 | 字节 | 三角面 | SHA-256 |
| --- | ---: | ---: | --- |
| 原始GLB | 1125312 | 21272 | `b81c2061d82b16c769f26ecf3ce8d8675781881bed2426026a6192773c1cef6e` |
| 近景GLB | 376532 | 21272 | `9e8e0b1429b94caed06d9ce8df7e789eed3990671b3e571d5ff9eadaf171727f` |
| 远景GLB | 242120 | 13908 | `c12d7aeec584d19f88a1c01e2291d181b2c2d087401f063278d8b8a3c613f371` |
| 可编辑Blender | 260509 | 21272 | `9210bd57f9f63e823d4d001f3d65d8d163cd63597f6c10fc1984275c5cd016cf` |

Blender实地重开并逐面核对165个可编辑网格。原始、实际解压近景与远景各检验159个首面，覆盖18组折面窗、各层窗梃、侧向玻璃、两层栏板的石料与透空、凹廊后窗、石阶、屋顶及竖井。检查按照片上的构件位置发射射线，另对屋面、竖井及最高齿顶的高度作数值复核。[原生与解包核验](geometry-native.json) · [477条首面及高度记录](surface-probes.json) · [原生渲染](jingan-pei-mansion-garden-front-preview.png)

主楼占地来源为东亚建筑数据3135号，邻地身份、实际近远网格及裁切范围均已核对。裁切482.06平方米，主楼碰撞441.66平方米，13处地面核点包括两个折窗、玻璃门内侧、花园、石阶以及独立周边楼栋。相机离线测试在桌面与手机检查园侧九个可见构件，设定朝向338°、俯仰36°；真实网页和地图表现以各自浏览器记录为准。[足迹与实际网格](footprint-review.json) · [配准合同](final-placement-contract.json) · [离线视线](../../../source/precise/jingan-pei-mansion-garden-front/camera-preflight.json)

主要正面依据2013年园内原照。侧背外观、檐高和竖井深度属概括，院门、花园亭、帐篷与室内另列。[身份、尺寸及出处](../../../source/precise/jingan-pei-mansion-garden-front/README.md) · [独立网页](../../../pei-mansion-garden-front.html)

正式23177与23178源站分别返回214、215处地标的目录。此前174处候选行逐字节对应。实取1221份文件，共1,072,799,948字节。运行时只对3135号主楼实施局部归属裁切；地面验证覆盖实际封闭的折面窗、入口门线、花园石阶与同组邻楼。[两代目录](renderer-parent-controls.json) · [全量实取](renderer-release-http.json) · [运行时通行与邻楼](renderer-runtime-placement.json)

在正式23178站分别以1250×820桌面和390×844手机实点近、远两档。四张图的三层折面窗、两条透空栏板、金属门框、女儿墙和右侧竖井均可辨认，原始、近景、远景和Blender四个下载与清单逐字节一致。[浏览器与下载收据](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)

在独立页选择「折面窗与凹廊」，桌面与手机都能看到左右两组突出墙面的钢框窗、两层后退的栏廊，以及入口的室外台阶。栏板镂空的回纹可与2013年照片上的细部逐段对照。侧面和背面缺少同等清晰的照片，保留概括体量。[花园侧正面照片](garden-front-2013.jpg) · [栏板照片局部](gallery-rail-detail.jpg) · [桌面斜面查看](faceted-windows/oblique-desktop.png) · [手机斜面查看](faceted-windows/oblique-mobile.png) · [实际交互记录](faceted-windows/oblique.json)

将已登记入口在870像素桌面、390像素手机和1280像素宽屏分别投影到实际近远楼体网格，9个标志点均在可视范围，原底图的近远楼体没有遮住安全区域内的目标像素。此项是几何预检，页面浮卡和灯牌另以实图核验。[镜位与逐点结果](ordinary-camera-preflight/pixel-visibility.json) · [桌面深度比较图](ordinary-camera-preflight/desktop.png) · [手机深度比较图](ordinary-camera-preflight/phone.png)

## 贝宅花园侧主楼在上海地图中的实拍

从城市目录进入时，桌面和390像素宽的手机都选中了贝宅。旧目录有214处，增加贝宅后有215处。地图鼠标与触屏测试均从吴同文住宅出发，以真实指针点中贝宅灯牌，再核对所选地点。13处主楼、台阶和花园地面，加上5座保留邻屋，实测通行与碰撞均与登记相符。[旧目录主图](city-31178/before/map-before.png) · [桌面目录与主图](city-31178/desktop/map-desktop-settled.png) · [手机地图](city-31178/phone/map-mobile-settled.png) · [指针和地面记录](city-31178/visual-review.json)

花园侧的两组凸窗向侧面折转，钢窗横竖梃沿三层延续。中央凹廊的两道透花栏板、下面的门和台阶能从建筑近景辨认。左下方的说明卡遮住一段窗脚，地图标牌也遮到局部栏板，独立页斜视能看到整排窗与栏板。屋顶镜位可见浅色竖井及其投影。[开间与钢窗](city-31178/architecture/map-faceted-steel-windows.png) · [两道内凹廊](city-31178/architecture/map-recessed-galleries.png) · [屋面](city-31178/architecture/map-roof.png) · [独立页斜视](faceted-windows/oblique-desktop.png) · [全城远景](city-31178/distant/map-distant.png)

第一次建筑近景会话遇到本地静态服务连接中断。恢复受影响的原路径后，原先失败的25条资源均返回正确字节。第一次鼠标会话的渲染器在操作中退出。在600像素宽的鼠标复测中，灯牌已选中贝宅，自动镜头停在17.18级，尚未进入近景底模的加载层级。鼠标复测分别记录了选中及街墙近景。第一次触屏会话在选中并加载贝宅后切换镜头时中断，随后独立触屏会话复核实际指针、地点、可见近景和其下载字节；手机建筑画面由正常目录会话另行保存。第一次连续从近镜切远镜时渲染器退出，单独远景会话已载入并验证LOD，但首次截图时退出。释放本地复核服务占用的内存后，后续会话单独从同一地图拍摄远景。触屏会话实载近景，远景会话实载LOD，四份独立页下载的字节数与SHA-256均符合清单。[中断与复测](city-31178/initial-attempts/comparison.json) · [下载核验](viewer.json)
