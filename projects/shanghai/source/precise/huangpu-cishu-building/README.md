# 慈淑大楼（东北街角及塔亭）

南京东路353号的慈淑大楼曾称大陆商场大楼、东海大楼。上海市房屋管理局在第二批优秀历史建筑中以2A027登记“慈淑大楼／东海商都”。市地方志《上海名建筑志》使用旧门牌327号，记庄俊设计、1931年动工、1933年建成。杨浦区图书馆所载文章另记1932年竣工，1933年2月9日中国国货公司开幕，并明确1934年加建南京路一侧顶层。工作名录与OSM也采用1932年。现状OSM的同一轮廓使用353广场、Mosaic Mall与旧名慈淑大楼。两条沿街面的定位来自南京路步行街与山东中路交会处。[房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [上海名建筑志](https://web.archive.org/web/20200927110455id_/http://www.shtong.gov.cn/Newsite/node2/node71994/node81772/node81774/node81784/userobject1ai108958.html) · [杨浦区图书馆藏图文](https://web.archive.org/web/20141122074649id_/http://www.yplib.org.cn/structure/jdsh/bnsz/dg_74828_1.htm) · [地块与名称](https://www.openstreetmap.org/way/494086374)

Virtual Shanghai将历史照“大陸商場”编为1322号，日期栏为1933年，估计年代区间为1933至1945年。据此只能比对同一幢楼及其窗墙特征，照片本身不能确定拍在1934年加建之前还是之后。2011年夜景记录临南京东路的窗组与塔端，2014年的街景和2024年4月拍摄的正面、仰视和斜照可逐一辨认东北角塔身双窗、分层退台和顶部环架。2024年的低角度窗墙近照还显示浅弧窗头上方金色分格扇纹、四扇一组的上层窗和略退后的窗间板。[大陆商场历史照片](https://www.virtualshanghai.net/Photos/Images?ID=1322) · [2011年南京东路夜景](https://commons.wikimedia.org/wiki/File:Shanghai_-_Nanjing_Road_(6275637199).jpg) · [2014年街面](https://commons.wikimedia.org/wiki/File:353_Plaza_Shanghai.JPG) · [2024年街角实照与窗墙细部](https://commons.wikimedia.org/wiki/Category:Donghai_Building) · [照片条目、署名、日期、许可及文件哈希](reference-review.json)

重建范围从斜角两端分别沿两条街道展开，包括山东中路三组、南京东路四组近角窗跨，街角底层店面、六道上层窗列及顶部阶梯塔亭。灯亭的外圈、竖撑、内灯体与旗杆分别建模。照片中的商户商标、悬挂的广告条幅和迎风旗面属于当时的营业与街景陈设，模型保留固定建筑构件。底图和OSM用于水平定位，未获实测剖面，窗宽、楼层高度、檐口、塔亭退距及灯架直径依据照片比例估测。外展临街翼、南京东路中段、九江路面与完整屋顶另计。[源体与街道核对](footprint-review.json)

地方志记载建筑原有通向三面街道的十字通道。现有照片仅能确认近角店面，未见现状通道两端、内部门槛和净宽；本次保留外观浏览，商场内走线待补测。几何、材质与装饰均由参数化源码生成，模型包未嵌入参考照片。[制作源码](source/street_corner.py) · [单体浏览](../../../cishu-building.html)

## 重新生成模型

从上海项目目录运行。构建入口使用本项目通用打包工具，调用 Blender、gltfpack、ImageMagick 和 Open Image Denoise，输出原始、网页和简化GLB以及可编辑的Blender文件。程序同时重新打开原生文件并核对网格。

    python -B source/precise/huangpu-cishu-building/source/build_model.py \
      --out /tmp/cishu-models --audit /tmp/cishu-native --decoded /tmp/cishu-decoded

可用 `--blender`、`--gltfpack` 和 `--oidn` 指定本地工具路径。[构建入口](source/build_model.py) · [几何及放置核验](../../../data/audit/cishu-building-v1/README.md)
