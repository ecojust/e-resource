# 武康路99号正广和大班住宅

市房管局第二批名录2D036、地方志及2013年原片的「99／武康路」门牌共同确定了这栋1928年的住宅。西面木栏阳台可从公共街道核对，南面露木山墙、四根砖柱敞廊、上层透花砖栏和两处老虎窗则依据图书馆保存的花园实照。院门及其他分栋保留为今后单独测绘的对象。[史料、实照和示意图的区别](../../../source/precise/xuhui-caldbeck-manager-residence/README.md) · [门牌照片](number-99-crop-2013.jpg) · [摄影署名](photo-credits.md)

## 网格、屋顶和敞廊

使用 Blender 4.3.2 独立重开110个可编辑网格，原始模型共有30,613个有向三角面及16种材质。网页近远档均解码后与对应生成网格逐面比较。每一档用133条射线核对窗玻璃和窗框、半露木架、西阳台、敞廊和能透视的砖栏孔洞、两处老虎窗与两组砖烟囱。屋脊与谷线先逐条切开，另在22处坡面上将实际命中高度与设计屋坡比较，误差上限9.5厘米。院内空地的测试射线穿过全高。这里的屋高与构件尺寸依照片估计。[Blender重开与解码凭据](geometry-native.json) · [399条独立检测](surface-probes.json) · [原生构图](xuhui-caldbeck-manager-residence-preview.png) · [渲染边距](native-framing.json)

| 可下载文件 | 字节 | 三角面 | SHA-256 |
| --- | ---: | ---: | --- |
| 原始GLB | 2,211,052 | 30,613 | `a3e740232b324e22f24120dc5fd591ea4e6dd54d1ec46da93c6e54374e17b177` |
| 网页近景 | 1,014,468 | 30,613 | `87e369945803936aadca5c074ac8fa408f25b1c9d53e9c7581077a4bf52be735` |
| 网页远景 | 491,224 | 15,381 | `4af129d7b232843ff35af57584391b4e9166c5b0475a9d9845b7af2ad3125117` |
| 可编辑Blender | 482,791 | 30,613 | `9d282f088681614e87457ec2fefd8188e08724e7cc4f340ba849345a5d32c168` |

## 主屋、通行与邻楼

宏块14-13718-6695的2729号为主屋，登记足印264.67平方米。核对原底图的近景10,640个三角面与远景20个三角面，同组其余八座保持原样。最近的原生几何体与替换范围相距2.36米。建筑地面碰撞总面积242.07平方米，扣除廊下约23.44平方米的开放部分，再分别标出四根园廊柱和两根街面阳台柱。19个检查点覆盖主体、柱脚、廊道、院子及相邻房屋。按来源位置独立考察了手机与桌面从真实建筑物之间观察园侧和屋顶的视线。[房屋、碰撞与邻楼](footprint-review.json) · [正式放置契约](final-placement-contract.json) · [取景射线](../../../source/precise/xuhui-caldbeck-manager-residence/camera-preflight.json) · [独立交互预览与下载](../../../caldbeck-manager-residence.html) · [四件与页面实取](standalone-http.json)

正式23170与23171源站分别返回207、208处地标的目录。此前167处候选行逐字节对应。实取1165份文件，共1,049,042,723字节。运行时只对2729号增加3片裁切，18项矢量检查及27个地面点分别确认主屋、敞廊、6个独立柱脚与周围8栋建筑的范围。[两代目录](renderer-parent-controls.json) · [全量实取](renderer-release-http.json) · [运行时通行与邻楼](renderer-runtime-placement.json)

在独立模型页选择「武康路阳台」，桌面鼠标和手机触屏都能从南园转到临街山墙，看到上层木栏阳台、下方两根柱和转角另一面的园侧敞廊。临街照片摄于围墙外，屋后的构造仍按来源记录中的估计范围表示。[2013年临街原貌](west-front-and-gate-2013.jpg) · [桌面临街斜面](street-balcony/oblique-desktop.png) · [手机临街斜面](street-balcony/oblique-mobile.png) · [两端实测](street-balcony/oblique.json)

将已登记入口在870像素桌面、390像素手机和1280像素宽屏分别投影到实际近远楼体网格，10个标志点均在可视范围，原底图的近远楼体没有遮住安全区域内的目标像素。此项是几何预检，页面浮卡和灯牌另以实图核验。[镜位与逐点结果](ordinary-camera-preflight/pixel-visibility.json) · [桌面深度比较图](ordinary-camera-preflight/desktop.png) · [手机深度比较图](ordinary-camera-preflight/phone.png)

## 武康路99号在城市地图中的实拍

普通地点目录从207处增至208处。桌面点击和390像素手机触屏都能进入武康路99号；在地图上的标牌另分别用鼠标与触屏选中。27处地面采样覆盖主屋、花园敞廊、柱脚和八座邻屋。[更新前的地图](city-31171/before/map-before.png) · [桌面目录进入](city-31171/desktop/map-desktop-settled.png) · [手机目录进入](city-31171/phone/map-mobile-settled.png) · [城市远景](city-31171/distant/map-distant.png)

桌面和手机地图上都能辨认红瓦屋顶与两个老虎窗。花园近景能看到砖柱敞廊和上层透花栏板；左下说明卡遮住部分山墙和柱脚，标牌也挡住局部窗面。独立页的街侧斜视可从围墙外侧查看西阳台及双柱。[花园敞廊](city-31171/architecture/map-garden-loggia.png) · [山墙和老虎窗](city-31171/architecture/map-timber-gable-and-dormers.png) · [屋面](city-31171/architecture/map-roof.png) · [独立页街侧阳台](street-balcony/oblique-desktop.png)

首次连续切换画幅时，只取得手机两图，桌面重载中断。随后六个独立浏览器会话使用同一版地图，依次完成手机、桌面、建筑近景、鼠标选中、触屏选中与远景核验。远近网格在真实场景中加载；四份下载的长度和SHA-256与清单相符。[原始中断记录](city-31171/initial-interruption/main-browser.json) · [实测汇总与进程退出记录](city-31171/visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 43 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/a32c9658c58447160696953fd6bb2745540f6ff7/projects/shanghai/index.html#landmark=xuhui-caldbeck-manager-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 43 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
