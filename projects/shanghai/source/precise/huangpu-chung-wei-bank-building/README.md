# 中汇大楼

上海市房管局第二批名录2A052登记为“中汇大楼”，地址延安东路143号。《上海名建筑志》同时列河南南路16号。中汇银行1934年9月迁入这幢新厦。黄日鲲、赖安吉爱设计，久记营造厂承建。志书记载共十五层，十三层原供职员休息，最上两层用于水塔。上海博物馆1959年至1993年曾使用这栋大楼，改建时填满了中央空间。[第二批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [《上海名建筑志》原文存档](https://web.archive.org/web/20200927112634/http://www.shtong.gov.cn/Newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108942.html)

2015年1月2日的东侧街照可辨河南南路的连续水平窗带、砖红色窗间墙、栏杆和北面退台塔。2024年6月30日从金陵东路看见南侧短立面，以及长边与北塔的相对位置。网页模型里的角度、窗号与材质按现状估绘。2015年照片上的北京银行招牌用于辨识拍摄时期。窗框厚度、后立面、冠顶标高及屋顶设备缺少测绘记录。[2015年原片](https://commons.wikimedia.org/wiki/File:New_Chung_Wei_Bank_Building_Shanghai.JPG) · [2024年原片](https://commons.wikimedia.org/wiki/File:Shanghai,_30_June_2024_(147).jpg) · [影像署名和日期](reference-review.json)

地块使用具名原生记录830和OSM道路数据，长边沿河南南路，塔楼朝延安东路。另址德士古大楼在该地块东北约319米，两栋建筑有不同的底图记录。[地块与邻体](footprint-review.json)

## 修改模型

模型以米为单位。东面窗带、南侧开间、阳台、水塔各级截面和金属桅杆在建模源中独立定义。编辑这些构件后，可在上海项目根目录重建三个GLB和Blender场景。

```sh
python source/precise/huangpu-chung-wei-bank-building/source/build_model.py --out /tmp/chung-wei-model --audit /tmp/chung-wei-audit --decoded /tmp/chung-wei-meshes
```

[几何源](source/chungwei_geometry.py) · [相机](source/preview_camera.py)
