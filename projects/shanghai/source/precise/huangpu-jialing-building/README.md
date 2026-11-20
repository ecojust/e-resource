# 迦陵大楼 · 南京东路北立面

上海市房管局第二批名录2A026列原名「迦陵大楼」、现名「嘉陵大楼」、南京东路99号。上海市地方志另记四川中路346号、1937年12月竣工，全楼由南至北分别为十三层、十层和八层，原底层曾由大通银行承租。2014年街照的中文说明明确为上海迦陵大楼；同一照片的英文文件名写作 Hamilton House，容易和江西中路170号的汉弥登大楼混淆。两栋建筑的道路、轮廓和模型入口均可独立核对。[市房管局第二批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [上海市地方志](https://web.archive.org/web/20191118223010/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108947.html) · [逐项来源](reference-review.json)

2014年北端街照显示，石基上六行窗按两侧各一列、中央四列排布，中部三条外凸竖肋直达赭色檐带。底部石门是矩形，两侧各有上下两块深色金属饰板，中间还有短槽纹。模型依照这幅照片制作双层石基、天花、入口四级台阶、六列窗及檐边尖叶纹。当前银行标识与街树遮挡的部位只按可见构件处理；金属饰板小纹样为近似。四川中路长立面、层层升高的南段、其余屋顶与背侧仍待补全。[Livelikerw，2014年1月14日，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Hamilton_House_Shanghai.JPG) · [独立页](../../../jialing-building.html)

现行OSM北边线长17.61米，与冻结来源1468的平面交并比为98.78%。照片经单幅透视校正后，侧翼檐口高度估计约29.9米，误差约一至两米。地块西缘贴近独立来源2324，模型在西端收窄，使共享地界处的低层几何能够完整保留。独立几何沿用项目MIT许可证；航片、照片及网页图像用于核对，保留原作者的权利。空间资料来自 OpenStreetMap contributors（ODbL 1.0）与 Overture Maps Foundation。[实测边线](footprint-review.json) · [证据与取景误差](reference-review.json) · [项目许可证](../../../../../LICENSE)

从 `projects/shanghai` 执行下面的命令。构建需要 Python、NumPy、Shapely、mapbox-earcut、Node、gltfpack、Blender、ImageMagick 7 和 Open Image Denoise。完整任务会重新打开原生工程，逐材质核对网格，并实际解码网页近、远景。

```sh
python source/precise/huangpu-jialing-building/source/build_model.py \
  --out assets/models/candidates/huangpu-jialing-building \
  --audit data/audit/jialing-building-v1
```
