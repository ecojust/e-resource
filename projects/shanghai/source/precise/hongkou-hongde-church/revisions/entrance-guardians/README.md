# 鸿德堂北门石狮

市房管局第二批优秀历史建筑名录2F003号登记鸿德堂，地址为多伦路59号。北门的台阶两侧各有一只坐狮，面向街道。Livelikerw在2014年12月9日拍摄的日间照片可辨卷鬃、凸眉、短吻、前爪与胸带。东侧石狮一腿直落，另一爪下有较小的纹饰。西侧石狮的一爪搭在近圆形石球上。Windmemories于2024年1月7日拍摄的夜景中，两只坐狮仍分别位于同一方座上。两份照片采用CC BY-SA 4.0授权。[2014年照片](https://commons.wikimedia.org/wiki/File:Fitch_Memorial_Church_Shanghai.JPG) · [2024年照片](https://commons.wikimedia.org/wiki/File:20240107_Hongde_Tang_Christian_Church_on_Duolun_Road.jpg) · [日期、作者及完整照片指纹](reference-review.json)

上海虹口于2024年11月24日发表的《多伦路上的中式教堂》记载，杨锡镠设计的鸿德堂于1928年10月7日举行献堂典礼，建筑描述提及门口两只石狮。现有照片不能确定两座石雕的具体雕刻年代。模型保留坐姿、脸部轮廓、束带和两侧前爪的差异，对背部细纹与东侧小雕件采用概括形状。[上海虹口报道](https://www.163.com/dy/article/JHPI11570514A3B5.html)

原模型 `hongkou-hongde-church` 已包含北门真拱、台阶及两座石台。其来源脚本将石台标为 `guardian-base-only-statue-unmodeled`。新雕像分别对齐原石台顶部的0.86米标高，以照片中头高与座宽的比例估计其尺寸。地图对应上海基督教鸿德堂的具名OSM建筑w1085786138，宏块14-13720-6692仅替换2557号源，北门外向方位约5.57°。[原模型与建筑地块](../../README.md) · [方位、原件及石台](baseline.json) · [坐狮几何](guardians.py)

修订沿用鸿德堂原交付的许可。模型和两张外观照片采用CC BY-SA 4.0，程序代码采用MIT。OSM与Overture轮廓沿用ODbL 1.0。石狮使用实体曲面塑形，摄影原件仅供建模参考。[原模型许可](../../COPYRIGHT.md) · [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

实读网页近景的新增顶点，两只石狮各宽0.524米，进深0.576米，最高点在模型标高1.703米处。爪下支承底部嵌入原石座约3毫米。平面投影完全落在每座原有0.66×0.65米的台顶内，保留两座之间的门阶通路。

四件成品中，网页近景保留441,648个三角面，远景保留192,592个三角面。原生工程内原5个对象的矩阵及2个原网格签名保持一致，新雕像分成8个有名称的可编辑网格。前后两档网页文件都已在Chromium中实读，门口对照图显示两侧增添坐狮，中央阶梯清晰。[成品下载及指纹](manifest.json) · [逐对象复验](../../../../../data/audit/hongde-entrance-guardians-v1/native-object-signatures.json) · [门口照片与渲染比较](../../../../../data/audit/hongde-entrance-guardians-v1/visual-review.json)
