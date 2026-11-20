# 真光大楼东立面

圆明园路209号为真光大楼，原属中华浸信会书局。它与西侧虎丘路128号的广学大楼在同一组建筑中，各自在市房管局名录中登记。真光靠圆明园路的一面在中心高处有四个独立小尖券，广学朝虎丘路的一面是跨越多层的大尖拱。黄浦区档案局记真光由邬达克设计，1930年建成，并将其记为十层；其他文献和现行地图记为九层。本模型参照外立面实有窗层和女儿墙确定高度。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [黄浦区档案局](https://web.archive.org/web/20200221134216/http://www.archives.sh.cn/shjy/tssh/201206/t20120607_35344.html) · [逐项来源](reference-review.json)

修缮设计方发表的圆明园路整街正立面带25米比例尺，图中真光大楼的砖面和突出檐缘宽约22.8至23.5米。现行底图东边从南到北约23.32米；历史冻结的同一来源面向北少约5.4米。正立面的七对窗列、大小两类砖壁柱、逐层收分的虎爪形浅石收头、中央尖券和北端高台均可从图纸和街照相互核对。2010年黄浦档案照片可辨四个凸字和原有石门楣。商铺玻璃外观参照修缮设计方的完成照，字形采用单独挤出的四字衬线体近似。[修缮项目与图纸](https://davidchipperfield.com/projects/rockbund-project) · [2014年街照](https://commons.wikimedia.org/wiki/File:China_Bapist_Publication%26Christian_Literature_Building_Shanghai.JPG) · [2022年修缮报道](https://www.163.com/dy/article/HBQPNU0I0514IGIT.html) · [街面和地块核对](footprint-review.json)

模型还原距圆明园路街墙约两米的浅段，两端和后界以截面收口。窗玻璃、门楣、钢框、凸字和出挑砖肋均为独立几何。街面图片和设计图均保留原作权利；Livelikerw的2014年摄影为 CC BY-SA 3.0，项目只链接原件。四字衬线体基于 Noto Serif CJK SC，字体子集采用 SIL OFL 1.1。地理数据来自 OpenStreetMap contributors（ODbL 1.0）与 Overture Maps Foundation。[独立页](../../../china-baptist-publication.html) · [字体声明](source/fonts/provenance.json) · [OFL](source/fonts/OFL.txt) · [项目许可证](../../../../../LICENSE)

在 `projects/shanghai` 目录运行下面的命令。所需工具为 Python、NumPy、Shapely、mapbox-earcut、fontTools、Node、gltfpack、Blender、ImageMagick 7 和 Open Image Denoise。构建命令会重开Blender工程并对比真实解码的网页近、远景。

```sh
python source/precise/huangpu-china-baptist-publication-building/source/build_model.py \
  --out assets/models/candidates/huangpu-china-baptist-publication-building \
  --audit data/audit/china-baptist-publication-v1 \
  --decoded /tmp/baptist-publication-decoded
```
