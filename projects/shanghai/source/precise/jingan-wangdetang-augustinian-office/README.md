# 望德堂院内门廊与曲线山墙

北京西路1220弄2号的西侧短墙有一处高拱，院内石阶伸入门廊。底层窗上可见弧边尖顶窗帽，楼上有挑出的铁栏阳台。门廊上方的小山墙和朝向南侧街面的较宽山墙均开圆窗。转角的后退露台、上部小阳台和侧墙双拱窗前的阳台分别建模。金属遮篷、晒衣和管线随住户变化，模型只概化了可辨的外廊罩棚，后部墙体和室内另列。[打开模型](../../../wangdetang.html) · [2017年院内照片](https://commons.wikimedia.org/wiki/File:望德堂.jpg) · [2016年实照](https://blog.sina.com.cn/s/blog_a598306e0102wr1h.html)

上海市房屋管理局第二批优秀历史建筑登记表以2B023列“望德堂”，使用栏为“住宅”，门牌为北京西路1220弄2号。《上海宗教志》“奥斯定会办事处”记北京西路1220号，又名望德堂。方志所记1894年是该会在沪设立办事处的年份。2016年图文记这一处住宅1930年始建、1932年建成，另载1955年和1990年的产权变化，后两项尚待独立档案复核。宗教志紧接着另列香山路6号的重整奥斯定会办事处。模型只呈现可辨认的院内入口，原账房和小祈祷室的准确位置仍待查。[市级名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [上海宗教志存档](https://web.archive.org/web/20131219141831id_/http://www.shtong.gov.cn/newsite/node2/node2245/node75195/node75203/node75283/node75297/userobject1ai91966.html) · [照片及资料记录](reference-review.json)

北京新村2号楼的独立点位在冻结地块786内部5.69米。2017年照片的原图定位精确到整角秒，可作为院内近照的辅助，无法单独确定镜头方向。2021年2月北京西路两处带坐标全景均显示，朝街长面的西端有一组圆窗山墙及三扇小拱，往东续为成排上下窗列。2016与2017年照片中的深圆拱、石阶和小挑台位于相邻的西入口面。2025年公开视频题名记“正门面西”。入口短面沿地块约12.55米。南侧长边约20.77米，模型只表现具有照片依据的西段，山墙、门窗与檐口的高度按照片比例估算。后立面、内部布局、北京新村其余各门牌以及相邻的两栋原楼继续保留。[地块及航片](site-and-roof.json) · [冻结城市原体](footprint-review.json)

## 重建

从上海项目目录运行。环境需要Python、NumPy、Shapely 2.1、Blender、gltfpack、Open Image Denoise及项目的Node依赖。

```sh
python -B source/precise/jingan-wangdetang-augustinian-office/source/build_model.py \
  --out assets/models/candidates/jingan-wangdetang-augustinian-office \
  --audit data/audit/wangdetang-v1 --decoded /tmp/wangdetang-decoded
```

[可编辑几何源码](source/frontage.py) · [四种文件](../../../assets/models/candidates/jingan-wangdetang-augustinian-office/manifest.json) · [独立检验](../../../data/audit/wangdetang-v1/README.md)
