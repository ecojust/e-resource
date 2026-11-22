# 忆定村住宅屋顶方间与双道红砖檐带

2014年5月9日，Antigng从江苏路拍摄了忆定村。树冠后方露出一间抹浅色灰的屋顶方间，正面和侧面都能看见红色檐带。一片更低的瓦屋面从侧墙接出。上海市第四批优秀历史建筑名录将忆定村登记为江苏路495弄，编号4M008。[打开模型](../../../yiding-village-roof-pavilion.html) · [原照裁切](measurements/antigng-roof-room.jpg) · [名录与建筑资料](measurements/building-and-rooftop.json)

正面钢窗分四列。第一、三列的横档靠近顶部和底部，第二、四列的两道短横档集中在中间。屋顶上另能辨认两根立杆，侧墙上可辨外开窄窗、明管和带圆形风扇的空调箱。外挂构件呈现拍摄时的状态。[原照与模型](study-views/roof-room-in-2014.jpg) · [钢窗逐列对照](study-views/staggered-steel-grid.jpg) · [侧窗与瓦面](study-views/return-and-tile-eave.jpg)

## 从照片读取的细部

将照片按相机的EXIF方向旋转90度顺时针，再截取保有正面、侧返和下方瓦面的区域。根据窗洞四角、屋檐转角和侧窗恢复透视，以正面窗洞高1.55米估算尺度。两道红色檐带用浅色横线分开，正面两排分别读取53和52个浅色中心，规律间距中位数均约为9.45厘米。侧檐受阴影和透视压缩，侧面的砖面节距参考正面。[相机和控制点](measurements/roof-room-camera.json) · [正面两排檐砖](measurements/double-cornice-rhythm.json) · [钢窗横档位置](measurements/steel-window-pattern.json)

在未用于相机拟合的22列原照像素上，复核正面浅色檐线的上缘。近、远景导出的对应边线均方根偏差为1.29像素，最大约2.30像素。方间顶面、背侧截面、两侧不能看清的檐后构造和相邻瓦面进深均采用估值。[檐线逐列复核](measurements/independent-cream-belt.json)

## 模型与定位

近景模型包含14,328个三角面、87个可编辑组，远景包含8,712个三角面、78个可编辑组。每个导出网格均完成302次几何检查，近、远景各有七张视图。[建模源码](source/build_model.py) · [三档实体检查](../../../data/audit/yiding-village-roof-pavilion-v1/preflight/geometry-rays.json) · [来源与许可](SOURCES-LICENSE.md)

院界内保有七处城市建筑轮廓，3、9、27、31、35、41、45和47号分别落在不同的住宅排上。原照只署「江苏路495弄」，屋顶方间采用独立展页，七处原有建筑均保留。[院界、门牌和房屋轮廓](measurements/compound-and-original-buildings.json)
