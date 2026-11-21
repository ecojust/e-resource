# 东平路5号花园住宅南敞廊

徐汇区东平路5号花园住宅约始建于1918年，1924年在主楼东侧增建桌球室。上海市第四批优秀历史建筑登记表编号4D015，现用名为上海音乐学院附小图书馆。本次制作花园一面的两层敞廊。左、右两座底层大拱设白色栏杆，中央一拱后退，由红色台阶登上廊面。上层以四根细圆柱承托五连拱，栏头、栏脚和宝瓶状的栏杆柱均可斜看。[市级登记表](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [南、北两面照片与历史图纸](https://www.thepaper.cn/newsDetail_forward_21629034)

南立面原照宽950、高609像素。敞廊前的圆花铺地图案也出现在两幅俯视影像中。在原照的三排花砖上量取14个圆心，用顶视图中约1.66米的花心间距换算，得到敞廊宽度约9.9至10.8米，模型采用10.30米。中央台阶底边约2.64米，上层栏杆高约0.85米。照片中的台阶遮住一段墙脚，敞廊进深和背面仍为估计。[照片坐标与几何参数](measurements/south-elevation-ratios.json) · [花砖标定、两组正射与误差](measurements/courtyard-paving.json)

通用地图的5号门牌点落在东平路北侧约75米。与南立面照片相符的铺地在路南，位于带独立门牌的沿街小楼后方。两处沿街建筑和朝花园的敞廊分别核过。[街道与四个旧轮廓对照](measurements/courtyard-paving.json)

浅灰外墙、白栏杆和深色落水斗取自南面照片。坡檐建至可辨的红瓦前坡和老虎窗；其余翼楼、东侧桌球室、后侧屋面及室内仍待制作。花园住宅的两层敞廊与2015年照片所示的沿街立面分别记录。[资料对读及照片哈希](reference-review.json) · [版权与再分发](SOURCES-LICENSE.md)

从较暗的门廊照片中还能辨认出后排的墙柱、过梁和门窗暗面。模型按照片分别处理上下层的暗面宽度，两道墙面的间距暂取2.15米。门扇的分格及开启方式仍待室内资料补证。[背光部位的照片读数](measurements/rear-gallery-readings.json)

从仓库根目录构建原始、网页、远景和可编辑模型。

```sh
python projects/shanghai/source/precise/xuhui-dongping-five-south-arcade/source/build_model.py \
  --out out/dongping-arcade/assets --audit out/dongping-arcade/audit
```

[南敞廊正面](study-views/south-elevation.jpg) · [中央台阶和后排门洞](study-views/lower-passage.jpg) · [上层栏杆局部](study-views/balusters.jpg)
