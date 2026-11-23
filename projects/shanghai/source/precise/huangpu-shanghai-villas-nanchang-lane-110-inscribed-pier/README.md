# 上海别墅南昌路110弄双题名石柱与112号院墙

从南昌路面向弄内，左右两根石柱各刻「上海別墅」。西侧矮墙接到写有112号的端墩，东柱向弄内的一侧挂着绿色110弄牌。此件按2020年2月的街面制作。照片中的两个告示保留了外形，告示正文在街景中无法辨读。[查看独立模型](../../../shanghai-villas-inscribed-pier.html) · [街景与测点记录](measurements/street-measurements.json)

上海市房屋管理局第四批优秀历史建筑名录将上海别墅列为4C006，地址为南昌路110弄、112–122号。原卢湾区地方志也将「上海别墅」记在110弄，把「花园别墅」列在136弄。新华网在2020年6月记录了南昌路110弄的综合修缮。[上海市房屋管理局原表](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [地方志地址表](https://web.archive.org/web/20160327115113id_/http://www.shtong.gov.cn/Newsite/node2/node2245/node70862/node70869/node70913/node70917/userobject1ai73689.html) · [新华网报道](https://web.archive.org/web/20200807181700id_/http://sh.xinhuanet.com/2020-06/16/c_139143167.htm)

## 石柱、院墙与铁门

2020年2月20日从街上三个位置反算出柱心距3.67米，2023年6月9日另三个位置量得3.74米。模型取柱高3.90米、柱心距3.67米。每根柱的灰色题面向内凹进，四字从上到下排列，外面一道斜边框住题字。近景字槽切进石面，槽底填深色。柱脚向外放大，顶部石帽分级收进。[两期街景测量](measurements/street-measurements.json) · [两柱与院墙的部位测点](measurements/frontage-details.json)

112号短墙从西柱外侧延伸约3.2米。墙脚有勒脚，墙顶两道横枋高约2.0至2.4米，九道木条继续伸到约3.6米。冬季街景中的西门扇贴近弄内，东门扇半掩，扇顶的铁花沿起伏曲线排列。门扇转角、铁件截面、石柱进深和石材本色按照片估计。原城的街区建筑与真实地面另行配准。[尺寸参数](source/pier_dimensions.json) · [街区位置记录](footprint-review.json)

## 模型与复核

近景有20,392个三角面，远景有6,508个。两档均有九幅从解码模型生成的视图，分别查看题面、柱帽、铁花、绿牌、112号端墩以及从弄内回望街面的门扇。原始模型与两个网页档各以278道射线核对，含128道穿过门间、木条间和露天上方的净空检查。[近景街面图](../../../data/audit/shanghai-villas-nanchang-lane-110-inscribed-pier-v1/preflight/full-views/nanchang-front.jpg) · [东柱110弄牌](../../../data/audit/shanghai-villas-nanchang-lane-110-inscribed-pier-v1/preflight/full-views/green-address.jpg) · [几何核验方法](../../../data/audit/shanghai-villas-nanchang-lane-110-inscribed-pier-v1/verify-export.py)

从本目录运行下列命令可重建原始GLB、两个网页档、带九个检查相机的可编辑Blender文件及重开、解码与表面比对记录。环境需要仓库列出的Python几何依赖、Blender、gltfpack、ImageMagick和Open Image Denoise。

```sh
python -B source/build_model.py --out ./shanghai-villas-model --audit ./shanghai-villas-check
```

建筑几何与材质采用仓库的MIT许可。两套字体子集分别用于柱名和门牌，采用SIL Open Font License 1.1。第三方街景用于识别和量测，成品使用自建几何和材质。[资料与权利说明](reference-review.json) · [字体来源](source/lettering/provenance.json) · [字体许可](source/lettering/OFL.txt)
