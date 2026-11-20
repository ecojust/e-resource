# 瑞金宾馆1号楼（马立斯住宅主楼与庭院立面）

上海市房屋管理局的首批优秀历史建筑1C002登记为「瑞金二路住宅」，使用名「瑞金宾馆1号楼」，地址瑞金二路18号。当代上海瑞金洲际酒店使用瑞金二路118号。上海文旅推广网将1号楼列为1917年起建的英商马立斯住宅，砖木结构两层，主辅楼呈L形，合计建筑面积1335平方米。1956年成立瑞金宾馆，1984年向社会开放。徐汇区太原路160号的瑞金宾馆太原别墅属另一处院落。[第一批官方名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [上海文旅推广网](https://www.meet-in-shanghai.net/cn/shanghai-cultural-relics-protection-unit/ruijin-2nd-road-residence-044290/) · [酒店当代地址](https://www.ihg.com/intercontinental/hotels/cn/zh/shanghai/shgsr/hoteldetail)

酒店公开的1:500总平面可直接区分1号主宅、北侧2号楼和后建的酒店主楼。以复兴中路、茂名南路、瑞金二路、永嘉路组合的四个街道路口定位，控制点残差约2.4至2.8米。门廊屋面在四期航片中可辨，其中心用于补充约4米的局部位置修正。主楼实际地面位置仍有约3至5米不确定性。图上1号主体占地约664平方米，两层面积与文旅资料相近。2019、2022、2024和2026四版航片均可辨出相同主楼、门廊与庭院另一侧的独立楼栋。[业主公布的总平面 PDF](https://digital.ihg.com/is/content/ihg/intercontinental-shanghai-4180232119-original?fmt=pdf) · [控制点和底图记录](footprint-review.json) · [主宅、2号楼与城市分段图](../../../data/audit/ruijin-guesthouse-01-v1/site-plan.png)

北庭院面用清水红砖、交错石隅、浅色窗套、成对塔司干圆柱和可透空的石阳台构成。酒店的正面照片可逐扇辨认东西两侧不同的开窗数量。2009、2011和2013年的院内视角用于核对窗廊衔接、坡屋顶、烟囱和门廊出挑。东端凸窗、后侧屋面体量据总图与航片确定，层高、具体坡度、木窗格及石材颜色依照片估计。与2号楼相通的带券洞翼廊、现代主酒店、南侧花园喷泉及室内尚待单独建模。[酒店方庭院正面实照](https://digital.ihg.com/is/image/ihg/intercontinental-shanghai-4193710534-2x1?wid=1100) · [2009年院内照片](https://commons.wikimedia.org/wiki/File:Ruijin_Hotel.jpg) · [2011年院内照片](https://commons.wikimedia.org/wiki/File:Ruijin_hotel_1.jpg) · [2013年现场图文](https://shanghailander.net/2013/08/intercontinental-ruijin-hotel/)

[进入上海地图](../../../index.html#landmark=huangpu-ruijin-guesthouse-01&mode=overview) · [单体交互页](../../../ruijin-guesthouse-01.html) · [模型下载清单](../../../assets/models/candidates/huangpu-ruijin-guesthouse-01/manifest.json) · [来源、作者与照片许可](reference-review.json) · [模型验收](../../../data/audit/ruijin-guesthouse-01-v1/README.md)

## 重建

几何源与渲染依项目 MIT 许可。照片、酒店总平面和卫星影像只外链作证。道路归属 © OpenStreetMap contributors，城市分块数据由 Overture Maps Foundation 汇集，航片归 Esri 及其影像供应商。使用 Python 3、NumPy、Shapely 2.1、Node、Blender、gltfpack、ImageMagick 7 与 Open Image Denoise。从 `projects/shanghai/` 运行以下命令。

```sh
python -B source/precise/huangpu-ruijin-guesthouse-01/source/build_model.py \
  --out /tmp/ruijin/assets --audit /tmp/ruijin/audit --decoded /tmp/ruijin/decoded
python -B source/precise/huangpu-ruijin-guesthouse-01/source/check_surfaces.py \
  --manifest /tmp/ruijin/assets/manifest.json --out /tmp/ruijin/audit/surfaces.json
```
