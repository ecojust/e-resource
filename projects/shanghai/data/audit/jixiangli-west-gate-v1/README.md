# 吉祥里山东北路西弄门

山东北路22弄的绿牌、窗下自右向左的「吉祥里」石额和向东通入住宅区的弄道，可在三个拍摄年代互相辨认。2013年和2017年的铁门开向弄内，2021年1月12日两扇铁门闭合。模型呈现2021年的铁门和门楼，范围从石门洞的两侧立柱到窗上方的阶梯山墙。门洞估宽3.39米，门楼全宽4.58米，最高10.51米。三处街道机位和窗楣、墙顶高度都是照片估算。[史料与照片来源](../../../source/precise/huangpu-jixiangli-west-gate/README.md) · [机位和屋顶核对](../../../source/precise/huangpu-jixiangli-west-gate/street-registration.json) · [独立预览](../../../jixiangli-west-gate.html)

可编辑的 Blender 文件含32个网格、11种材质。原始模型和网页近景各有19,396个三角面，远景有9,900个。重新打开原生文件后渲染的正面，能看到窗上齿饰、木窗的三块竖向分格、石额及卷成弧线的双扇铁门。三档模型分别用33个射线或部件检查验证门扇后退、栏杆上方净空、窗框、石额和凹凸字形。[原生渲染](huangpu-jixiangli-west-gate-preview.png) · [原生文件与解压后的网格](geometry-native.json) · [三档99个检查](gate-checks.json) · [四种文件与SHA-256](../../../assets/models/candidates/huangpu-jixiangli-west-gate/manifest.json)

门楼投影约4.63平方米，落在两排原有住宅中间。距两个近景组实际网格分别为2.627和0.623米，距远景0.699米。其在街口独立添加，两个住宅地块208和2480保持原状。两个门墩和闭合的铁扇均参与步行碰撞，门扇前的门槛、街面及门后的弄道保持原有地面。[三维网格、地面13处与邻楼间距](placement-geometry.json) · [地图放置合同](final-placement-contract.json)

街对面的原有住宅会遮住低角度镜头。对照桌面和手机各125组机位后，采用朝向93°、俯角30°。将模型正面10,555个命中点回射到正式取景位置，两种屏幕下可见的铁门、门额和窗顶样本均能越过前景。[各组相机与真实街区网格首交点](camera-preflight.json)

把门扇实际的0.07米金属厚度直接用作步行障碍时，150组控制器试走有115组从一次采样跨过了铁门。步行区域改为以扇面为中心宽0.44米的障碍，覆盖生产控制器一次冲刺的最大步长0.425米。街道和门槛仍可抵达，渲染网格保持照片所示的细铁栏。正式控制器以20至60帧、走路和冲刺、三个横向位置及五种不同起点复试，150组均在已关闭的门扇前停下。[实际薄度的初测](preflight/physical-width-walk.json) · [修正后的试走](closed-leaves-walk.json) · [可重跑的控制器验证](check-closed-leaves.mjs)

作者工作树的真实独立页在1250×820和390×844两种屏幕分别读入了近远景。两端均能辨认阶梯山墙轮廓、上窗、横向石额及关闭的铁扇。四种下载与清单SHA-256逐项相符。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机远景](viewer-mobile-lod.png) · [实际浏览与下载](viewer.json)

原生相机对象和相机数据均使用西弄门名称。早期文件留有另一栋建筑的相机标签，已从更正后的作者脚本重新封装、打开原生场景，并从独立页再次下载四件文件。三档GLB重建后字节逐一相同。[原生相机实读](native-camera.json) · [更名前四件摘要](preflight/first-native-digests.json)

正式185处站点从22148读取了973个冻结输入和5个原生城市源，978次HTTP共963,087,923字节全部匹配。与22147的184处场景逐项比较，两侧近景组和两套矢量源均保持原状，13处地面点通过。全城前后各986片、20个宏区，最大的宏区322片，由正式版分表绘制。早期184/185冻结树仍使用320片的单表上限，实际失败日志随旧版下载收据保存。[正式站点978个下载](accepted-http.json) · [实际运行模块与两侧地块](runtime-overlay.json) · [早期原始站点下载](frozen-http.json) · [单表超限记录](preflight/raw184-185-single-table.log)

在184处的街区原貌上，门楼所在的位置可以看见后方弄道。加入模型后，桌面鼠标和手机触摸分别点中了编号185的西弄门。近看时，门楼夹在两排住宅之间，两扇铁门、上窗和石额有清晰的层次。街口正面位于阴影中，手机独立页远景仍可分辨山墙、窗和门洞。两排住宅的源网格与碰撞均通过复核，门后弄道与门前街面仍可步行。前后各检验13个地面位置，并从目录进入独立页实际保存了原始、近景、远景和 Blender 四份文件。[加入前的街区](final-map-24148/before/before-front.png) · [主图门扇近照](final-map-24148/after/map-stone-plaque-and-closed-leaves.png) · [手机街景](final-map-24148/after/map-mobile.png) · [实际操作与下载](final-map-24148/after/after.json)

首次从建筑目录切换页面时，核验脚本读取了仍在载入的场景。保留首次两端点选的原始收据后，脚本改为等待场景就绪，随后复跑了后态的五幅主图、目录跳转及四件下载。前态由首次脚本完成，收据载有其摘要。[首次导航记录](preflight/first-catalog-navigation/after/after.json) · [前态记录](final-map-24148/before/before.json) · [后态核验脚本](final-map-24148/check-independent-city.cjs) · [独立页照片与正式站点的文件核对](final-map-24148/independent-viewer-24148.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/a126918a917cc04972d0bd833c7ba255650dda0e/projects/shanghai/index.html#landmark=huangpu-jixiangli-west-gate&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
