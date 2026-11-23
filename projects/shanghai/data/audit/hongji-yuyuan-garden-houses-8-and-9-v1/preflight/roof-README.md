# 弘基园八、九号楼屋顶与九号北窗

[屋顶与北山墙实网图](roof-and-north-gables.jpg)绘出两宅瓦面、截顶和九号北侧凹进山墙。[逐档汇总](roof-and-north-windows-review.json)列出两份作者网格、两份独立解码网格及逐束报告的校验值。[闭合构件报告](roof-editable-components.json)逐材质记录瓦面与烟囱的纹理坐标、可编辑构件数量及最小封闭体积。

八号楼18个檐底测点中有17个首中奶油色漆面，另一个先碰烟囱红砖。九号楼18个测点全部落在奶油色漆面。九号楼北面七樘窗的49束墙面法向检查均首中预期材料。2023年两张斜照共34个像点中，近档22个、远档23个在原像点直接命中，其余在八像素内可重得。两张照片遮挡了两个底窗窗台的部分边线，标高估计随原始测点保留。

八号楼图04原有单面配准会把观察点落入九号楼，保留该解作对照。按草坪和两幢相对位置重新配准，原七点有六点从草坪正面首中预期屋面。2016年另一张斜照五点均直接命中，2023年图06八点中有六点直接命中。各期正射的原像点和0.77米邻域读数可在逐档报告中复查。

从模型作者目录运行以下命令。参数 MESH 指向未经压缩的作者网格或已独立解码的发布网格。

```sh
python measurements/check_hongji_roofs.py --mesh "$MESH" --out roof.json
python measurements/check_nine_north_windows.py "$MESH" windows.json
python measurements/render_hongji_roof_review.py --mesh "$MESH" --out roof-and-north-gables.jpg
```
