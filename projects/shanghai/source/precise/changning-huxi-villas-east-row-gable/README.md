# 沪西别墅东侧临弄山墙与跨层钢窗

上海市第三批优秀历史建筑3M008位于长宁区愚园路1210弄东侧。区规划资源局记其建于1948年，占地5710平方米，建筑面积3120平方米，并记载“好莱坞”赌场兼舞厅原在别墅西侧。[长宁区规划和自然资源局](https://www.shcn.gov.cn/col7698/20211207/1152659.html)

Livelikerw在2014年2月8日从弄内向东北拍下东排红砖与浅色粉刷相接的山墙。最近的房屋有上下两扇狭窗、山尖下的小通气口、白色转角雨水管，以及灰色实板隔开的上下两层绿色钢窗。模型沿这一段可见前墙、屋檐和后退短翼收口。[2014年原照及CC BY-SA 3.0署名](https://commons.wikimedia.org/wiki/File:Hu-Xi_Bieshu_Shanghai.JPG)

沿弄由南到北，保护地块中六排独立屋面的原城市地物编号依次为4129、733、3123、522、523、3542。南口外的2015年冬季道路摄影能辨入口和东侧白色建筑，街房、树木遮住了院内门牌。2号地图点在南数首排。2014近墙仍保留南数首排、次排两个位置，单栋完整端墙和整排住宅不作位置互换。[保护地块](https://www.openstreetmap.org/way/488959788)

在本项目目录运行 `python source/build_model.py --output out/full-source.glb` 可生成近景，添加 `--lod` 可生成远景。运行 `python measurements/check_end_wall_solids.py out/closed-components.json` 可逐件检查闭合实面。原照像素和两种位置的控制结果位于 measurements。

首稿与修订稿都接受同一组21个原照材料点检验。修订稿按原片补入上部冷凝器圆形面框、背托和排水管的下端折返，并调整灰色园墙帽及后部短返窗台的高度。近景、网页近景和远景各有19点直接命中实物表面。上机架支脚的测点击中了机壳，小通风口左缘的测点击中了粉刷收边。南口照片中的围挡和树木遮住院内细部，因此两个排位图只用于对照同一街口光轴的可见范围。

本件的粉刷、面砖及陶瓦都有独立生成的颜色和法线图。面砖取院墙几处明暗相近的砖芯。最近屋面的可见瓦面很窄，瓦色取自同张原片中下一排的坡面。玻璃透明度是表现用值。室内、其余排屋和西侧邻栋的用途均超出模型范围。

运行 `python source/finishes.py` 可重新制作六张程序纹理。运行 `python measurements/check_gable_surfaces.py out/full-source.glb out/photo-probes.json` 可复核21个独立原像点。运行 `python measurements/render_registered_gable.py out/full-source.glb out/registration` 可重绘弄内与南口两站的三张模型图。
