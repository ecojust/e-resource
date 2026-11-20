# 汉弥登大楼（江西中路170号街角、入口及塔冠）

上海市房屋管理局第二批2A037记原名“汉弥登大楼”、公布时称“福州大楼”，地址江西中路170号。Virtual Shanghai楼宇547号的英文门牌为170 Kiangse Road，建筑用途为公寓。2021年《新民晚报》记者张钰芸拍摄楼宇外观并走访内部，报道沿用“汉弥尔登大楼”的译名，确认它与对街的都城饭店、建设大厦及原市政府大楼共同围合路口。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [历史楼宇卡](https://www.virtualshanghai.net/Data/Buildings?ID=547) · [新民晚报2021年8月12日原版](https://img1.xinmin.cn/xmwb/2021-08-12/70812.pdf) · [逐项来源与哈希](reference-review.json)

1930年10月16日的施工照片有明确题注，前景正在给汉弥登大楼打桩，后景是施工中的都城饭店。2021年报导记1931—1933年建造，Virtual Shanghai的楼宇记录记1933年，故将当日可见的基础施工与后人记的建造期分别保留。2007年可见凹角及塔部，2013年同框照片能把南北楼分开。2017年能读出南楼入口雨篷上“福州大楼”四字，后有三扇券窗，楼上住宅窗留有百叶、个别窗篷与空调外机，肩部的两孔可透过天空。北楼位于江西中路180号，冠部标识及酒店入口灯饰另有专图。[1930年原图及题注](https://www.virtualshanghai.net/Photos/Images?ID=26765) · [2007年](https://commons.wikimedia.org/?curid=30117507) · [2013年双楼同框](https://commons.wikimedia.org/?curid=30235179) · [2017年福州大楼正面](https://commons.wikimedia.org/?curid=65031174) · [都城饭店独立来源](../huangpu-metropole-hotel/reference-review.json)

固定底图14-13720-6694的1844号和门牌为170号的OSM地块重合98.13%，与北侧358号都城饭店相隔约14.32米。沿转角街墙的六个源顶点拟合凹弧半径约13.96米，地块两端分别贴邻201号和1415号。模型沿弧布置五段立面、中央三券及其下的门道、可见门楣字、窗带、复式肩部开口、塔冠和两端短街墙。相连的两幢长翼、深处的屋面和内部仍须另行调查。[原生归属和贴邻地块](footprint-review.json) · [实名地块](https://www.openstreetmap.org/way/380340010) · [单体页面](../../../hamilton-house.html)

原生底图用十四层推算44.8米。另以2017照片的10毫米焦距、竖幅原图及地图上可定位的转角端点估算，冠顶标高约60.5米。可疑的相机高度、像主点、焦距及端点选择分别取上下界，所得区间约54.9至67.2米。入口、窗位与塔冠据同图的相对比例建模。该估计与实测建筑图纸仍有区别。[估算输入与敏感度](elevation-estimate.json) · [重算程序](source/estimate_elevation.py)

在上海项目目录运行以下命令可输出三个GLB、可编辑Blender模型及验收数据。汉字采用SIL开放字体许可的四字子集表现2017年实照的门楣文字。照片仅作外部参考。[制作代码](source/house.py) · [字体来源](source/fonts/provenance.json) · [字体许可](source/fonts/OFL.txt)

    python -B source/precise/huangpu-hamilton-house/source/build_model.py \
      --out /tmp/hamilton-models --audit /tmp/hamilton-native --decoded /tmp/hamilton-decoded
