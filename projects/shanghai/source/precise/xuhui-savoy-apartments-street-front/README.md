# 赛华公寓常熟路、延庆路转角立面

市房管局第二批优秀历史建筑2D047登记原名「赛华公寓」，公布时名「瑞华公寓」，常熟路209号。徐汇区房管局的修缮记录写作常熟路209弄1–4号，指同一公寓的住宅地址。公开资料记载1928年始建，建筑共九层。2020年启动外立面修缮，同时整治底层商铺与外部管线。2021年2月区房管局发布的照片显示外部工程已经基本完成。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [徐汇区房管局修缮记录](https://www.xuhui.gov.cn/zfjg_qzfbm_fgj_bmdt/20210220/283336.html) · [上海徐汇修缮报道](https://www.peopleapp.com/rmharticle/30020573995)

大楼位于常熟路、延庆路口东南角。冻结底图14-13719-6695中，1491自带中英文名「瑞华公寓」「Savoy Apartments」和旧称「赛华公寓」。实取OSM w495305884同时标注209号、常熟路、9层以及旧名，两版足迹交并比99.13%。临延庆路一面约40.40米，临常熟路一面约48.03米，中间的西北斜角宽约10.06米。相邻的皇家公寓有自己的足迹5455。[地块与坐标](footprint-review.json) · [图片、门牌与数据来源](reference-review.json)

临街底商以上，可在2016年与2021年照片中逐层辨认七排窗。转角中央的五排窗位于连续折面凸窗，顶层和底层使用平窗。两翼各有两组敞开辅助楼梯。照片中可见折面实心栏板、外露梯梁、楼梯间的立柱、浅色挑檐，以及顶层圆壳形装饰。模型按修缮后立面配色，底层店招以无字面板表示。建筑总层数包括屋面部分，屋顶后部与内院楼层无逐层实测。[Fayhoo于2016年2月8日摄，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Savoy_Apartments.jpg) · [修缮后的正侧面与夜景](https://www.xuhui.gov.cn/zfjg_qzfbm_fgj_bmdt/20210220/283336.html)

两条外墙的尺度采用冻结地图，竖向尺寸、栏板折角、窗肚墙进深、金属罩与楼顶屋间参考照片比例。进院后的住宅主门、车库、绿地、背墙及室内平面待后续查证。街面只表现照片可见的斜梯梁与梯缘，楼内完整的楼梯交通线不属于本件。衍生模型与构建代码按仓库MIT授权，照片只作核对。

在仓库根目录使用Python、NumPy、Shapely、Blender、Node.js、gltfpack、ImageMagick和Open Image Denoise运行下列命令。近景与远景分别生成；原生Blender工程展开展示可编辑的构件组。

    python projects/shanghai/source/precise/xuhui-savoy-apartments-street-front/source/build_model.py --out /tmp/savoy-assets --audit /tmp/savoy-audit --decoded /tmp/savoy-decoded

[单体预览](../../../savoy-apartments.html) · [城市总图](../../../index.html#landmark=xuhui-savoy-apartments-street-front&mode=overview) · [四份文件](../../../assets/models/candidates/xuhui-savoy-apartments-street-front/manifest.json) · [几何与落位核查](../../../data/audit/savoy-apartments-v1/)
