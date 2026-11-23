# 延庆路159号住宅庭院拱门与临街转角

徐汇区延庆路159号在上海市第五批优秀历史建筑名录中登记为住宅，编号5D047。院门照片同时可辨159号街牌和市级建筑牌。1934年行名录已在该址登记古巴公使馆。早期行号与文献中的1933年说法尚不能确定现存房屋的确切建造年份。[市级名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [行名录原文线索](https://www.thepaper.cn/newsDetail_forward_5465498)

院内近照记录了两面卵石墙交接的位置。东墙有一道内凹拱门，门上有圆形浅浮饰。拱门左侧能看到斜坡形的台阶侧墙。转角有一浅一深的钢窗组合，浅色扇向外开启。北墙靠角的绿钢窗和檐下较小的外开扇分别按画面中的铰端、自由端建模。三组临街窗还能在2015年及2020年街景中辨认。[院内照片出处](https://blog.sina.com.cn/s/blog_8001328c010305q4.html) · [庭院相机参数](measurements/court-station.json) · [街面多站交会](measurements/north-street-window-intersections.json)

街面三组主窗的中心距，从靠角第一组向第三组量得约3.67米和6.56米。单独采用2015年的不同机位组合，第一组至第三组约6.32至6.89米。模型按三窗间距统一定尺，第三组与第一组轴距约6.58米。局部高程从院内假定地面起算；对照临街拍摄站的地面，两套窗台高程仍相差约0.8至0.9米。[三窗复核](measurements/north-street-window-intersections.json)

首版交付庭院与街墙的两个相交立面、钢窗、浅色窗套、百叶和拱门侧墙。模型截去未见室内与隐蔽背面。空调、架空线和衣物遮住的洞口按相邻可见边缘约束，细部仍有缺口。远处151至157号联排住宅和瑞华公寓有各自的登记与边界。[地址与来源](measurements/sources.json)

运行 `python -B measurements/check_mesh.py output` 可重建两档网格和组件检查。运行 `python -B measurements/render_court.py output/full-source.glb output/render` 可从院内摄影位置查看几何，局部窗格还可按原片坐标逐点核对。[照片取点](measurements/visible-photo-traces.json)
