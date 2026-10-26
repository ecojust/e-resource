# 许可、署名与来源

模型及本栋照片依据的重建代码按 **CC BY-SA4.0** 交付，许可链接：https://creativecommons.org/licenses/by-sa/4.0/ 。模型是依据照片重新构建的几何，未嵌入摄影像素；并非CC0，也不承诺取得建筑形象之外的商标权。

两张 Commons 公开原图均保留原始字节：

- Antigng，2017-08-19，《武康路210号住宅》，CC BY-SA4.0：[来源](https://commons.wikimedia.org/wiki/File:%E6%AD%A6%E5%BA%B7%E8%B7%AF210%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg)，文件 `evidence/2017-antigng-original.jpg`，SHA256 `e2c980954ff6a49f3053680b422711cfea1c2e32a04f26cc2bd8e34ee57b2018`。
- Windmemories，2026-02-09，《20260209 210 Wukang Road》，CC BY-SA4.0：[来源](https://commons.wikimedia.org/wiki/File:20260209_210_Wukang_Road.jpg)，文件 `evidence/2026-windmemories-original.jpg`，SHA256 `b1dabf00fb8608acbe5306662c7ba7e700435c9726135657a813e78ee0da4949`。

完整作者、许可、来源URL、日期和EXIF证据在 `evidence/photo-sources.json` 与 `commons-imageinfo.json`。应保留上述署名、来源、许可链接及更改说明；后续若制作照片衍生纹理，同样处理ShareAlike要求。

来源轮廓由 Overture Maps Foundation 汇集，底层 **© OpenStreetMap contributors**，记录 `w790826981@1`，许可 [ODbL1.0](https://opendatacommons.org/licenses/odbl/1-0/)。`geometry-input.json` 保留原数据与版本、provider、许可和城市ownership。本模型的许可不会抹去源数据库的ODbL义务。地图轮廓不是从照片/航拍重描。

既有高度 provenance 是 GHSL ANBH2018 的100m格均值，原元数据列CC BY4.0；仅保留作为基线，不据此校准建筑高度。

官方名单仅保留最短事实“XH-J-014-V 住宅 武康路210号”、URL、日期和响应SHA，不分发整页HTML。该名录由上海市规划和国土资源管理局2015-09-22发布。

`common/photo_architecture.py`、`photo_metric.py` 复制自项目已发布的129独立源码；保留原项目代码许可。`common/curved_prism.py` 从该模型的曲面几何函数复制，其出处和模型CC BY-SA声明保留。`common/blender_finish.py` 同源复制，仅将预览地面固定到本模型的0m基准下0.01m并增加该项日志，防止基底决定街面。没有引入字体、外部纹理或私有运行依赖。

目录外用于身份上下文的 Esri World Imagery 未声明再分发许可，**不属于发布白名单**，也不作为贴图或轮廓描摹输入。高倍瓦片返回No data，低倍主体有树遮挡，不能声称它独立证明了完整屋顶/外墙边界。
