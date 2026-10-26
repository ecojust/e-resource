# 许可与归属

## 原始照片

- **Antigng，2017年**：[《武康路129号住宅》](https://commons.wikimedia.org/wiki/File:%E6%AD%A6%E5%BA%B7%E8%B7%AF129%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。文件 `references/2017-antigng-cc-by-sa4-original.jpg`，SHA256 `89e59d2e55cd33b16636b004f09aa8d00994a6a93ffd654e8daf714ac51922b5`。
- **Windmemories，2026年**：[《20260209 129 Wukang Road》](https://commons.wikimedia.org/wiki/File:20260209_129_Wukang_Road.jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。文件 `references/2026-windmemories-cc-by-sa4-original.jpg`，SHA256 `43722c05f8bed1cc9108a5b4671add6eb3d1f07db6c6deb371cc0d14e1c7506a`。

两张照片原字节不变，完整来源与作者许可元数据在同名 `.metadata.json` 中。再分发应保留上述作者、来源、许可链接；若以后制作照片衍生纹理，必须注明修改并处理 CC BY-SA 的相同方式共享要求，不能将照片误标为CC0或项目代码许可。当前没有制作衍生纹理。

当前 raw 几何重建在资产版权字段注明 CC BY-SA 4.0 与两位照片作者；模型未嵌入照片。`calibration/comparison.png` 是在 Windmemories2026照片上增加分面和条件尺寸标注的分析衍生图，也采用CC BY-SA4.0。`common/`为项目几何/标定代码的未改副本，保留其代码许可与哈希；地图数据许可不因模型或代码许可而消失。

## 地图及高度来源

原轮廓来自现有 Overture Maps Foundation 建筑数据，底层数据提供者为 **© OpenStreetMap contributors**，记录 `w582319150@1`，许可 [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/)；地址关系示意中的道路、邻楼和店铺 POI 同样来自 OSM。数据来源说明保留在 geometry-input 和各 evidence JSON。`identity-context.png` 为这些地图坐标的绘制结果，应保留 OpenStreetMap attribution；没有第三方航拍底图。

旧高度由现有城市管线保存的 GHSL ANBH 2018 / 100m单元均值产生，许可记录为 CC BY 4.0。这里保留完整既有 provenance，不把该值当成房屋实测高度。

## 官方文字和辅助资料

官方历史建筑名单只保留URL、响应SHA和最短事实摘录“XH-J-091-V 德利那齐宅 武康路129号”，不随源码分发整页HTML。公开搜索结果和其他候选研究缓存不列入分发白名单。

辅助 Esri World Imagery 航拍只在目录外作私人身份关系核查；未声明再分发许可，未复制像素到本包、贴图或示意图，也未据图描绘轮廓。不能把整个研究工作目录递归复制到公共仓库。
