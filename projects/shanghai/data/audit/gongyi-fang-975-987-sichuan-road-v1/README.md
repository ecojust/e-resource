# 公益坊3号楼 · 交付核验

四川北路975–987号的九跨商住楼与北面的1号楼分开核验。3号楼独立页提供原始、网页和远景三档GLB，以及从街角、海宁路端墙、屋顶、阳台和底铺观察的八个机位。[3号楼预览](../../../gongyi-fang-975-987-sichuan-road.html) · [楼号、年代和建筑范围](../../../source/precise/hongkou-gongyi-fang-975-987-sichuan-road/README.md)

| 实际检验 | 结果 |
| --- | --- |
| 网格导出 | 原始和网页各148,504个三角面，远景106,640个。近、远两档各自经独立解码器校验三角面的位置、顶点顺序和材质。近景1,355个实体、757个具名可编辑组，远景1,199个实体、674个具名组，所有实体闭合且有正体积。[曲面校验](preflight/decoded-surface-comparison.json) · [闭合校验](preflight/editable-parts-closure.json) |
| 砖面与照明 | 近、远两档各检查896个纹理三角面上的2,688个UV角点。对每档解码网格按八个源机位重新渲染，砖影、窗洞和阳台透空均取自实际几何。[UV核验](preflight/render-uv.json) · [近景八图](preflight/full-views/views.json) · [远景八图](preflight/lod-views/views.json) |
| 阳台、几何透空和照片 | 每档核460处栏片、托座、花铁及透空，再向修后原图的十处像点发射视线，三份网格均460/460、10/10。[原照与模型对照](balconies/README.md) |
| 街面四个底铺、十六组阳台门 | 以修后街照固定116束视线，三份网格均88处在原点直接打中预期表面，116处在三像素内打中。南五跨采用同层参照和2018年全景对照。[逐点结果](street-openings/three-mesh-window-and-shop-checks.json) |
| 海宁路端墙 | 三层四处、二层三处凹口逐个检查面心、内外洞边、窗帽和窗台，包括窗间实墙，三档各52/52。2022年夜景的可见范围另有记录。[原始网格](../../../source/precise/hongkou-gongyi-fang-975-987-sichuan-road/measurements/south-short-wall-first-hit-raw.json) · [修后夜景](../../../source/precise/hongkou-gongyi-fang-975-987-sichuan-road/measurements/south-short-wall-post-repair.json) |
| 修后屋面 | 2025年33个固定像点，28个直接打中，32个在两像素内。2021年28个固定像点，22个直接打中，27个在两像素内。两期各自保留原来未命中的位置。[两期三网报告](repaired-roof/README.md) |
| 城市定位 | 主楼底座与地块561相交557.37平方米，原地块保留62.08平方米；玻璃商业楼627和北侧1号楼3085重叠均为零。当前发布独立页，城市主图纳入进度按实际主线交付更新。[三网实算](../../../source/precise/hongkou-gongyi-fang-975-987-sichuan-road/measurements/registered-plinth-and-retained-city-source.json) |

桌面和手机分别使用八个普通页面按钮查看模型，切换近景、远景和自动模式，并通过真实下载按钮保存三件GLB。浏览器回读的页面、脚本、清单与文件哈希一并记录。[双端截图及下载回执](ordinary-ui/ordinary-views.json)

默认屋顶依据修缮后影像。2018年瓦面研究通过源程序另行输出，原始、网页及远景三个下载均使用默认修缮后状态。[2018年研究导出回执](preflight/2018-source-study.json) · [模型及公开图像的许可](../../../source/precise/hongkou-gongyi-fang-975-987-sichuan-road/SOURCES-LICENSE.md)
