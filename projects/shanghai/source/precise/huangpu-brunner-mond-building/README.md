# 卜内门大楼（四川中路五开间东立面）

卜内门大楼位于四川中路133号，福州路与广东路之间的路西。上海市房屋管理局将其列入第二批优秀历史建筑，编号2A047，登记“卜内门大楼／上海时运物业集团、上海市新华书店”。市地方志记载1921年7月动工、1922年底建成七层。实地名称还有储运大楼、上海新华发行集团楼。现状OSM在同一轮廓内保留门牌、原名及历史建筑编号。[房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [《上海名建筑志》](https://web.archive.org/web/20200927103158id_/http://www.shtong.gov.cn/Newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108959.html) · [杨浦区图书馆藏图文](https://web.archive.org/web/20140505130248id_/http://www.yplib.org.cn/structure/jdsh/bnsz/dg_74826_1.htm) · [现状轮廓](https://www.openstreetmap.org/way/380339845)

Donnelly家族收藏照片的题注标明133 Szechuen Road、拍摄日期1937年5月12日。杨浦区图书馆的历史斜照可辨柱下的扛柱力士，地方志明记原有雕塑中一部分已不存。2009年5月14日、2013年12月19日的街景与2020年2月1日从对楼拍摄的清晰正面可确认现存的五券门窗、后退中门、中央两根槽柱、柱头叶饰、贝壳双涡卷山花及两层退台。模型按当代照片表现现存柱脚、支座和阳台。历史人像、飞鸟和狮球雕塑的全套形态与当前部位留待进一步调查。[1937年照片](https://www.virtualshanghai.net/Photos/Images?ID=14900) · [2009年南侧街景](https://commons.wikimedia.org/?curid=53199740) · [2013年斜视](https://commons.wikimedia.org/?curid=30235157) · [2020年东立面](https://commons.wikimedia.org/?curid=86502183) · [逐项来源、作者、日期与文件哈希](reference-review.json)

原生宏区14-13720-6694中的1600号轮廓，与实名OSM重合97.86%。朝四川中路的一边长约24.62米。地方志记占地676平方米，固定源投影面积约503平方米，两者量取范围有差异。原生层数估高28.8米，参考照片用于分布楼层与窗带，室内净高、门后进深及装饰轮廓均为比例估计。本次只制作东正立面及前缘的一段屋面，后部设施、南侧面、背面与室内另计。[底图与逐边道路测量](footprint-review.json) · [单体预览](../../../brunner-mond.html)

从上海项目目录运行下列命令，可输出三份GLB和可编辑的Blender文件。构建需要Blender、gltfpack、ImageMagick与Open Image Denoise。槽柱采用本项目已有的几何函数，现存扇贝、涡卷和叶饰单独建模，参考照片不嵌入模型。[构建入口](source/build_model.py) · [窗墙](source/street_elevation.py) · [石雕细部](source/ornament.py)

    python -B source/precise/huangpu-brunner-mond-building/source/build_model.py \
      --out /tmp/brunner-models --audit /tmp/brunner-native --decoded /tmp/brunner-decoded
