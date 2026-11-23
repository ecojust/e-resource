# 中西女中东楼（五一楼）院落立面

上海市房屋管理局第二批优秀历史建筑表将中西女中列为2M008，地址为江苏路155号东楼、北楼。校方1916至1917年报记载，1916年6月27日付清新址购款，同年秋季高年级在原有的二十五室住宅开课。校长Martha E. Pyle在1922至1923年报记载，寄宿部于1922年9月12日迁入新建的Lambuth-Clopton Hall。Jennifer Bond的访校照片将这栋宿舍辨认为今五一楼，上海市文旅推广网称它为1922年所建的东楼海涵堂。Social Hall（社交堂）为另见于中文校史的旧称。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [1916至1917年报第196页](https://archive.org/details/seventhannualrep01meth/page/196/mode/1up) · [1922至1923年报第305页](https://archive.org/details/thirteenthannual1923meth/page/305/mode/1up) · [访校照片与楼名辨识](../changning-mctyeire-richardson-hall/measurements/east-building-dates.json) · [校史采访](https://www.thepaper.cn/newsDetail_forward_1494412) · [原有来源逐项记录](reference-review.json)

Ctny于2017年拍摄了五一楼的庭院正面与全景。两张照片均显示院面中央有一座浅色山墙，拱形正门上方为菱形带饰，两侧底层为铅条菱窗。左右各六孔拱廊，上有两排双窗及四扇老虎窗。模型以这组影像重建约70.7米的院面。此版在同一模型上接续制作了东南翼朝草坪的一面。院廊主体的首版原始GLB可按原发布哈希复建。[庭院照片](https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-One_lecture_hall.jpg) · [庭院全景](https://commons.wikimedia.org/wiki/File:Shanghai_No._3_Girls%27_High_School,_Five-One_lecture_hall_panorama.jpg) · [轮廓与航片](footprint-review.json)

局部X轴沿正面朝东南，Y轴朝楼内东北方向，Z轴向上。地块确定了约20.3米宽的中央突出段、两端接缝及其方向。檐高、门廊深度、瓦面、窗棂和石料颜色根据照片估计。两层窗框、铅条、拱券后壁、短侧墙、老虎窗与山墙盖石均为独立几何，外部照片只作对照。

## 东南草坪返翼

2017年8月21日，Ctny 在16时37分拍到院内转角，16时44分的全景又收录了靠草坪的六个窗轴。另一个机位拍到四个窗轴，前廊、云和树荫的投位都可区分。两排楼层各有六处窗洞。底层可确认五处，最靠院角的一处受到券廊和花木遮挡。修订模型有17处贯通墙厚的开口、两根落水管与带红瓦帽的小屋顶窗。第六个屋顶窗只做到树冠挡住的位置。[独立草坪侧照](https://www.historic-shanghai.com/mctyeire-school-for-chinas-daughters/) · [第三站原像素手读](measurements/historic-lawn-window-readings.json)

同址源地块2885和具名轮廓分别给出约29.48和29.52米长的返翼内墙，临草坪的墙位相差约0.19米。照片足以建模约26米，远端树后的实形与翼后房间保留在原有资料范围。全景局部的沿墙长度估计在树缘约有2.3米误差。墙面色差和玻璃透光按照片估计，两种可平铺的色图和法线均以程序生成。[窗框坐标与独立误差](measurements/lawn-return-observations.json) · [三幅原像的局部取景](measurements/lawn-return-stations.json) · [材质颜色测读](measurements/return-finish-readings.json)

三张照片均显示，返翼大屋面的脊线高于早期模型。按两侧外墙相距约15.3米、屋脊取中这一条件，三图各自反算的脊高约22.3–22.4米。第三幅照片还能辨出四个老虎窗的侧颊、挑出窗身的瓦帽和帽下暗色封檐。合模把第一樘老虎窗移到两张草坪照片共同指示的院角位置。[三站屋脊读数](measurements/lawn-roof-parameters.json) · [瓦帽与侧颊的独立原像点](measurements/historic-lawn-roof-readings.json)

在自含源码包中，从解压根目录运行以下命令。近、远两版都使用原有模型ID与坐标。生成时使用Python、NumPy、SciPy、Shapely和Pillow，网页编码和原生文件分别使用 gltfpack 和 Blender。

~~~sh
src=projects/shanghai/source/precise/changning-mctyeire-east-building/source
python "$src/build_model.py" --output rebuilt/whole/full-source.glb
python "$src/build_model.py" --output rebuilt/whole/lod-source.glb --lod
python "$src/package_model.py" rebuilt/whole rebuilt/packaged --gltfpack gltfpack
python "$src/package_editable.py" prepare rebuilt/packaged rebuilt/native
python "$src/package_editable.py" run rebuilt/packaged rebuilt/native
python "$src/package_exchange.py" rebuilt/packaged rebuilt/exchange
~~~

[打开五一楼独立模型](../../../mctyeire-east-building.html) · [返翼及原院立面的八项文件](../../../assets/models/candidates/changning-mctyeire-east-building/lawn-return/manifest.json) · [城市院面原有四项文件](../../../assets/models/candidates/changning-mctyeire-east-building/manifest.json)

两档新返翼各有251.54平方米的实体投影与原城市模型保留的2885号建筑相叠。城市继续调用原院面与原有裁切，五一楼独立页展示补入的返翼。[原城市模型与返翼逐面检查](measurements/retained-2885-mesh-test.json) · [2018年与2025年两期屋顶](measurements/two-roof-dates.json)
