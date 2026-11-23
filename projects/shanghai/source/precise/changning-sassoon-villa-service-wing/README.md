# 沙逊别墅辅楼院面与老虎窗

上海市房管局第一批优秀历史建筑名录以1M002登记虹桥路2409号的沙逊别墅。2014年承担辅楼保护修复的上海建为历保记录了公和洋行1928至1932年间的设计与建造过程，指出宅园有供起居的主楼和厨房、配电等后勤用的辅楼。本模型取辅楼面向院子的长立面、左返墙与可见坡屋面。[房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [2014年辅楼保护修复工程](https://www.jianweigroup.com/site/10/category0051/b1216655955211e89cd6408d5c6f7eaa.html)

1937年沙逊自摄影集《Eves》的第15页同时记录主、辅楼。照片左部可辨低翼的三组正面老虎窗、中央浅色山花和门洞、外露深色木架，以及通向高屋的窄连廊。修缮设计单位公布的2014年透视图从另一角度表现同一组构件，能读出窄竖格、曲木、暗门和左返墙上方的小屋窗。模型的色彩和细木格取自该方案，历史照片提供构件位置和明暗对照。各窗所在坡面实际开洞，屋脊与髋线的半圆覆瓦有独立截面。[沙逊摄影原件，DeGolyer Library，Southern Methodist University](https://digitalcollections.smu.edu/digital/collection/vsp/id/52) · [两幅图的坐标读数](measurements/wing-observations.json) · [正面三窗](measurements/front-dormer-controls.json) · [返墙与侧坡](measurements/west-return-observations.json)

院面暂按约14.8米建模，单位长度来自影像与现状屋檐的比对，实际测绘尺寸仍待核。两只摄影机的墙面和屋脊控制点中位偏差分别约2.0和1.4像素。2014年透视图中的色调是修缮方案用色。2016年实地摄影记录显示2409号入口关闭，拍摄者另有多张同园2号、3号楼的照片。主楼花园面、低连廊后部、返墙尽头被挡的屋窗以及室内仍待实测。[现场入口与分栋记录](https://4travel.jp/travelogue/11098400) · [局部配准及误差](measurements/wing-cameras.json) · [纹理读色及原图署名](SOURCES-LICENSE.md)

从项目检出目录运行 `python measurements/check_mesh.py 输出目录` 可重建两档网格并检查各构件闭合性。`python source/wing_finishes.py` 从保存的颜色统计和确定性噪声重新生成砖、瓦的颜色图和法线图。
