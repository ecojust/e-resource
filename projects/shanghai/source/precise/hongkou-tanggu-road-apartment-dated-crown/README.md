# 公安大楼塘沽路年份匾与双塔楼冠

上海市第五批优秀历史建筑名录第 5F002 项登记为“上海市警察局虹口分局”，现名“公安大楼”，地址为虹口区塘沽路 219 号。本件展品从最高一排四扇窗的窗台下方起，向上做到两侧灰色檐帽。2015 年人民网报道将公寓建造时间记为 1937 年。楼冠匾上可直接读出“1912—1936”，这里按画面保留文字。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [2015 年报道](https://sdqy.dzwww.com/jdtp/201510/t20151030_13263603.htm)

## 构件与展示比例

每座塔冠的前部折作三面，两条浅色竖肋沿折角上升，橙褐色墙面上接深灰色压边。两塔之间的浅色端柱帽刻有竖槽。四窗各有独立窗台和上方的浅凹板。右边两窗可辨四列六行窗格，左边两扇挑篷分别做出弧面、端面和浅色波边。年份匾的笔画、三个字孔和四处截角均由独立网格构成。[塔冠专题图](../../../data/audit/tanggu-road-apartment-dated-crown-v1/folded-towers/crown-profile.jpg) · [窗格专题图](../../../data/audit/tanggu-road-apartment-dated-crown-v1/window-sashes/crown-window-details.jpg) · [年份匾专题图](../../../data/audit/tanggu-road-apartment-dated-crown-v1/dated-cartouche/dated-cartouche.jpg)

公开资料未提供本栋的实测尺寸。本展品以年份匾全宽为比例基准，glTF 和 Blender 里该宽度取 4 个展示单位。两侧折面的进退、墙厚、檐口背缘、布篷出挑和背后遮住的窗框上段为展示估计。最高窗带下缘和两塔背缘均为展品剖切面。年代牌的文字可见，具体纪念事件仍待文献说明。[构件比例](measurements/crown-layout.json) · [双照匾文描读](measurements/dated-cartouche-tracings.json) · [图像出处与年代考证](measurements/crown-photographic-sources.json) · [照片来源与许可](SOURCES-LICENSE.md)

## 重建与检验

在包含上海项目依赖的仓库内执行以下命令，可重新生成两档 GLB。完整打包入口同时提供公共 Blender 工程、独立几何检查与渲染。

```sh
mkdir -p output
python source/build_model.py --output output/tanggu-crown.glb
python source/build_model.py --lod --output output/tanggu-crown-lod.glb
python source/build_model.py --out output/tanggu-delivery --audit output/tanggu-audit
```

原始模型和网页近景各有 6,260 个三角面，远景有 5,032 个。近远各自保留 102 个具名构件。三个文件分别检查了塔体及端柱的 111 个表面位置、窗与凹板的 164 处细节，以及匾额的 93 处笔画、字孔和边缘。两档的程序纹理和纹理坐标均从解码文件重新读取。[模型页](../../../tanggu-road-apartment-dated-crown.html)
