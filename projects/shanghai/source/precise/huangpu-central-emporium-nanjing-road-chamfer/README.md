# 中央商场折角入口、扇灯与三层街窗

上海市第五批优秀历史建筑名录将中央商场列在四川中路355号。2022年照片拍到了东北折角的同一入口，右柱上保留“123 南京东路”小铜牌。门下左半是带竖梃的玻璃，两旁可见的直边给出了框位；右半为开启的通道，模型将室内较深处表示为暗面。半圆扇灯中的六道钢件分隔八块玻璃，门额上嵌“中央商場”四个铜字。上方三层各有三扇面向街角的窗，石檐从正面转入两侧短翼。2019年的同址照片可供核对上层窗位和檐口。[两期照片与署名](measurements/photographic-reference.json) · [两处门牌及城市轮廓](measurements/footprint-review.json)

铜字分件保留可辨的孔眼。放射状券石的凹槽朝向按原照片刻画。右柱小牌上两颗铆钉、三个数字及街名字样各以独立实体表达，小字在照片中有局部粘连。[扇灯钢件与玻璃](measurements/2022-fanlight-members.json) · [铜字轮廓](measurements/2022-raised-sign.json) · [南京东路123号门牌](measurements/nanjing-123-plaque.json)

两段转角外墙的GIS边长合计约10.46米。根据扇灯占街角的比例，模型采用3.72米名义直径。入口凹进、墙厚、两翼短段和石檐出挑按照片估计。入内的店堂和离开折角后的街面超出研究范围。2019和2022的商号牌面已有变化，此处按2022年铭文字形绘制。[两期照片的固定参照点与上层窗位](measurements/2019-upper-frontage.json)

## 从源码重建

从项目完整工作树的本目录运行以下命令。

```sh
python source/paint.py
python source/build_model.py --output emporium-full.glb
python source/build_model.py --lod --output emporium-low.glb
python source/build_blender_source.py --check-raw emporium-full.glb
```

[折角墙面及两翼](source/market_front.py) · [扇灯与铜字](source/corner_fanlight.py) · [放射券石](source/fluted_archivolt.py) · [门牌](source/street_number.py) · [七个机位](source/cameras.json) · [来源与许可](SOURCES-LICENSE.md)
