# 武夷路174号花园住宅

长宁区武夷路168号翡悦里园内的174号别墅，名录地址为武夷路174号。历史住宅位于武夷路南侧。2018年的照片拍到院门柱上写着186号；2024年长宁区的报道明确将这一栋与棟梁的入驻地址相联。2020年沿街实景、2024年开业照片和2025年院内正面照可用临街木格山墙、双窗、砖角和烟囱相互辨认。同一街区的188号别墅另有自己的范围。[市级登记与七组图片记录](measurements/identified-villa-and-two-garden-fronts.json)

临街山墙下方的阳台向右呈弧形，左段覆盖券门。三扇底层窗并排开在凸窗上。向园内的一面有连贯的弧形阳台、落地门窗和两处形制不同的屋顶窗。2025年发表的临街正面照清楚记录了白篷、金属栏杆和石材窗套；2024年10月开业图组补充了花园侧的玻璃与栏板。

## 三张照片的同面复核

两扇上层窗和下一层左窗的边缘能在2018、2024和2025年的照片间复查。以2025年照片为参考，2018年图中有五个清楚的窗边点可用于计算单应矩阵，2024年斜照有七个。每幅图另留三个标记用于检验，原分辨率下的均方根误差分别为14.61和7.47像素。这个拟合只适用于窗所在的墙面。阳台、檐口和烟囱各自有独立进深。[原始观测](measurements/wuyi-road-gable-three-photographs.json) · [保留点误差](measurements/three-view-window-registration-results.json)

```sh
python measurements/check-wuyi-road-registration.py
```

[照片来源与许可](SOURCES-LICENSE.md)

## 宅址、朝向与尺度

2020年沿武夷路的两个全景位置都能辨认三角形木格山墙。用两站观测交会，上层两窗的中心约相距2.60米，临街主墙宽约7.2米。这个尺度受全景点位和窗框读数影响。2010、2019、2021、2025年航片及街景共同指向道路南侧。在地图库中，与实拍一致的是轮廓1577。路北的两个导航门牌点靠近底商，与院内住宅有距离。[定位、交会和精度](measurements/placement-identity.json) · [四期瓦片日期与原始服务响应](measurements/tile-date-responses.json)

## 房屋的两面

临街一面以两扇上层窗所在的墙面定比例。木格山尖前有深挑檐。入口一侧的阳台平直，三扇底层窗一侧向外折转，券门上方的石托向内收曲。两处白色遮阳篷上的英文店名按照片重新绘制。朝街的较低屋翼还有一组平顶老虎窗。北庭石板和修剪灌木的范围取自2025年入口照片。

花园一面的大老虎窗有斜屋顶，小老虎窗覆浅坡顶。两处窗台前各留一段低瓦面，与左右两片大坡屋面分别交接。开业照片中另可辨凸窗玻璃、玻璃门上的布篷和两侧长短不同的阳台。阳台后墙、外凸玻璃、挑檐与主脊各有不同的进深。近照可以量门框和栏杆，远屋脊须结合航片与街侧的山尖高度估计。按525、650像素两种试用焦距反投，交叉屋脊在所取进深处约高9.6至10.3米。东、西两侧被房舍和树木遮住的部位仅保留能确定的大体轮廓。[花园侧照片测点](measurements/south-garden-two-photographs.json) · [屋顶19点与焦距、进深变化](measurements/garden-roof-nineteen-landmarks.json) · [东侧凸窗](measurements/south-oriel-image-observations.json)

两幅花园照片都能看见红瓦滴水沿和三块白色门篷。用滴水沿的两端和中部校核两站后，模型把南檐放在门窗墙面前约0.30米、离地约5.52米。黑色雨槽在瓦沿下方，白色门篷再低一层。较早的近景试模有三处门篷被屋顶遮盖；记录中保留旧相机和远屋脊上的留出点，可复查调整前后的差别。[街侧与花园侧的相片登记](measurements/south-garden-two-photographs.json)

## 重建与实测

从本目录运行以下命令。Python 需要 NumPy、Shapely 2.1 与 Pillow。网页打包使用 Node.js 和 gltfpack，可编辑工程使用 Blender。最后一条命令由 Chromium 在本地打开项目页面，实际切换近远模型和机位并下载四件文件。

```sh
python measurements/export_checked_model.py full --out output/exports
python measurements/export_checked_model.py lod --out output/exports
python measurements/package-web-model.py output/exports output/models output/audit
python source/build_blender_source.py output/exports/full-source.glb output/models/changning-wuyi-174-dongliang-garden-villa-editable.blend output/audit/native-reopened.json
python measurements/register-native.py output/models output/audit/native-reopened.json
python measurements/render-villa-stations.py output/exports/full-source.glb output/previews
python measurements/check-street-rays.py output/exports output/audit/street-three-models.json
python measurements/check-viewer.py output/ui
```

网页验收从项目的 `assets/models/candidates/changning-wuyi-174-dongliang-garden-villa/` 目录加载模型和清单。替换网页文件时，应将 `output/models/` 中的五件一起放入该目录。[浏览花园住宅](../../../wuyi-174-dongliang-garden-villa.html) · [模型复核](../../../data/audit/wuyi-174-dongliang-garden-villa-v1/README.md)
