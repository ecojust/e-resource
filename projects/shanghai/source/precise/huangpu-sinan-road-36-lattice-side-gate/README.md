# 思南路36号边门的错台门柱与几何铁栏

2018 年 7 月 30 日，Antigng 拍下这段沿街围栏。右柱的绿色搪瓷牌写着“36”“思南路”和“边门”。市房管局第五批优秀历史建筑名录第 14 行登记为 5A012、思南路 36 号住宅。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [原始照片](https://commons.wikimedia.org/wiki/File:%E6%80%9D%E5%8D%97%E8%B7%AF36%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg) · [打开模型](../../../sinan-road-36-lattice-side-gate.html)

黑铁栏固定在低墙上。两道横杆之间排着交错的斜杆，四处卷方回纹高低相间，中部栏顶连续折出三个三角形。原照片里的扇形临时告示遮住部分铁条。模型保留告示的外轮廓和包边，铁条按照片可辨的段落建造。两根浅色门柱各有三条纵槽、错台肩部和开缝柱帽。右柱门牌有独立的深绿底釉及浅色漆层。[照片可见铁栏的逐段记录](measurements/iron-panel.json) · [门牌轮廓及笔画留空](measurements/plaque-strokes.json)

铁栏按原照片旋正后的像素配准，以两个柱帽中点和两处深色勒脚的上缘确定正面。两中点名义间距为 2.66 米，柱帽与勒脚名义高差为 2.47 米；门柱厚度、铁件埋入位置和照片边缘截断的底座按估值建造。右柱门牌按自身四角单独校正，汉字保留笔画内的底色。建筑独立展示，位置复核所用的门牌资料可以确认地址，精度尚不足以定位每根门柱。[照片与像素范围](measurements/photographic-reference.json) · [位置复核](measurements/footprint-review.json)

三档网格各通过 98 条射线，覆盖栏杆、回纹、空隙、柱槽和门牌。另从照片取得 43 个浅色笔画点和 9 个绿釉点，原始网格、解码近景和解码远景都逐点命中对应材料。[52 处照片首交记录](measurements/released-address-material-review.json)

## 从源码重建

在本项目的完整工作树中，从本目录执行下列命令。第一、二行分别生成近、远景网格，第三行从近景原件检查纹理，第四行从原始照片重新测量门牌。

```sh
python source/build_model.py --output sinan-full.glb
python source/build_model.py --lod --output sinan-low.glb
python source/build_blender_source.py --check-raw sinan-full.glb
python measurements/trace-address.py original-photo.jpg rebuilt-plaque.json
```

[门柱与低墙](source/piers.py) · [铁栏](source/iron_panel.py) · [搪瓷门牌](source/address_plaque.py) · [七个视点](source/cameras.json) · [来源与许可](SOURCES-LICENSE.md)
