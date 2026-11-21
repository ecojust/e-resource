# 吴同文住宅（绿房子）

铜仁路333号在市房管局第二批保护名录中登记为2B015，原名称为“花园住宅”，使用单位为“市规划院”。邬达克为吴同文设计的四层住宅位于铜仁路西、北京西路南的地块北部。[市级名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) [区位及照片收据](reference-review.json)

《上海住宅建设志》记宅于1934—1937年建造，占地2213.33平方米，建筑面积1731.75平方米。《静安区志》把哈同路333号住宅建成列入1937年。修复项目采访采用1938年这一建造年份。两种记载分别保留。2009年修复团队开始研究，2012年底进场，主要修缮工程完成于2013年，2014年6月14日修后首次对公众开放。[上海住宅建设志](https://web.archive.org/web/20160627194310id_/http://www.shtong.gov.cn/Newsite/node2/node2245/node75091/node75095/node75115/node75127/userobject1ai90866.html) [静安区志](https://web.archive.org/web/20191127200419id_/http://www.shtong.gov.cn/newsite/node2/node4/node2249/node4412/node17428/index.html) [2014年6月15日修复团队采访](https://www.thepaper.cn/newsDetail_forward_1250899)

## 形体与取样

模型依据四层平面、园侧和街侧立面线图，对照2013年4月刊出的修缮前后现场资料及Fayhoo在2016年4月4日拍摄的花园全景。西南侧红色面层弧梯通到二层露台，东南圆端有三层连续弧窗。中央各层露台边界不同，最高一层的弧形雨檐向西收窄。沿北京西路的北侧有一座通高弧形楼梯窗。底层平面中南北两排房间之间的车道可贯通。[高参88现场调查与图纸](https://web.archive.org/web/20160305025742id_/http://blog.sina.com.cn/s/blog_5d1bdf480101bwv8.html) [Fayhoo花园原照，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Residence_of_D._V._Wood.JPG)

按相邻两层的圆窗中心与北梯间轴线，将图纸归至统一平面。航片上西翼屋顶端、东南圆端及北梯间三个控制点的平面残差依次约为0.43、0.47、1.00米。保留单栋主楼的外廓，南侧独立楼栋、门房、车库和园墙、室内陈设另列待核。贴面砖缝为按建筑尺度简化的原创几何，单块釉色及树冠遮住的窗格没有逐块实测。[底图、航片、坐标与误差](footprint-review.json)

## 地图与文件

模型在14-13719-6694内替换简化楼栋436。该楼栋与现有具名OSM环835065787重合约95.31%，原面积约185平方米，漏掉西翼、东南圆端和花园露台。原址按图纸和航片校准，锚点为121.44441344，31.22965980，图纸横轴方位68.5度。地面阻挡按底层两排实际房间生成，车道、花园和外梯保有各自边界。[主地图](../../../index.html#landmark=jingan-woo-tongwen-green-house&mode=overview) [独立模型与四个下载文件](../../../woo-green-house.html) [核验报告](../../../data/audit/woo-green-house-v1/README.md)

近景 51,536 个三角面，远景 22,612 个三角面。Blender工程可编辑，另有原始GLB和压缩的两档GLB。所有几何为原创，随项目采用MIT许可。参考照片及航片著作权归各自作者或供应商；模型中没有嵌入照片。[下载清单](../../../assets/models/candidates/jingan-woo-tongwen-green-house/manifest.json) [项目许可](../../../../../LICENSE)

## 重建

自项目根目录运行下列命令。需要Python、NumPy、Shapely 2.1、Blender、Node.js、gltfpack、ImageMagick 7和Open Image Denoise。下例假定相应程序已经在PATH中。

```sh
python -B projects/shanghai/source/precise/jingan-woo-tongwen-green-house/source/build_model.py \
  --out /tmp/woo-assets --audit /tmp/woo-audit --decoded /tmp/woo-decoded
python -B projects/shanghai/source/precise/jingan-woo-tongwen-green-house/source/check_surfaces.py \
  --manifest /tmp/woo-assets/manifest.json --out /tmp/woo-audit/surfaces.json
```
