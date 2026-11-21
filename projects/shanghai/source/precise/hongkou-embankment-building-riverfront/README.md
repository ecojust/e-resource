# 河滨大楼临苏州河立面

河滨公寓由新沙逊洋行投资，公和洋行设计，1935年竣工。市房管局第二批优秀历史建筑2F002登记在虹口区北苏州路340号。2022年修缮报道将整栋楼列在400号，地图还以370号标注一个临河入口。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) [2020年修缮前资料](https://sh.sina.com.cn/news/m/2020-11-19/detail-iiznctke2172994.shtml) [2022年修缮后报道](https://www.peopleapp.com/rmharticle/30026793088)

2023年建筑专访将整座公寓描述为双向S形。这次制作其中靠河的一段。沿苏州河岸的长翼向东北延伸，在屋顶亭的位置转入U形入口庭院，再从最东端的圆弧窗返回河岸。2020年航拍可辨长翼上的四道褐色楼梯窗带，以及后方的原有屋面。2022年临河照片记录了修复后的壁柱、水刷石外墙、窗带与公用入口。2025年5月的跨河近照还能分辨连续弧窗之间的细钢格、石质窗台、阳台墙与亭顶开敞层。当年的报道记载原楼8层、后期部分增建至11层。现状长翼按一层基座上九排可见住宅窗制作，亭冠和局部女儿墙另计。[2023年建筑专访](https://www.thepaper.cn/newsDetail_forward_22162999) [2013年跨河实照](https://commons.wikimedia.org/?curid=30815091) [2025年5月CC0实照](https://commons.wikimedia.org/?curid=164811427) [逐项来源与署名](reference-review.json)

## 建筑范围

地图第14-13720-6693块中的2146与3142相接，两份来源均具名The Embankment House，现行OSM含河滨大楼中文名。西南长翼和东北折翼与当前OSM的轮廓交并比分别为98.25%和98.72%。模型使用两份原始楼脚配准，并用2024与2026两组影像核对长翼、两个圆端、入口庭院和亭的位置。独立的同组楼体1459和附近的河滨豪园都保留原样。[楼幢、两期影像及门牌](footprint-review.json)

本版交付沿岸墙面、四处楼梯窗带、阳台和窗台、三个圆转角、屋顶亭以及入口庭院的三面窗墙。从临河墙面向内约四米处收口。后部原楼、完整屋面、历次加层的逐户变化、室内与屋顶设施保留待考。窗台、钢格、构件厚度和高度按照片及两档原城体量估算。[单独旋转及下载](../../../embankment-riverfront.html) [城市地图](../../../index.html#landmark=hongkou-embankment-building-riverfront&mode=overview) [模型核验](../../../data/audit/embankment-riverfront-v1/README.md)

## 文件和重建

近景原始与压缩文件各130,980个三角面，远景62,394面。可编辑Blender文件内有96个命名网格。三份模型和工程均使用原创几何及材质，按项目MIT许可开放。外部照片只供尺寸、年代和形体对照。资料中另存原摄影者、文件地址及实际许可。[全部文件与签名](../../../assets/models/candidates/hongkou-embankment-building-riverfront/manifest.json) [MIT](../../../../../LICENSE)

在仓库根目录运行以下命令。需要Python、NumPy、Shapely、Blender、Node.js、gltfpack、ImageMagick 7与Open Image Denoise。

```sh
python -B projects/shanghai/source/precise/hongkou-embankment-building-riverfront/source/build_model.py \
  --out /tmp/embankment-assets --audit /tmp/embankment-audit --decoded /tmp/embankment-decoded
python -B projects/shanghai/source/precise/hongkou-embankment-building-riverfront/source/check_surfaces.py \
  --manifest /tmp/embankment-assets/manifest.json --out /tmp/embankment-audit/rays.json
```
