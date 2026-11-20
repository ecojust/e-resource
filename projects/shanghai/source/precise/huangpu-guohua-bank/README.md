# 国华银行大楼 · 东南转角与弧形窗墙

上海市房管局第二批优秀历史建筑2A019列国华银行大楼，名录所载现名为「黄浦税务局」，地址北京东路342号。上海市银行博物馆记1931年8月由通和洋行与李石林承接设计，1933年8月竣工。街角主门朝东南，拱门约两层高；主塔与两边的弧翼高低有别。其后翼部加层，因此当年画稿和较晚实景的屋缘轮廓有差别。另有二手资料将其称为四川大楼，延安东路110号同名建筑另属城市体块1848。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [建筑、街照及修缮报道](reference-review.json)

中央直塔为三列窗，两侧各有三列沿弧排列的窗，主门配置半圆形放射铁格、花岗石门框和内退石阶。建筑原设计透视和两张街照共同约束门塔及弧翼。2014年门楣为「上物金属」，2023年12月重新启用主门时，四块石牌已恢复为右起「國華大樓」。本件采用重开时的外门状态，上部以可辨窗排和原图中的浮雕位置为准。小浮雕、砖石线脚、尖角、色彩和曲面半径均为按图近似。两条街继续延伸的翼墙、楼内、背立面和其余屋面待后续核实。[2023年上观新闻](https://export.shobserver.com/baijiahao/html/696935.html) · [2014年Livelikerw街照，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:342_East_Beijing_Rd._Shanghai.JPG) · [独立页](../../../guohua-bank.html)

现行OSM来源w494082451与原城市1253的投影交并比约98.77%。模型以主门两边外侧凸点作控制，弦长约9.14米；中间另有内退边点，约束主门内凹。城市源粗体高25.6米，博物馆的全楼记载约50米；模型只补有实景和图稿约束的街角。四字为独立网格，衬线形体据有再分发许可的字体子集近似。地理数据来自 OpenStreetMap contributors（ODbL 1.0）与 Overture Maps Foundation；模型几何依项目MIT许可证。[GIS控制](footprint-review.json) · [字体来源](source/fonts/provenance.json) · [字体许可](source/fonts/OFL.txt) · [项目许可证](../../../../../LICENSE)

从 `projects/shanghai` 执行下面的构建命令。依赖包括Python、NumPy、Shapely、mapbox-earcut、fontTools、Node、gltfpack、Blender、ImageMagick 7 和 Open Image Denoise。原生工程会重新打开，并与已导出的原始网格、实际解码的网页近远景核对。

```sh
python source/precise/huangpu-guohua-bank/source/build_model.py \
  --out assets/models/candidates/huangpu-guohua-bank \
  --audit data/audit/guohua-bank-v1
```
