# 怡和洋行大楼临江立面

中山东一路27号、北京东路转角的现存钢筋混凝土楼始建于1920年，1922年落成。上海市房屋管理局首批名单第1A008条写作「怡和银行／市对外贸易局」。发现清单转录的1853年涉及同址沿革。本模型还原现存楼的临江主面和东北斜角。[第一批优秀历史建筑](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [上海名建筑志](https://web.archive.org/web/20200927090649id_/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108931.html) · [全部原始页面与照片](reference-review.json)

两侧各四个通高拱窗，围绕中央双扇门；粗凿石材的水平分缝、券石和四根跨层巨柱组成1920至1922年主体。正面前后两个时代的照片显示旧屋面带圆顶石屏，当代大檐上方则有两排窗、中央高女儿墙和旗杆。中文地方志与英文条目对原楼层数和加层次数记载不同。模型以2014、2025年的外观为准，未对每层冠以未经证实的增建年份。[现代正面](https://commons.wikimedia.org/wiki/File:Jardine_Matheson_Building_20251127.jpg) · [东北角](https://commons.wikimedia.org/wiki/File:Jardine_Matheson_Building_The_Bund_Side_View.JPG) · [旧屋顶](https://commons.wikimedia.org/wiki/File:Jardine_Matheson_Building_The_Bund_Old_Pic.jpg)

登记源面为宏块14-13720-6693的833号、OpenStreetMap建筑177930855。临江边约47.3米，斜角约10.5米。高度按照片比例估算，11米进深为模型截面。西侧凹院、楼内和相邻的扬子大楼各自保留。原生Blender中可按立面、构件名称编辑石券、门窗、柱头、檐口、女儿墙和旗杆。[地块与航影记录](footprint-review.json) · [公开地图建筑](https://www.openstreetmap.org/way/177930855)

在项目根目录运行下列命令即可生成三种GLB、可编辑Blender文件、居中相机预览和网格审计。需要Blender、gltfpack、ImageMagick、oidnDenoise、Node.js、Python、NumPy与Shapely。

```sh
python projects/shanghai/source/precise/huangpu-jardine-matheson-building/source/build_jardine.py \
  --out /tmp/jardine-model --audit /tmp/jardine-audit --decoded /tmp/jardine-decoded
```
