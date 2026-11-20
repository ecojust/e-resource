# 德士古大楼（延安东路110号弧形街墙及入口）

上海市房屋管理局第二批2A051的原名栏为“德士古大楼(会德丰大楼)”，公布时使用单位栏载“上海黄浦房地产股份有限公司”。门牌处1994年2月15日的市政府铭牌明确写出先属英商会德丰，后转让给美商德士古石油公司。英文牌记挪威建筑师Hans Berents，1943年竣工。门牌和独立街景中称四川大楼。未查得可核实的产权转让年份。[房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [铭牌原照](https://www.meipian.cn/31sop5rq) · [核对记录](reference-review.json)

Virtual Shanghai的历史照片33256可辨两扇短窗、路口中央高起的女儿墙和延安东路侧连续九组带形窗。照片未明确标注拍摄日期。2015年实照可数四川中路侧十一组大窗，窗下留有较多空调机，延安东路侧局部正在施工。政府铭牌记1986年曾加层，2014年现场记录另载第七层和局部第八层以及2012年12月延安东路一侧的局部坍塌。各年顶层的改变分别保留。[历史照片](https://www.virtualshanghai.net/Photos/Images?ID=33256) · [2014年现场记录](https://blog.sina.com.cn/s/blog_5d1bdf480102ux4c.html) · [2015年四川中路侧](https://commons.wikimedia.org/?curid=38441164)

2020年两面独立照片里，延安东路侧为地面层加四排上窗，四川中路侧和中央为地面层加五排上窗。中间的双门、圆柱和双窗，两侧米黄色釉面砖、窗带周边的白色细边和门旁纵向壁棱都采用原创几何。不同拍摄时期的上层、后屋顶、院面和内部另需图纸。用两列中央窗校定的水平比例只能估计高度，图中的树和车辆留在街景资料中。[2020年东向、南向、近照及铭牌](https://www.meipian.cn/31sop5rq) · [单体页面](../../../texaco-building.html)

门牌为110号的实名地块和固定底图14-13720-6694中1848号的覆盖率为99.22%。按其中连续六条边和弧形街墙的照片推得外立面长约72.2米。市政府公布时的建筑名、今天的通行名与底图所有者相互对应。四川中路北侧另有创业大楼874号，最近边界约5.81米。[实名地块](https://www.openstreetmap.org/way/378107253) · [坐标、近景瓦片与近邻](footprint-review.json)

在上海项目目录中，运行以下命令可生成三个GLB、可编辑的Blender文件和原生文件核验材料。[窗墙制作代码](source/street_front.py)

    python -B source/precise/huangpu-texaco-building/source/build_model.py \
      --out /tmp/texaco-models --audit /tmp/texaco-native --decoded /tmp/texaco-decoded
