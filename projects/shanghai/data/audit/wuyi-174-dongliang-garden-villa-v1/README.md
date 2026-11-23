# 武夷路174号花园住宅模型复核

武夷路一侧可以看到木格山墙、两扇楼上窗、券门上方的弧形阳台和较低屋翼的老虎窗。花园侧有两种屋顶窗、三扇双开门和一组外凸的弧形玻璃。侧墙受树木和相邻房屋遮挡，可见范围以外保留基础墙体。屋脊、檐口、阳台的高度与进深均为照片与航片估算值。[模型浏览与下载](../../../wuyi-174-dongliang-garden-villa.html) · [调查、照片出处与重建程序](../../../source/precise/changning-wuyi-174-dongliang-garden-villa/README.md)

| 模型渲染 | 可检查的部位 |
| --- | --- |
| [武夷路正面](registered-views/street-gable.jpg) | 两扇上层窗、凸窗、券门上方的栏杆、两处白色店篷 |
| [花园立面](registered-views/garden-elevation.jpg) | 两处老虎窗的屋顶、三道浅色门篷、弧形阳台 |
| [花园阳台近景](registered-views/garden-balcony.jpg) | 卷花铁栏、灰石厚边、木门及落地窗的转角 |
| [整栋俯视](registered-views/overall.jpg) | 主脊、相交的坡屋面、烟囱及街侧挑檐 |

近景及未压缩模型各有104,708个三角面，远景有74,242个。逐件核对有向边和有符号体积，近景的2,498个实体、远景的2,075个实体均闭合。两档网页文件解压后对应源网的三角面朝向、材质和贴图坐标；瓦面、灰石和粉刷层的三张原创贴图均随文件内嵌。[闭合检查](editable-parts-closure.json) · [两档解码记录](web-model-verification.json)

在另一个 Blender 进程重新打开可编辑文件，读回406组命名网格、7台相机、3张内嵌贴图和104,708个三角面。比对11,160个使用贴图的面角，UV最大绝对差小于百万分之一。[Blender 复开记录](native-reopened.json)

临街照片的17处材质标记在未压缩模型及两档解码模型上均命中。花园近照的20处全部命中。花园远照的8处中，4处命中，另有3道细铁栏和1处窗梃与相应照片点相距0.42至13.28像素。门窗洞背后的8条短射线另行检查，开口与门框位置吻合。花园远照最东侧瓦沿边界点在模型中碰到灰墙，原读数保存在表内。[街面逐点记录](street-three-models.json) · [花园两张原照与四份网格复核](south-garden-bay/README.md) · [四机位参数及渲染信息](registered-views/render-stations.json)

桌面与手机尺寸均从模型页打开七个机位、切换近远景，然后用各自的四个下载按钮实际保存文件。两端所得四份文件的大小和 SHA-256 与发布清单一致。[页面与下载记录](ui/viewer-checks.json) · [桌面图](ui/desktop/oblique.jpg) · [手机图](ui/phone/oblique.jpg) · [模型清单](../../../assets/models/candidates/changning-wuyi-174-dongliang-garden-villa/manifest.json)
