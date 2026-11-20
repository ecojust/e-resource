# 东方汇理银行（外滩29号临江立面）

中山东一路29号的现存银行楼坐西朝东。上海市房屋管理局第一批优秀历史建筑表编号 **1A009**，原名东方汇理银行，登记使用名光大银行。外滩29号往南是格林邮船大楼，再往南越过北京东路才是27号怡和洋行。本模型取面向黄浦江的东面，宽约21.93米。临江照片和街坊底图均可区分相邻楼栋。[第一批名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [街坊位置图](../../../data/audit/banque-de-lindochine-v1/street-blocks.png)

地方志记载这里1911年兴建新楼。杨浦区图书馆转载上海档案信息网蒋遵和的文章进一步记载，1911年旧房拆除，1914年新楼投入使用。建筑三层，总高21.6米。1956年后使用东方大楼名称，1995年中国光大银行上海分行迁入。2012年照片说明另记1910年完工，此处采用可查到拆旧和启用两阶段的档案记述。[上海市地方志办公室《上海名建筑志》](https://web.archive.org/web/20200927102404/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108933.html) · [杨浦区图书馆《东方汇理银行大楼》](https://web.archive.org/web/20131220192039/http://www.yplib.org.cn/structure/jdsh/bnsz/dg_82153_1.htm)

## 立面和取舍

底层的四扇半圆拱窗围绕独立的中央双扇门。门前的小圆柱承托折断弧形山花，二、三层之间两根光身爱奥尼克巨柱分隔中间三开间。五组二层窗带半圆盲拱和透空石栏，三层矩形窗按一、二、三、二、一列布置。深檐排有齿饰，两端高起的女儿墙有垂花和圆饰，中段为透空栏板。现代行名取自实照，标志和石雕纹样作概形处理。宽度据底图东边线取值，各档层高、窗深、柱径和花饰据照片比例估计。[2017年正面](https://commons.wikimedia.org/wiki/File:Banque_de_l%27Indochine_Building,_Shanghai,_Dec_2017.jpg) · [2012年斜照](https://commons.wikimedia.org/wiki/File:Former_Banque_de_l%27Indochine%2C_The_Bund%2C_Shanghai.jpg) · [2025年现状](https://commons.wikimedia.org/wiki/File:Banque_de_l%27Indochine_Building,_Shanghai_20250501.jpg)

立面止于东侧墙线向楼内2.04米的剖面。主地图保留原有楼体更深的部分并封合截面。西端屋面、改建阶段、内部玻璃天棚和院落仍待平面或可定位照片。街坊定位采用开放街图现行楼栋177930859第11版及冻结源2037，二者投影交并比约98.46%。地图数据归属 © OpenStreetMap contributors、Overture Maps Foundation。参考图片仅用于辨认；模型、雕饰、窗框和渲染由程序独立生成，几何使用项目 MIT 许可，行名字形所用子集使用 SIL OFL 1.1。[测量和底图绑定](footprint-review.json) · [取证网址、作者、许可与文件指纹](reference-review.json) · [字体来源](source/fonts/provenance.json)

## 浏览和重建

[上海主地图](../../../index.html#landmark=huangpu-banque-de-lindochine&mode=overview) · [独立交互预览](../../../banque-de-lindochine.html) · [下载清单](../../../assets/models/candidates/huangpu-banque-de-lindochine/manifest.json) · [地图及模型验收](../../../data/audit/banque-de-lindochine-v1/README.md)

从 `projects/shanghai/` 运行。使用 Python 3、NumPy、Shapely 2.1、fontTools、Node、Blender、gltfpack、ImageMagick 7 和 Open Image Denoise；后两种外部可执行工具的路径可传给打包脚本。脚本同时导出原始 GLB、两个 meshopt 细节版本、可编辑 Blender 工程及由重新打开的工程生成的渲染图。

```sh
python -B source/precise/huangpu-banque-de-lindochine/source/build_model.py \
  --out /tmp/bund29/assets --audit /tmp/bund29/audit --decoded /tmp/bund29/decoded
python -B source/precise/huangpu-banque-de-lindochine/source/check_surfaces.py \
  --manifest /tmp/bund29/assets/manifest.json --out /tmp/bund29/audit/surfaces.json
python -B data/audit/banque-de-lindochine-v1/verify-placement.py \
  --manifest /tmp/bund29/assets/manifest.json --work /tmp/bund29/map --out /tmp/bund29/audit
```
