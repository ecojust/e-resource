# 黄浦剧场北京东路圆角入口与通高玻璃窗

北京东路780号的金城大戏院由华盖建筑师事务所设计，于1934年2月1日开幕。此模型取2016年大修后的转角门脸。日间资料采用黄浦区融媒体刊载的正面照片，雨篷上的院名与2016年11月夜景互证。[第四批优秀历史建筑登记表](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [上海城建档案](https://www.thepaper.cn/newsDetail_forward_8742228) · [黄浦区融媒体](https://news.qq.com/rain/a/20241213A08N8100) · [2016年修缮后夜景](https://www.kankanews.com/detail/kDwmzDomO2l)

## 建筑范围

五道深窗带围成弧形，四根浅色圆柱贯通上下。近景保留两扇向外支起的窗、窗后方折护栏、横排院名的字边和雨篷前沿英文。两扇打开的折门后可见首段楼梯。两侧有独立海报框，近景用几何色块表示会更换的节目。本项止于贵州路和北京东路两侧相接的第一段墙。剧场其余街翼、完整的观众厅、舞台及后部屋面留待后续。

1934年的两张门脸照片分别出现《人生》和《渔光曲》片名。2016年2月照片上的四字院名位于高窗上方。同年11月资料及区融媒体照片上的院名站在挑檐上。竖牌和雨篷采用同一修缮后时期。[开幕照片](https://imagepphcloud.thepaper.cn/pph/image/83/330/751.jpg) · [《渔光曲》时期照片](https://imagepphcloud.thepaper.cn/pph/image/83/330/753.jpg) · [2016年2月实拍](https://commons.wikimedia.org/wiki/File:Huangpu_Theatre_Shanghai.JPG)

## 尺寸和估计

2021年街面五个拍摄位置给出高窗边缘、立柱、平直门线、雨篷肩部和上墙两端的位置。从北京东路向贵州路，四柱之间约1.26、1.32、1.36米。五窗上缘约14.8米，下缘约4.2米。街角底座弧半径约9.26米，凹窗弧半径约5.42米。门口两端相距约5.40米。外墙粉刷线和窗檐的深度、可见台阶的级数与内侧玻璃门按照片比例建模。[窗柱交会](measurements/axes.json) · [门、檐、顶标高](measurements/components.json)

北京东路上层浅黄墙止于实测两种墙色的交界。以这一竖线为灯箱内沿，把照片上十道横格的左右端成对回投，得牌面向街伸出约1.13米。采用不同标高与墙边得1.11–1.18米。绝对平面位置对单一街景机位的误差可达约1.6米。可见的最下缘约4.69米，受路口信号灯遮住的板底取3.93米。箱体厚度0.22米为估计。安装件、墙后构造和舞台空间没有足够照片。[挂接处街景](measurements/east-wall-verticals.json) · [十道横格回投](measurements/sign-attachment.json)

## 可编辑源码与许可

从本目录内执行以下命令可重建原始、近远网页模型、Blender 文件和检查报告。使用项目共用的封装脚本、Blender、gltfpack、Node 以及 Python 的 NumPy、Shapely、Pillow 和 fontTools。

```sh
python -B source/build_model.py --out builds/models --audit builds/audit --decoded builds/decoded
```

字体子集采用霞鹜文楷 TC 和 Work Sans，以院名的实际汉字与英文进行替代刻字。两套字体遵循 SIL OFL 1.1。模型、程序和矿物粉刷纹理为本项目原创。历史报道、街景和原照片只作核对资料。地图数据标注 © OpenStreetMap contributors，遵循 ODbL 1.0。[文件及来源](reference-review.json) · [霞鹜文楷许可](source/calligraphy-OFL.txt) · [Work Sans 许可](source/canopy-OFL.txt) · [OSM来源](https://www.openstreetmap.org/way/414733191/history/4)
