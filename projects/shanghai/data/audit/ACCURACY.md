# 上海16区地理与地标精度审计

核验日期：2026-10-25。核验对象为公开资料、坐标系统、行政区几何和地标尺寸。本报告不把地图数据的一致性当作实地测量精度，也不证明每栋建筑的高度或立面正确。

## 核验结果

- **16个区全部存在，16个多边形全部有效。45个检查点全部落在预期区内，每区2–4个点。**检查点包括16个道路起点，以及来自Wikipedia或OSM的独立命名地点。后者与OSM边界并非全都独立来源。
- 覆盖检查包含崇明岛、长兴岛、横沙岛、浦东机场、滴水湖/临港、金山枫泾、青浦淀山湖/朱家角、松江佘山、嘉定安亭等。点通过不等于整片区域每栋建筑都已建模，模型完整性由全域提取manifest另外统计。
- 坐标使用WGS84经纬度；距离使用WGS84椭球，面积使用UTM51N（EPSG:32651）。未将GCJ-02、百度坐标直接混入。
- 排除了3个不适合作为内部检查点的次级来源点：杨浦大桥中点落浦东侧、上海交通大学百科坐标指徐汇校区而非闵行校区、吴淞百科概略坐标落河中浦东边界内。拒绝记录完整保留。

## 边界与面积

[上海市政府地理介绍](https://english.shanghai.gov.cn/en-Overview/20231209/705180b43f794c1ca43f4d1ddaa049a2.html)给出东经120°51′–122°12′、北纬30°40′–31°53′、面积6,340.5平方公里和16个区。项目展示框[120.8,30.6,122.25,31.95]包含这一经纬范围。

现有OSM展示边界并集面积约11,994.93平方公里，**不能称作上海陆地或已建成建筑的覆盖面积**。它包含河口、海域及行政水域；官网常用陆地/统计面积口径，两者不应强行对齐。完整原始OSM关系另存，展示版本移除了焦点框以外的远方离散成员；不能据此声称这些成员是行政错误。

|区|官网面积 km²|OSM展示多边形 km²|差异 %|
|---|---:|---:|---:|
|[黄浦区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231212/6f71628f86d945d8a67760f04b19ef4e.html)|20.52|20.55|+0.17|
|[徐汇区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20261010/33acf7ac30b846f78f729f8770599d62.html)|54.93|55.19|+0.48|
|[长宁区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231212/6965b32407ac4fa1890b043b7b949b7e.html)|37.18|37.16|-0.05|
|[静安区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231212/ca64242370a848ac9f0b0dbb73e096ad.html)|37|36.74|-0.70|
|[普陀区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20260920/f242ded342494a3c8a8bd70607765c9f.html)|55.53|55.81|+0.50|
|[虹口区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231216/b1d529f3e8694b03b846e92448064b5f.html)|23.48|23.37|-0.49|
|[杨浦区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20261015/019c8985f20c4556a421b55022bece88.html)|60.61|60.51|-0.17|
|[闵行区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231216/5552bf8628204eccbacafd610e49cc9a.html)|373|372.50|-0.14|
|[宝山区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231212/e46f2404cb2348749c3e5fb476ab5b5d.html)|300.6|366.80|+22.02|
|[嘉定区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20260929/19b60ce28b324feeb5ac15a39ac4ddfa.html)|463.16|462.68|-0.10|
|[浦东新区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231212/3276816dc2c046baa809770587694d72.html)|1210|3146.14|+160.01|
|[金山区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231216/c7a641be2de34119a801913d4a40d710.html)|613|757.68|+23.60|
|[松江区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231216/a024f6cbcbac4cc98570c3bca0e7beb1.html)|604|604.29|+0.05|
|[青浦区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231216/d8c39f2103aa4bed9e73627608ed1885.html)|668.54|669.03|+0.07|
|[奉贤区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231216/d7ba9f8f024b43f8aa4250689b2b377c.html)|733.38|1195.33|+62.99|
|[崇明区](https://english.shanghai.gov.cn/en-AdministrativeDistricts/20231216/43ae181c16834a7ba2f49d001463efc8.html)|1413|4131.16|+192.37|

较小内城区差异通常在1%内，但这只能说明面积量级相符。宝山、浦东、金山、奉贤、崇明的水域口径差异明显。金山官网特别区分陆地613平方公里与海域445平方公里。官方区页各自发布日期不一，比较不是同一时刻的边界法律认证。

## 地标高度及尺寸

|地标|采用参考高度|已读取的可靠来源|
|---|---:|---|
|上海中心大厦|632 m|[CVU/CTBUH Skyscraper Center](https://www.skyscrapercenter.com/building/shanghai-tower/56)，architectural height|
|东方明珠|468 m|[运营方东方明珠集团](https://www.opg.cn/)，正文“高468米”|
|上海环球金融中心|492 m|[开发商森大厦项目页](https://www.mori.co.jp/en/projects/swfc/)，101层、492米|
|金茂大厦|420.5 m|[CVU/CTBUH Skyscraper Center](https://www.skyscrapercenter.com/building/jin-mao-tower/189)，architectural height|
|上海海关大楼|79.2 m|[上海海关官网原文的2010年存档](https://web.archive.org/web/20100610110157/http://shanghai.customs.gov.cn/publish/portal27/tab8419/module26899/info82241.htm)，含钟楼总高|

**审计实际发现并已修正的尺寸：**金茂旧模型420 m与公开420.5 m不符；海关旧模型90 m引用了英文百科，而上海海关原文明确总高79.2 m、主楼36.2 m、钟楼约43 m。海关官方原文还给出钟面直径5.4 m、分针总长3.17 m、时针总长2.3 m；旧模型钟面直径10.32 m过大。分针总长可能包含平衡端，不应把3.17 m全部当作半径2.7 m钟盘内的指示端。

官网现行旧链接返回412/503；Internet Archive保留的官方原文成功获取。英文百科90 m的冲突值记录在customs-height-conflict.json，不能将其当成第二份确认。原文中的20世纪20年代经纬度没有现代WGS84基准说明，未用于移动模型。

### 主立面比例的照片复核

海关官网配图为铜钟，不能用于外立面比例。另读取[Diomidis Spinellis 2006年正立面照片](https://commons.wikimedia.org/wiki/File:ShanghaiBundCustomsHouse.jpg)（作者提供CC BY 2.5许可选项），钟盘影像直径约92像素、所在塔墙约140像素，比例约0.66。以官方5.4米钟盘粗略换算，所在塔墙约8.2米，下方三条窗塔段约10.6米；这些数值受拍摄透视影响，只用于纠正原24米塔段的明显比例问题，不能称作立面测量。主楼立面粗略比例约44米宽。

现取OSM周边，命名上海海关way178407318为前部的一块建筑轮廓，其最小旋转矩形约36.34×23.42米；后翼与周围建筑分成多个对象，不能将这一对象当作整栋海关的完整 footprint。最终海关模型已改为该前楼轮廓和质心，朝向烘入模型；后翼由全域模型补充。塔层宽8.2/10.6米属于照片比例推定，其他立面细节仍是概括表达。相关脚印保存于customs-osm-footprints.geojson。

### 位置复核

|地标|OSM锚点与百科标志点间距|解释|
|---|---:|---|
|上海中心大厦|28.5 m|建筑包围盒中心与社区标志点口径不同；不是实测误差|
|东方明珠电视塔|52.3 m|建筑包围盒中心与社区标志点口径不同；不是实测误差|
|上海环球金融中心|26.9 m|建筑包围盒中心与社区标志点口径不同；不是实测误差|
|金茂大厦|4.3 m|建筑包围盒中心与社区标志点口径不同；不是实测误差|

模型继续使用OSM建筑锚点与真实地图对齐。上述几十米差异意味着不能宣称位置达到亚米级；需要建筑主塔中心或测量控制点才能进一步消除锚点不确定性。此处不因百科点粗糙就自动把模型平移。

## 可重复检查

数据文件：checkpoints.geojson（点和逐点来源）、report.json（面积/包含关系/高度依据）、official-sources.json（16区政府页面）、poi-sources.json与poi-fixes.json（候选与查询结果）、height-sources.json与customs-height-conflict.json（实际获取结果）。

```sh
python -m pip install shapely pyproj
python data/audit/build_audit.py --project .
```

脚本检查边界有效性、至少2个区级检查点、全部点的归属，并记录边界SHA256。高度参考值与当前元数据的比较随每次运行更新；GLB真实几何高度需另由模型导出/验证脚本检查。

## 仍然不能从本报告推出的结论

- 未逐栋对照实地照片、竣工图或LiDAR；真实轮廓也可能有缺失、影像提取误差和年代差异。
- 基于遥感栅格补充的高度仍是统计估计，尤其高层、临水、树冠和小建筑区域不能视为实测单栋高度。
- MVT边界量化、瓦片裁切和合并误差应在全域提取元数据中保留。
- 桥梁桥面高度、道路立交、地形、建筑内饰与立面细部属于其他验证层次。行政区覆盖和点归属通过并不验证这些细节。

OSM派生点与边界遵循ODbL-1.0，Wikipedia来源链接逐点保留；政府和开发商页面仅引用用于核验的事实与短摘录，不重新许可其网页内容。
