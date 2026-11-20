# 岳阳路320号在君楼

徐汇区旅游咨询中心保存的斜俯照片将双内院、东面三组高窗、每侧八开间的长翼与七券入口纳入同一画面。2014年岳阳路街照能单独核对六根方柱、端部支承、盲券内的竖砖和窗间肋的尖形装饰。三档GLB均为原创几何，可编辑Blender文件含76个网格。完整与简化档分别有73,664和45,416个三角面。三份原始或解码后的模型各用139条射线检查门洞、柱帽、顶面、窗扇、砖饰、檐口和露天内院。[制作依据](../../../source/precise/xuhui-yueyang-320-research-building/README.md) · [四件模型](../../../assets/models/candidates/xuhui-yueyang-320-research-building/manifest.json) · [单体浏览](../../../yueyang-research-building.html) · [正面](xuhui-yueyang-320-research-building-preview.png) · [原生双院斜俯](native-courtyard-oblique.png) · [原生核验](geometry-native.json) · [射线记录](surface-checks.json) · [两份照片的目视核对](visual-review.json)

主楼714及前廊715同属一个城市瓦块，实际解码近景分别为68,360和6,384面，远景分别为68和12面。现存粗模型原先均按24.30米挤出。七券前廊按照片改为约6.2米，两个内院维持透空，另八处邻楼保留。最近独立近景距裁片6.53米。24个地面样点包括七个可通过券口、八个柱脚位置、两院、入口台阶、街面及主楼实体。[两档原始建筑](source-geometry.json) · [配准与地面](placement-geometry.json) · [登记合同](final-placement-contract.json) · [默认镜头视线](overview-sightlines.json)

将2024年航片按东立面轴线旋正，沿低廊前缘取得七条可分辨的局部暗带，六个连续间隔平均2.42米，模型七券的均分节距为2.53米。树影覆盖了最南侧边缘，所以券数取自可逐一识别的两张地面及斜俯照片。研究保留先前把715视作独立窄条的初步判断，以及三期影像复核后的具体修正。[阴影采样](portico-shadow-comparison.json) · [图层收据与判断修订](../../../source/precise/xuhui-yueyang-320-research-building/footprint-review.json)

第167处城市目录继承医学院东楼所在的166处版本。实际调用城市裁切程序时，近景组中40个裁片只绑定主楼714与七券门廊715。同组448及761保留，另一个相邻分组的裁片数为零。运行时共检查29个地面样点。冻结站的801份文件均已通过HTTP逐字节核对，总计760,485,270字节。[实际城市运行时](runtime-placement.json) · [源站核对](frozen-http-summary.json) · [登记增量](inventory-increment.json)

最终城市页面从166处升到167处。手机实点建筑目录进入，在桌面输入“在君楼”后，用三次Tab和Enter选中同一地点。桌面默认画面可见双院、两翼和七券低廊。手机初次画面中，两翼部分下层仍呈灰色粗面；街面近景清楚显示门廊和窗带，地点灯牌遮住中央高窗下部。屋顶画面能分辨两个独立的露天院落。在远景中可识别两院的开口。与同机位旧图相比，原来与主楼等高的门廊降到实照所见的低层。[两端实测](final-map-23129/measured-summary.json) · [原有街景](final-map-23129/map-before.png) · [手机入口](final-map-23129/map-mobile.png) · [桌面入口](final-map-23129/map-desktop.png) · [七券街面](final-map-23129/map-street-facade.png) · [双内院](final-map-23129/map-roof.png) · [远景](final-map-23129/map-distant.png)

实测时底图有8,714个建筑要素，七处券口、八个柱脚、两院及街面、主楼、五处邻屋等29点全部符合预期。40个裁片只绑定714和715；近远模型、原始GLB、原生工程及两份原城市瓦块的字节数和SHA-256均匹配。最终网页的809项输入实取760,559,737字节。早先基础服务中断时页面留在加载提示；恢复后重新核对两端10项依赖，并重新进入原路由取得全部画面。记录同时保留了磁盘用尽导致一次浏览器未能启动的情况。[浏览器原始记录](final-map-23129/main-browser.json) · [前态记录](final-map-23129/control-browser.json) · [最终资源](final-map-23129/all-http.json) · [运行时](final-map-23129/runtime-placement.json) · [首次加载画面](final-map-23129/initial-unavailable/initial-unavailable.png) · [恢复核验](final-map-23129/dependency-health-after-recovery.json)

正式24129手机复查中，从地点目录实点进入后，首个可观察的精细画面和1,718.6毫秒后的稳定画面保持同一位置、角度和缩放。两个矢量源均已隐藏，现场状态连续稳定3,994.9毫秒，沿街两翼可以辨认窗带和七券入口。对旧手机图的三个灰色取样框复算，原有1,459、1,525和676个指定颜色像素，复测各帧均为零。原默认桌面及手机的两行灯牌均离开中央窗组；只有主动街面近景的牌面与所取的三处下部窗格相交。旧图保留了首次加载的状态。[新手机原界面](final-map-24129/stable-public-mobile.png) · [首个精细渲染帧](final-map-24129/first-verified-frame.png) · [稳定帧](final-map-24129/stable-frame.png) · [实际时间线](final-map-24129/timeline.json) · [前一版本的灯牌和灰面取样](final-map-23129/source-and-label-pixels.json)

实际底图14/13719/6696瓦片中，714和715均缺少高度和层数，矢量层按12米绘制。冻结运行时对两座具名物体的真实轮廓求交，两者均可全部隐藏，周围八处保持。手机默认17.3615已满足17.3近景门限，视点到这一组的边界距离为零。较早手机画面里两源尚无隐藏状态；同会话桌面及此次正式手机的相应源均已隐藏。首次旧画面没有逐帧事件记录。最终版本全部811项输入实际读取760,586,706字节，实地对照了两个版本的46项网页和资产请求。在君楼的登记、放置、四件资产和默认相机保留一致。[取样与距离](final-map-24129/review.json) · [实到矢量及HTTP范围](final-map-24129/overture-source-samples.json) · [23/24两版对照](final-map-24129/pair-http.json) · [最终全部输入](final-map-24129/all-http.json)

单体页面在1250×820桌面与390×844手机上分别切换近景和远景，并通过正面观察按钮检查画面。四幅图都完整显示长翼、抬高的中央体和七券入口。在网页上依次保存原始GLB、网页近景GLB、远景GLB和Blender工程，四份实际下载文件的名称、字节数及SHA-256均与发布清单吻合。检查期间没有页面脚本错误。[四次下载记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/ebe8e0f4810756348b5a0f2d4a393c3c3fb12942/projects/shanghai/index.html#landmark=xuhui-yueyang-320-research-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
