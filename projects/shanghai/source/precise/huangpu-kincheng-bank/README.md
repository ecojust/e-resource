# 金城银行大楼（江西中路200号临街主楼）

黄浦区江西中路东侧，工部局历史主楼对街。此处是金城银行原址，后来由交通银行使用，入口正上方现在可见“交通银行”四字。外滩14号另有一处交通银行历史大楼，位于中山东一路，地图给这两处各自定位。[历史条目](https://zh.wikipedia.org/w/index.php?oldid=89527694) · [看看新闻2021年实地报道](https://www.kankanews.com/a/2021-04-22/0039733930.shtml)

## 可见外观

江西中路立面采用花岗岩饰面。中部门洞前有两根多立克式圆柱，门楣上有弧肩和圆形徽章，再向上是矩形长窗、三角形窗楣、题名、半圆拱窗及弧形石阳台。中轴两侧各有三组较窄的窗，低处的圆弧窗头是实心石面。两端的高拱内则有玻璃，拱上另有成对窗和三联窗。模型用实际窗洞与分格金属框区分两种拱形，用独立构件表现石缝、檐口托块、门柱、牌字和阳台弧面。[2015年江西路立面照片](https://commons.wikimedia.org/wiki/File:Former_Kincheng_Banking_Corporation_Building_Shanghai.JPG) · [何晓云拍摄的街面细节](https://www.meipian.cn/3g232286)

1924年开工、1926年1月底落成是建筑条目采用的日期；仓库历史建筑名录第1批41号记为1927年。原楼层数、1940年加层及后来资料所称七层有不同口径。本模型依照2015年照片能辨认的临街开间与上部两排窗制作，层高和屋顶标高为估计。徽章按较近照片可辨的凸形外缘处理，旧记载所述龙、凤、斧细纹在照片中不能确认。[名录原始记录](../../../data/model-todo/discovered-buildings.json) · [照片日期、来源及SHA256](reference-review.json)

## 地图范围

冻结地图记录来自 OSM way `380339899`，宏块 `14-13720-6694` 的建筑 `1708`。交通银行 POI 位于其中，西边界沿江西中路，长约35.5米。局部原点取西侧路面边界中点，约东经121.482780、北纬31.237527，Blender 局部 X 向南沿街（方位角约167.56°），Y 向东入楼。导出的 glTF 使用 Y 向上、Z 正向朝街。地图以十层推算32米，建模另据立面资料估计高度约30米。已比较三期19级历史卫星图以排查屋面和相邻体量，屋檐斜投影有明显位移。[定位线索、瓦片和冻结数据收据](reference-review.json)

模型进深约20米，仅到已确认的临街地图块，另有独立建筑位于东侧，北邻汉口路151号，南邻都城饭店。历史建筑名录和单份楼面面积资料不足以证明周边屋顶、设备和院内翼楼的归属。侧后墙使用素面收边，室内、屋面设备和当前无法核实的东侧部分留待调查。正门凹景止于暗色背衬。

## 成品与检查

[三维查看器](../../../kincheng-bank.html) · [地图定位](../../../index.html#landmark=huangpu-kincheng-bank&mode=overview) · [独立实景范围配准](footprint-review.json) · [下载清单与哈希](../../../assets/models/candidates/huangpu-kincheng-bank/manifest.json)

| 文件 | 字节 | 三角面 |
| --- | ---: | ---: |
| [原始 GLB](../../../assets/models/candidates/huangpu-kincheng-bank/huangpu-kincheng-bank-raw.glb) | 1,769,708 | 35,368 |
| [网页 GLB](../../../assets/models/candidates/huangpu-kincheng-bank/huangpu-kincheng-bank-web.glb) | 563,492 | 35,368 |
| [远景 GLB](../../../assets/models/candidates/huangpu-kincheng-bank/huangpu-kincheng-bank-lod.glb) | 363,520 | 22,680 |
| [可编辑 Blender](../../../assets/models/candidates/huangpu-kincheng-bank/huangpu-kincheng-bank.blend) | 494,060 | 35,368 |

正面图和入口近景从重开的 Blender 文件输出。原始、网页与远景模型各通过35项表面检查，范围包括两种不同开窗、门道退深、屋顶和邻楼边界。[正面图](../../../data/audit/kincheng-bank-v1/huangpu-kincheng-bank-preview.png) · [入口近景](../../../data/audit/kincheng-bank-v1/entrance.png) · [看图记录](../../../data/audit/kincheng-bank-v1/author-visual-review.json) · [三套网格检查](../../../data/audit/kincheng-bank-v1/surface-checks.json) · [Blender 重开和解码校验](../../../data/audit/kincheng-bank-v1/geometry-native.json)

## 重建

从仓库根目录执行。环境需有 Python 3、NumPy、Shapely 2.1以上、FontTools、Node.js、gltfpack 0.25、Blender 4.3、ImageMagick 7 及 Open Image Denoise 2.5。可用 `--gltfpack`、`--blender` 和 `--oidn` 指定可执行文件位置。

```sh
python -B projects/shanghai/source/precise/huangpu-kincheng-bank/source/build_model.py \
  --out /tmp/kincheng-assets --audit /tmp/kincheng-audit
python -B projects/shanghai/source/precise/huangpu-kincheng-bank/source/check_surfaces.py \
  --manifest /tmp/kincheng-assets/manifest.json --out /tmp/kincheng-audit/surface-checks.json
```

程序输出原始、网页、简化远景和可编辑 Blender 四件模型。独立射线检查读取实际网格，对中部门洞、拱窗、盲楣、端部上层弧窗、屋面与邻楼空域取样。网页与远景 GLB 通过项目的 meshopt 解码器读取。[建模源码](source/kincheng.py) · [打包程序](../../../tools/package_architectural_model.py) · [表面检查](source/check_surfaces.py)

## 许可

原创几何与代码采用 MIT。“交通银行”四字以 Noto Serif CJK SC 的重命名子集挤出，字体遵从 SIL OFL 1.1，字形与原招牌有差异。照片不做贴图。Livelikerw 的 Commons 照片许可为 CC BY-SA 4.0，何晓云的照片仅作研究。地图来源为 © OpenStreetMap contributors（ODbL 1.0）及 Overture 相应派生记录。Esri World Imagery Wayback 与相应数据提供者保留影像权利。[MIT许可](../../../../../LICENSE) · [字体来源](source/fonts/provenance.json) · [OFL许可](source/fonts/OFL.txt) · [图像署名](reference-review.json)
