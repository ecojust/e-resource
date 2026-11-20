# 罗别根花园主宅

虹桥路 2310 号住宅位于长宁区程家桥，历史上称为罗别根花园。上海市房屋管理局首批名单 1M004 将原名记作「虹桥路2310号住宅」，登记使用单位为海南置地上海公司。长宁区规划和自然资源局将此处记为维克多·沙逊的一幢英式乡村别墅，建筑面积 960 平方米。地方志另记沙逊在虹桥路 2409 号的伊甸园，即后来的龙柏饭店一号楼。[首批正式名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [长宁区规划和自然资源局](https://www.shcn.gov.cn/col7698/20220823/1220533.html) · [地方志有关两处住宅的记载](https://web.archive.org/web/20200707200055/http://www.shtong.gov.cn/Newsite/node2/node71994/node81772/node81775/node81786/userobject1ai109010.html)

区规划资源局记 1932 年建造，杨浦区图书馆整理的资料和 2017 年报道记 1931 年，项目工作名录另记 20 世纪 40 年代初。模型呈现 1998 至 2017 年照片中可见的外观。南向两座山墙之间为后退的阳台与门厅。东南斜照能辨认东侧窗室、烟囱、外露黑木架和红瓦交屋面。[杨浦区图书馆资料及东南斜照](https://web.archive.org/web/20170416124048/http://www.yplib.org.cn/jdfzzdg/cfjz/33870.htm) · [2017 年花园立面](https://commons.wikimedia.org/wiki/File:English_Country-style_Villa_at_2310_Hongqiao_Road-2.jpg) · [逐张图像和年代依据](reference-review.json)

原始 OpenStreetMap 对象 `w1316079023@2` 记载同一门牌、旧名、使用单位和两层住宅。其原始轮廓与城市场景的 1431 号源面交并比为 97.53%。三幅 2017 年照片保存了相机经纬度和罗盘读数。其中一张近照的方向与源面质心有约 115° 出入，仅用作门廊和材料参考。花园一侧另两处拍摄点、区规划局立面照、卫星屋顶和原始地块共同决定本体朝向。源面向西伸出的狭长连接段、两排独立近邻、花园和室内均单列。后侧墙体、山墙高度、窗洞及装饰尺度为估计。[独立预览](../../../luobiegen-garden.html) · [屋顶与原始建筑核对](footprint-review.json) · [OSM 原件](https://www.openstreetmap.org/way/1316079023)

[原始 GLB](../../../assets/models/candidates/changning-luobiegen-garden-villa/changning-luobiegen-garden-villa-raw.glb) · [网页 GLB](../../../assets/models/candidates/changning-luobiegen-garden-villa/changning-luobiegen-garden-villa-web.glb) · [远景 LOD](../../../assets/models/candidates/changning-luobiegen-garden-villa/changning-luobiegen-garden-villa-lod.glb) · [可编辑 Blender 工程](../../../assets/models/candidates/changning-luobiegen-garden-villa/changning-luobiegen-garden-villa.blend)

## 复建

在 `projects/shanghai` 下执行以下命令。需要 Python、NumPy、Shapely 2.1 以上、Node.js、Blender 4.3、gltfpack、ImageMagick 和 Open Image Denoise。程序为窗洞、两层廊、半木构、交屋面、阁楼端墙、瓦垄和烟道分别生成可编辑部件。原始、网页和远景文件采用相同的米制坐标，X 沿主立面指向约 80°，Y 指向约 350°，Z 向上。GLB 使用标准 Y 向上。[构建程序](source/build_model.py) · [几何程序](source/villa_geometry.py)

```sh
python -B source/precise/changning-luobiegen-garden-villa/source/build_model.py \
  --out /tmp/luobiegen-assets --audit /tmp/luobiegen-audit \
  --gltfpack gltfpack --oidn oidnDenoise
```

程序与原创模型采用仓库 MIT 许可。Fayhoo 的原始照片采用 CC BY-SA 3.0，政府及地方文献图片用于外观研究。地图来源及其许可分别见配准记录。[仓库许可](../../../../../LICENSE) · [摄影出处](reference-review.json)
