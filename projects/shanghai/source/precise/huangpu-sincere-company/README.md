# 先施公司历史主楼与摩星塔外观候选

[查看模型](../../../sincere-company.html) · [四件资产与摘要](../../../assets/models/candidates/huangpu-sincere-company/manifest.json) · [检查记录](../../../data/audit/sincere-company-v1/README.md)

本件表现南京东路、浙江路转角的历史先施公司主楼及摩星塔，包含照片可见的浙江路北段低翼。时装商店与东亚饭店属于同楼的不同经营用途，不能仅按别名拆为两栋。永安、新新、大新及四川中路的东亚大楼均不在本件范围；摩星塔也不是永安公司的绮云阁。

## 来源与尺度

[来源登记](source-register.json)汇总两份实际读取的官方志书、三张实际查看的照片及冻结地图审查。官方记南京路沿街约66米、浙江路约61米，主楼原5层、后加2层，共7层，高“30余米”；同文占地7000余平方米，不能把66×61米自动变成完整矩形。官方没有给出准确塔顶高度，也未核实主楼高度是否包括所有屋顶局部。现代地图约106.04×74.99米为粗覆盖范围，无分栋、天井或高度数据，不作为实测墙线。

本模型选100×68米主体，主檐30.6米；东北低翼21.8米，主楼7个、低翼5个造型层。东南角塔由阶梯钟座、两级方亭和圆形上亭组成，帽顶47.3米、杆顶51.3米。**这些数值、段高、退台边界和削角均为作者设计估计**，不能把“30余米”加上自拟塔段解释成已证实的总高；官方三层空塔的计层方式也未逐项绑定到本模型构件。

[文献复核](../../../data/audit/sincere-company-v1/documentary-review.json)保留原始数据及范围限制；[地图范围审查](../../../data/audit/sincere-company-v1/footprint-review.json)记录独立源对象、邻楼与别名排除。

## 照片与简化

实际观察的照片包括Pyzhou的2010-05-07长街面（GFDL1.2或以后版本）、Livelikerw的2013-12-19摩星塔近照（CC BY-SA3.0），以及Chainwit.的2024-04-24夜间街角（CC BY4.0）。[独立照片复核](../../../data/audit/sincere-company-v1/photo-review.json)逐张记录出处、SHA256、时间和可见范围；照片拍摄年不等于上传年。

保留底层骑楼外廊、削角入口、跨层圆柱与弧形断檐山花、石栏／铁栏阳台、檐口、摩星塔方转圆的分段，以及浙江路北段降低的屋面和大拱窗。不同年份的广告与招牌不复刻，广告遮挡后的细部没有可靠重建依据。长街面仍采用较规则的模块化窗网，主檐与柱列层级经照片比较作了强化，但不等于复原精确开间、柱式或雕饰。侧后墙、屋面连接、深部平面、雕饰和窗网有推估；封闭屋面是候选表达，不能证明实楼没有内院。钟面10:10为示意。它不是1917年原貌复原，也不是2026年测绘现状或全部立面的照片精度验收。

照片仅供观察，不取样、不嵌入且不随包分发；每张照片保留各自许可。公开包中的原创建模代码与几何为MIT。文献只保存事实摘要与出处，不推定其全文再发布许可。

## 重建与检查

从仓库根目录执行；Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender和gltfpack。

```bash
python projects/shanghai/source/precise/huangpu-sincere-company/source/build_model.py --out /tmp/sincere-build
python projects/shanghai/source/precise/huangpu-sincere-company/source/build_model.py --out /tmp/sincere-build --lod
python projects/shanghai/source/precise/huangpu-sincere-company/source/verify_geometry.py --assets /tmp/sincere-build --out /tmp/sincere-geometry.json
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-sincere-company/source/build_native.py -- --raw /tmp/sincere-build/huangpu-sincere-company-raw.glb --out /tmp/sincere-build/huangpu-sincere-company.blend --previews /tmp/sincere-previews
python projects/shanghai/source/precise/huangpu-sincere-company/source/package_assets.py --raw /tmp/sincere-build/huangpu-sincere-company-raw.glb --lod /tmp/sincere-build/huangpu-sincere-company-lod.glb --native /tmp/sincere-build/huangpu-sincere-company.blend --out projects/shanghai/assets/models/candidates/huangpu-sincere-company --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/huangpu-sincere-company/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/huangpu-sincere-company --out /tmp/sincere-packaged.json --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack --blender /usr/bin/blender
```

作者构件分别闭合，未作全楼布尔并集，不宣称整楼是单一流形。压缩解码检查逐材质有向三角面及其重复次数，保留真实索引拓扑结果。近远景保持外包，远景简化窗框、栏杆、齿饰与曲面分段。Blender文件包含另计的摄影棚地面、灯光和相机。

网页检查需Playwright与Chromium。启动`python -m http.server 8782 --directory projects/shanghai`，运行`node projects/shanghai/data/audit/sincere-company-v1/qa-browser.cjs`；可用`MODEL_URL`和`QA_OUTPUT_DIR`指定页面及报告目录。仅支持整栋外包以外的地面漫游，真实模型外廊开口不意味着已支持进入外廊、登阶或室内。未原址配准或替换城市对象；独立场景使用60米模型范围、80米外围场地边界。
