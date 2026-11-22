# 人民路1号中国银行南市办事处旧址东南转角

从小东门面向方浜中路，右侧街角的建筑先后为大昌协记绸缎洋货局、中国银行南市办事处与童涵春堂。上海市第四批优秀历史建筑名录将其登记为4A034。方浜中路南侧的仁记珠宝银楼另属4A035。历史街照中的上层报时钟已消失，2015年和2021年照片里的顶部为一座透空小柱亭。模型取摄于2015至2021年的外观，底层按2021年1月所见的红色封板。[上海市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [文汇报街口今昔对照](https://www.whb.cn/commonDetail/916501) · [历史机位与两栋方位](measurements/historical-camera-order.json)

模型从中央切角沿方浜中路和人民路各延伸一个完整开间。两翼分别可见底层封板、上下层凹窗与前凸弧形铁栏、三角外框包着的圆弧窗冠和阁楼小窗。中央的“童涵春堂”自上而下排列，四字上方为黑底金色圆徽和“1783”。《文汇报》2024年刊登的邢千里照片呈现了摘字后的立面，金字背后有一扇椭圆窗、一扇长方窗、弧形窗冠和下垂花饰。模型给这些构件分别留了真实的窗洞和进深。屋顶八角柱亭保留柱间通透、分段弧顶女儿墙及有影像依据的三尊石饰。[2015年转角原照](https://commons.wikimedia.org/wiki/File:Tonghanchun_pharmacy,_Renmin_Rd,_Shanghai.jpg) · [2024年照片与图注](https://www.whb.cn/commonDetail/916501) · [各来源用途](reference-review.json)

四个独立街景机位给出中央切角宽约3.50米，主檐高约13.56米，柱亭顶约19.37米。顶部后退带来的高度误差约1.3米，切角宽度误差约0.45米。方浜中路和人民路首开间的范围分别约为3.55和3.85米，门窗轴线单独从街景交会。拍不到的屋面深处、两翼其余店面、内部结构及已消失的民国高钟楼仍待调查。[四机位交会](measurements/measured-corner.json) · [首开间窗轴](measurements/first-side-bays.json) · [尺寸与误差](source/dimensions.json)

原始和近景网格各有61,641个三角面，远景有33,933个。16种材料区分金字饰面、铜色倒角、黑色珐琅、暗木、铁栏、玻璃和石材。656个建模构件按196个可编辑组组织。每个金字均有背衬、侧壁和独立表面。玻璃和封板位于各自开口之后，两层栏杆的中心向街面弯出。读入原始网格和两档实际解码网格后，每档都有56条实射，分别检查字腔、“1783”四个数字、两翼窗洞、真实的栏杆弧度和柱亭开口。[三档网格实测](../../../data/audit/nanshi-bank-southeast-corner-v1/preflight/geometry-rays.json) · [转角近景](../../../data/audit/nanshi-bank-southeast-corner-v1/preflight/full-views/small-east-gate-corner.jpg) · [简化档柱亭](../../../data/audit/nanshi-bank-southeast-corner-v1/preflight/lod-views/open-pavilion.jpg)

原建筑建模代码和独立制作的建筑几何使用MIT许可。Legolas1024于2015年2月21日拍摄的原照为铭文描摹底稿。由照片派生的竖向招牌、圆徽及对应装饰采用CC BY-SA 4.0。原图裁切、描摹、线缆遮挡处补接、缩放与立体化的过程均有记录。执行 `python source/extract_relief.py 原片.jpg 输出目录` 可从校验过的800 × 1200像素原片复现两份轮廓文件。模型构建直接使用随源附带的轮廓。[许可与署名](source/relief-license.md) · [轮廓提取程序](source/extract_relief.py) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

在上海项目目录中，通过 `python source/precise/huangpu-nanshi-bank-southeast-corner/source/build_model.py --out 输出目录 --audit 验收目录 --decoded 解码目录` 构建原始、压缩、可编辑文件和预览。工具使用Blender、gltfpack、OIDN与项目的几何检查器。可用 `--blender`、`--gltfpack`、`--oidn` 指定对应可执行文件。[建模入口](source/build_model.py) · [主图落位与地面](../../../data/audit/nanshi-bank-southeast-corner-v1/map-placement.md)
