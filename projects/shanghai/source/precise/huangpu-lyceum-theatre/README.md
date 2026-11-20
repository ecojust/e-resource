# 兰心大戏院

上海市房屋管理局第二批名录将茂名南路57号登记为兰心大戏院，编号2C006。建模范围是1931年在茂名南路和长乐路路口建成的剧场。此前虎丘路的剧院、茂名南路58号法国总会和相邻的兰馨公寓另有地址或独立的建筑轮廓。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [《上海名建筑志》原文存档](https://web.archive.org/web/20190415081402/http://www.shtong.gov.cn/newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108967.html)

三层主入口面向西南。二层的三扇半圆券窗设券框、拱顶石和小石栏；三层由方窗、突出阳台和成对托臂组成。深色雨篷、金色中文招牌、褐色面砖与交错假石墙角按2012年和2019年的实照制作。2020年修缮报道中的效果图提供了两侧低翼的信息。门顶与两侧的英文招牌只在该效果图中得到辨认，模型采用实照中的中文招牌。[2012年实照](https://commons.wikimedia.org/wiki/File:Lyceum_Theatre.jpg) · [2019年实照](https://commons.wikimedia.org/wiki/File:Lyceum_Theatre,_Shanghai_(20191114165625).jpg) · [修缮报道及效果图](https://www.sohu.com/a/410184037_260616)

现行Esri影像和2021年档案影像可辨认门厅后的蓝灰拱形上盖及一座与它横向相交的矩形后台高屋，2018、2024年档案影像及Bing影像可辅助确认。树荫和楼顶影像位移影响背墙位置。模型依据实际地面轮廓约束屋身与东邻，屋顶标高、隐藏设备、部分侧窗、背面和门头字体为估计。内部观众厅和舞台设备未建模，参考照片未嵌入成品。[实物与年代](reference-review.json) · [实际地块与影像收据](footprint-review.json)

~~~bash
cd projects/shanghai
python -B source/precise/huangpu-lyceum-theatre/source/build_model.py --out /tmp/lyceum-theatre --audit /tmp/lyceum-audit
~~~
