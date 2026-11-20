# 八仙桥基督教青年会大楼（西藏南路双檐临街翼）

西藏南路123号的青年会大楼于1929年10月动工，1931年落成，设计者为李锦沛、范文照和赵深。1949年后曾用名淮海饭店，后改为青年会宾馆，2014年酒店更新。2024年上海市国资委的报道使用“锦江都城经典青年会酒店”。南京西路150号的西侨青年会和四川中路595–607号的浦光大楼各有自己的名录记录。后者是同一组织较早的会址，Commons 的同名分类中也混有它的照片。[上海市国资委2024年报道及照片](https://www.gzw.sh.gov.cn/shgzw_zxzx_gqdt/20240227/a8f150cf3d2746f98d137d4b528577d1.html) · [历史建筑名录](../../../data/model-todo/discovered-buildings.json) · [逐张照片核对](reference-review.json)

## 外观与范围

原建筑由三块体量组成，平面南侧凹入。西翼临街，下部三层浅色仿石，以上五排褐砖窗墙，屋顶双檐之间另有红柱窗廊。西立面下部九个开间，砖墙的窄窗每层可辨四个单窗和五对双窗，端面可见三列窗。檐角上翘，檐面深蓝色，檐下可辨蓝绿色斗拱、彩枋与红色边沿。来源所载十层是整处建筑的楼层数，较高部分在北侧。两份文字资料分别给出12,870和10,422平方米建筑面积，此处保留不同口径。[2014年街面全景，Livelikerw](https://commons.wikimedia.org/wiki/File:Marvel_Hotel_Shanghai.JPG) · [2011年街景，Legolas1024](https://commons.wikimedia.org/wiki/File:八仙桥基督教青年会大楼.jpg)

入口的石框高约八米，上角削斜，凹处有棂窗和“青年会”三字。模型依据2024年报道的入口近照制作后加雨篷、两侧小门和雕框所在的位置。近景呈现独立的窗洞、砖缝、窗格、上下两道曲面瓦檐、筒瓦、檐下承托和门额字。云纹雕饰、彩枋图案与字形按可见轮廓近似。屋顶不同时期有不同的商业招牌，模型止于瓦脊及脊内的平屋面。北面后楼、东翼、中央庭院、室内及现代屋面设备留待其他资料确认。[来源、拍摄年代及文件哈希](reference-review.json) · [双檐几何](source/eaves.py) · [街面几何](source/street_wing.py)

## 地图

冻结地图将西侧临街翼单列为宏块 `14-13720-6694` 的 `2224`，对应 OSM way `369238017`。临街边约37.08米，宽约11米，西边中点约东经121.4749825、北纬31.2292729。建模坐标中 X 正向沿街往南偏东约157.32°，Y 向楼内，glTF 的 Y 正向朝上、Z 正向朝街。建筑比例来自街景与足迹，尺寸为估计。三期19级卫星图均可区分西翼长屋顶与北、东两块，檐口存在显著视差。东后角旁另有源建筑，模型将后侧檐头收在本翼边界内。[冻结四点、影像收据与许可](reference-review.json) · [源范围配准](footprint-review.json) · [相邻建筑与地面检查](../../../data/audit/baxianqiao-ymca-v1/final-placement-contract.json)

## 成品与检查

[三维查看器](../../../baxianqiao-ymca.html) · [地图定位](../../../index.html#landmark=huangpu-baxianqiao-ymca&mode=overview) · [下载清单与哈希](../../../assets/models/candidates/huangpu-baxianqiao-ymca/manifest.json)

| 文件 | 十进制 MB | 字节 | 三角面 |
| --- | ---: | ---: | ---: |
| [原始 GLB](../../../assets/models/candidates/huangpu-baxianqiao-ymca/huangpu-baxianqiao-ymca-raw.glb) | 9.596 | 9,596,476 | 151,200 |
| [网页 GLB](../../../assets/models/candidates/huangpu-baxianqiao-ymca/huangpu-baxianqiao-ymca-web.glb) | 4.041 | 4,041,220 | 151,200 |
| [远景 GLB](../../../assets/models/candidates/huangpu-baxianqiao-ymca/huangpu-baxianqiao-ymca-lod.glb) | 1.529 | 1,528,920 | 60,876 |
| [Blender 源文件](../../../assets/models/candidates/huangpu-baxianqiao-ymca/huangpu-baxianqiao-ymca.blend) | 2.394 | 2,394,220 | 151,200 |

三种 GLB 各通过51项针对窗列、门廊、两道瓦檐和相邻空域的射线检查。网页与远景模型经过实际解码。原生文件重开后又与原始 GLB 按材料比较。[全景图](../../../data/audit/baxianqiao-ymca-v1/huangpu-baxianqiao-ymca-preview.png) · [双檐近景](../../../data/audit/baxianqiao-ymca-v1/eaves.png) · [入口近景](../../../data/audit/baxianqiao-ymca-v1/entrance.png) · [逐图检查](../../../data/audit/baxianqiao-ymca-v1/author-visual-review.json) · [网格检查](../../../data/audit/baxianqiao-ymca-v1/surface-checks.json) · [原生与解码记录](../../../data/audit/baxianqiao-ymca-v1/geometry-native.json)

## 重建

从仓库根目录执行，环境需有 Python 3、NumPy、Shapely 2.1以上、FontTools、Node.js、gltfpack 0.25、Blender 4.3、ImageMagick 7 和 Open Image Denoise 2.5。独立安装的工具可以用 `--gltfpack`、`--blender`、`--oidn` 指定。

```sh
python -B projects/shanghai/source/precise/huangpu-baxianqiao-ymca/source/build_model.py \
  --out /tmp/ymca-assets --audit /tmp/ymca-audit
python -B projects/shanghai/source/precise/huangpu-baxianqiao-ymca/source/check_surfaces.py \
  --manifest /tmp/ymca-assets/manifest.json --out /tmp/ymca-audit/surface-checks.json
```

原创几何与代码采用 MIT。牌字使用重命名的 Noto Serif CJK SC 三字子集，字体遵循 SIL OFL 1.1。照片用于核对形体；原页列有作者与许可。Esri Wayback 图像归相应权利人，OpenStreetMap 数据 © OpenStreetMap contributors（ODbL 1.0），Overture 和 CNBH 估高数据适用各自许可。[MIT](../../../../../LICENSE) · [字体来源](source/fonts/provenance.json) · [OFL](source/fonts/OFL.txt) · [图像及地图资料](reference-review.json)

独立页已实测 1250×820 桌面和 390×844 手机的近、远景切换及四项原文件下载。[浏览器报告](../../../data/audit/baxianqiao-ymca-v1/viewer.json) · [截图复核](../../../data/audit/baxianqiao-ymca-v1/viewer-visual-review.json)
