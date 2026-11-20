# 亚细亚大楼 · 外滩1号

在中山东一路与延安东路的路口，面向两条街的墙面各有七开间。两侧翼部各两间，中间三间向内退进。模型用真实洞口和后墙表现中段廊道的深度，用独立柱身、卷涡、檐部和铁栏表现门廊及上层柱廊。东南角后退的单列窗把两个正面连接起来。

市房管局首批名录将本楼列为 **1A001 亚西亚大楼，中山东一路1号**。同表相邻的 **1A002 上海总会** 位于2号。本文采用近年报刊通行的“亚细亚大楼”。项目历史条目列1915年，《新民晚报》报道记1916年落成，建筑史资料记1913年开工、1930年代增建第八层。模型表现照片中的现存八层外观。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [新民晚报，2021年](https://wap.xinmin.cn/content/32078722.html)

## 照片与几何

2011年的路口照片同时拍到了两面门廊。2021年和2025年的东立面照片提供了中央三跨、柱对、栏杆和顶层角亭的正面比例。《新民晚报》2019年对东、南立面横竖各三段的描述与这些照片相符。[2011年东南转角](https://commons.wikimedia.org/wiki/File:The_Fomer_Asiatic_Petroleum_Building_(6081233096).jpg) · [2021年正立面](https://commons.wikimedia.org/wiki/File:亚细亚大楼正立面2021_(1).jpg) · [2025年东立面](https://commons.wikimedia.org/wiki/File:Asia_Building,_Shanghai_20250501.jpg) · [2019年报道](https://news.sina.com.cn/o/2019-09-07/doc-iicezzrq4104700.shtml)

建筑史资料记载原有内天井。模型依据现状屋面影像，在中央表现低于周围屋面的矩形采光顶。总高约34.85米、采光顶的分格、角亭后部和北、西背墙窗位均为估算。现存入口的临时标识、室内和天井内部不在本次制作范围内。三档几何和十种材质均为原创，未嵌入照片或第三方模型。[参考资料、作者与影像校验值](reference-review.json) · [场地与屋面影像索引](footprint-review.json)

## 编辑与重建

Blender 文件按门廊、柱身、退廊、墙面、窗框、角亭和屋盖等构件分组，以米为单位。Blender 的 X、Y、Z 分别指向东、北、上，原点在该栋冻结建筑面的中心。网页近景保留原始GLB全部三角面。远景减少窗棂、栏杆、石缝和曲线分段，同时保留柱廊、角亭与主要洞口。

在仓库根目录运行以下命令。依赖为 Python、NumPy、Shapely、mapbox-earcut、Node、Blender、gltfpack、ImageMagick 和 Open Image Denoise。

```bash
python projects/shanghai/source/precise/huangpu-asia-building/source/build_model.py \
  --out /tmp/asia-model/assets --audit /tmp/asia-model/audit
```

[单体查看器](../../../asia-building.html) · [资产清单](../../../assets/models/candidates/huangpu-asia-building/manifest.json) · [验证记录](../../../data/audit/asia-building-v1/README.md)
