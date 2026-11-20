# 总巡捕房旧址的福州路历史街面

市房管局第二批优秀历史建筑名录2A030记为「总巡捕房／上海市公安局／福州路185号」。布里斯托大学所藏 Stewart Young 系列 Yo-s23 是一张正对福州路主墙的黑白照片，著录约摄于1933至1939年。该馆记录大楼建于1933年，上海公共租界中央捕房条目另记1933年起建、1935年5月落成。此前1894年启用的是河南路口的另一幢四层楼。2013年12月19日的斜向街照还能辨认正面连续石墙、窄窗与两条较高的竖带。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [Yo-s23 档案卡](https://hpcbristol.net/visual/Yo-s23) · [2013年实照](https://commons.wikimedia.org/wiki/File:The_Central_Police_HQ.JPG) · [逐项来源与校验值](reference-review.json)

模型沿街面宽44.32米，原城市地块临福州路的边长约44.78米。黑白照中，两翼各四列与中央六列向上连续，六排窄窗上方是一层横窗。成对突出石带有半圆形上端凹饰和长条形暗槽，三种不同高度的平女儿墙形成上部轮廓。模型将历史照中的地面层做成封闭浅浮雕。石材分缝、窗格与栏板层次按影像估计，色调以2013年街照为参考。模型向内仅延伸约两米，两侧和背后均以朴素截面收口。[街面坐标和底图对照](footprint-review.json) · [模型页面](../../../central-police-station.html)

档案照片来自布里斯托大学图书馆特藏，Stewart Young 系列，馆方通用授权为 CC BY-NC-ND 4.0。现代街照摄影为 Livelikerw，授权 CC BY-SA 3.0。页面链接原图，模型中的面与材质均为原创。城市地理底图来自 OpenStreetMap contributors（ODbL 1.0）与 Overture Maps Foundation。[馆藏图片使用说明](https://hpcbristol.net/license/what-you-can-and-cannot-do-downloads) · [项目许可证](../../../../../LICENSE)

在项目的 `projects/shanghai` 目录运行下列命令。系统需要 Python、NumPy、Shapely、mapbox-earcut、Node、gltfpack、Blender、ImageMagick 7 及 Open Image Denoise。构建脚本会重开原生工程，并比较原件和真实解码后近远模的有向三角面。

```sh
python source/precise/huangpu-central-police-station/source/build_model.py \
  --out assets/models/candidates/huangpu-central-police-station \
  --audit data/audit/central-police-station-v1 \
  --decoded /tmp/central-station-decoded
```
