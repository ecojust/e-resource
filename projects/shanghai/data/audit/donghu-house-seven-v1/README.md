# 东湖宾馆七号楼花园立面

淮海中路1110号住宅的双层敞廊已改为封闭立面。原片可辨两端拱窗上的花饰与正中玻璃门，屋顶斜照补足三组窗的位置、前坡和两侧短坡。[保护牌与三个方向照片](../../../source/precise/xuhui-donghu-hotel-house-seven/reference-review.json)

原始和网页近景各45,884面，远景16,966面。Blender重开71个独立网格。三份交付网格各经83条实际射线，涵盖石刻、锁石、钢框、栏杆、柱头、底层柱、门把、阶梯、玻璃棚和屋顶。首版外柱被翼墙遮住，修正后在近、远景均辨认得到。[首版与修订](draft-review/joint-review.json) · [各档射线](surface-checks.json) · [可编辑工程核对](geometry-native.json)

原楼近景组含95,348个三角面，逐一核对各面中心与三个顶点，对七号楼的归属判断完全一致。远景有逐面来源标识。花园侧割面保留主楼北段，原楼近、远景分别保留65.1%、65.1%占地，两档接缝相差0.070米。最近其他建筑距裁切范围6.79米。[近远来源与地面](placement-geometry.json) · [选择视角检查](../../../source/precise/xuhui-donghu-hotel-house-seven/camera-preflight.json)

216处与217处的预览站点实取目录逐行核对，东湖七号楼接入时沿用此前所有建筑的位置和裁切。七号楼所在图组新增2片，只裁原楼552。两套矢量源共核16项，地面、台阶和相邻建筑核25处。[前后目录与裁切](renderer-parent-controls.json) · [运行结果](renderer-runtime-placement.json)

独立页已在桌面和390像素手机切换近、远景，四种文件均可下载。正式预览站逐项下载了1,237个输入，共1,087,338,948字节。另在该站单独核对独立页、脚本与模型文件，逐字节匹配运行浏览器时使用的版本。[桌面](viewer-desktop-full.png) · [手机](viewer-mobile-full.png) · [四件下载](viewer.json) · [HTTP校验](renderer-release-http.json)

## 在城市地图中查看花园立面

从216处的前一版进入现场，只见原有的灰色平屋顶和成排方窗。新版本中，在870×660桌面用鼠标点击目录、390×844手机直接触摸目录，均能看见花园立面、台阶和保留在后方的楼体。在街区地图上，从朱敏堂住宅实际点选七号楼的灯牌，也会返回同一处。窄屏默认画面能看全前坡和三组屋顶窗，桌面默认灯牌覆盖了部分屋顶窗。[原街面](city-31180/map-before.png) · [桌面](city-31180/map-desktop.png) · [手机](city-31180/map-mobile.png) · [灯牌点击](city-31180/map-beacon-return.png)

面向花园的近景中，两端拱窗上方的垂花雕饰、中央三段大窗、石柱头与深色短栏均可见。低处的玻璃棚向前突出，位置卡遮住了棚下入口的一部分。完整台阶可从手机默认画面查看。斜向屋顶画面则能同时看到前坡、两端短坡、三组屋顶窗和后方原楼。[花园近景](city-31180/map-street-facade.png) · [斜向屋顶](city-31180/map-roof.png)

正式地图中，552号原楼承担两片裁切，保留的建筑和近邻仍参与碰撞。25个地面点覆盖新旧墙面、棚内、阶前、两翼、花池和邻楼。门前与玻璃棚内的地面可通行，里面的门扇会挡住行人。近景实载45,884面，远景实载16,966面，440×380的街区画面中位置卡覆盖了中央区域。四个下载文件均已核对。独立页原有的四张实图与浏览器保存记录也已按正式站返回的文件逐一比对。[分段实测与25处地面](city-31180/main-browser.json) · [远景](city-31180/map-distant.png) · [独立页与四种文件的对应关系](city-31180/release-evidence.json) · [1,239项正式文件的下载校验](city-31180/all-http.json)

GitHub 固定提交的地图入口、运行模块、来源和四种下载等 39 个公开文件均实际返回 HTTP 200，字节数及 SHA-256 均与 Git 对应文件相同。 本次固定提交在第三方地图预览服务的入口响应为 429。主图交互依据本页所列的同版本浏览器实测。[GitHub 版本目录](https://github.com/ecojust/e-resource/tree/f723404054b12fd8aa2d7bf1c2e67c6154ea315e/projects/shanghai) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，4 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)

随后复查，第三方预览的地图入口已正常返回 HTML。固定版本的 39 个文件及地图实际引用的模块链均与 Git 对应字节一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/f723404054b12fd8aa2d7bf1c2e67c6154ea315e/projects/shanghai/index.html#landmark=xuhui-donghu-hotel-house-seven&mode=overview) · [预览复查](public-preview-recheck.json)
