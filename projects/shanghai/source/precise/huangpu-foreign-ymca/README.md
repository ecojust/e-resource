# 西侨青年会 · 上海体育大厦

黄浦区南京西路150号。上海市房屋管理局第一批名录编号1A014，原名称栏印作“西桥青年会”，使用单位栏为“上海市体育总会市体委”。上海市地方志、现存保护铭牌和市体育大厦的门牌均指向同一栋楼。地方志记载1928年开幕，1932年扩建至九层，由哈沙德洋行主持设计，安铎生具体负责。历史全址约1,933平方米，本次依据冻结地图中面积约900平方米的临街楼栋制作。[官方名录逐行核对](../../../data/audit/first-batch-register-2026-11-20/register-rows.json) · [地方志与资料登记](reference-review.json)

2004年拍摄的正面可以数出三座高拱、两翼各三条窗带与四根凸出的砖垛。2013年斜面照片显示暗色砖嵌成菱形、浅黄色墙身和金色“体育大厦”四字。2015年入口近景可辨三座石门套、双柱、窗裙、雨篷玻璃与椭圆金属缘饰。2025年照片显示上部两翼依然斜夹中央开敞空间，退入的后墙带窄拱窗。三个航片版本用于核对街面、楼翼、后段及毗邻建筑。影像发布日期与实际拍摄日期须区别理解。[2004年整面](https://commons.wikimedia.org/wiki/File:Old_YMCA_-_Nanjing_Road_(273732057).jpg) · [2013年街面对照](https://commons.wikimedia.org/wiki/File:Former_Foreign_YMCA_Building.JPG) · [2015年入口细部](https://commons.wikimedia.org/wiki/File:Shanghai_(December_9,_2015)_-_105.jpg) · [2025年中央退界](https://commons.wikimedia.org/wiki/File:Former_Foreign_YMCA_Building_20250505-1.jpg)

临街面宽约27.11米，进深约33.30米，后边沿街方向错移约0.67米。模型以独立的三道退进门口、两层高拱和开窗墙构造下部，中央平台以上的双翼与后段分别建模。两翼的上层双圆拱、砖垛压顶和浅色小饰件均为立体表面。模型高约34.91米，参照源高与照片比例。庭深、墙色、檐口及被遮挡的屋顶、后墙和设备缺少实测资料。室内泳池与街区后场不在本件交付范围。[四种文件清单](../../../assets/models/candidates/huangpu-foreign-ymca/manifest.json) · [原始模型代码](source/sports_hall.py) · [独立查看器](../../../foreign-ymca.html)

原城市源2846与当前 OSM 名称“上海体育大厦”对应，西邻170号国际饭店的源1138和东邻128号永新广场2365均为另一栋。除城市记录外，还核对了已发布83.8米国际饭店模型的整体包围范围。地面阻挡按交付网格两米以下的实体投影，临街三座入口在门扇以前保留退进空间。[冻结地图、门牌与经纬网格](footprint-review.json) · [源楼及相邻模型复核](../../../data/audit/foreign-ymca-v1/placement-geometry.json)

成品几何与源码为原创，采用项目 MIT 许可。照片仅用作观察，没有做贴图。四字招牌用 Noto Serif CJK SC 的改名字集挤出，字形与照片所见书法有差异。[摄影署名及许可](reference-review.json) · [字体来源](source/fonts/provenance.json) · [字体许可](source/fonts/OFL.txt) · [项目许可](../../../../../LICENSE)

    python -B projects/shanghai/source/precise/huangpu-foreign-ymca/source/build_model.py --out /tmp/foreign-ymca/assets --audit /tmp/foreign-ymca/audit --decoded /tmp/foreign-ymca/decoded
    python -B projects/shanghai/source/precise/huangpu-foreign-ymca/source/check_surfaces.py --manifest /tmp/foreign-ymca/assets/manifest.json --out /tmp/foreign-ymca/surfaces.json
