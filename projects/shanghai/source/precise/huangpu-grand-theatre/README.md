# 大光明大戏院：临街入口与灯塔局部外观候选

[模型查看与外围漫游](../../../grand-theatre.html) · [资产清单](../../../assets/models/candidates/huangpu-grand-theatre/manifest.json) · [检查记录](../../../data/audit/grand-theatre-v1/README.md)

本件仅包含南京西路入口、大玻璃立面、五道竖肋、左侧灯塔及紧邻的圆角墙带片段。玻璃雨篷带底面方格，入口设深色石柱与门框，灯塔有浅色分格板及原创简化英文字牌。没有制作后部观众厅、整排商铺、右侧咖啡店楼或同框后方高楼；背面是局部候选的封闭截面，不能视作完整电影院后立面。

## 参考与尺寸解释

Pyzhou摄于2010-05-07的照片支持灯塔、圆角墙带、入口雨篷与竖肋，但大幅电影海报遮挡中部。修缮报道中的未定年历史入口照片及未定年修缮后夜照补充大幅竖框玻璃和雨篷底面格栅。模型综合这些不同时期的线索，未将其声明为某一年的精确复原，也没有复制电影海报、商标图案或照片像素。

上海黄浦账号转引黄浦档案的2019文章，分别写“二层楼连同招牌高30.5米”和30.5米灯柱；乐游上海转载文章写16米方形玻璃灯塔。计高对象和端点均未统一。本件选择30.5米作为候选灯塔总高，16米保留为未解记载，不相加、相减或平均为“正确高度”。二／三／四层亦分别涉及门面、观众厅和修缮项目口径，未用它们推导隐藏楼层。

几何整体外包约23.85×9.31×30.5米；前场主体深7米，雨篷向前至Y−2.2米，灯塔方形平面3.8×3.8米，均为设计估计。大玻璃位于4.6–15.35米，局部屋面16.2米；竖肋前端22.5米、后端21.5米，肋后退进屏墙顶21米。圆角半径1.2米，墙带、窗格、分格板、字牌大小及后部截面也为估计。初版肋顶18.6米明显偏低，照片复核后提高，**这些调整是视觉估计，未从照片像素获得量测值**。

玻璃使用不透射的原创纯色材质；夜照的暖色只帮助辨认玻璃位置，不作为日间颜色校准。史料另有黄色半透明玻璃描述，候选的透光、色泽与反射仍需细化。招牌为原创简化线形字，不是历史字体或精确字距复刻；雨篷没有臆造中文历史题字。

历史设计图及修缮文字记门厅和影厅轴线约转30°、休息厅呈腰果形；本件未建这些后部构成，也未将地图六角外框直接挤出为全楼。12,000平方米是修缮资料建筑面积，不能反推当前足迹或宽深。所有比例与屋面交接均未测绘、未原址配准。

[来源登记](source-register.json) · [实际设计参数](design-input.json) · [独立照片复核](../../../data/audit/grand-theatre-v1/reference-review.json)。Pyzhou照片为GFDL1.2或后续版本；另两张图片未确认开放许可。本项目只私下参考，未重新分发图片或取样贴图。网页只引用必要事实、短引与出处。原创代码与几何MIT。

## 复跑

仓库根目录执行；依赖见`source/requirements.txt`，Blender4.3.2、gltfpack1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/huangpu-grand-theatre/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/huangpu-grand-theatre/source/build_model.py --out /tmp/grand
python projects/shanghai/source/precise/huangpu-grand-theatre/source/build_model.py --out /tmp/grand --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/huangpu-grand-theatre/source/build_native.py -- --raw /tmp/grand/huangpu-grand-theatre-raw.glb --out /tmp/grand/huangpu-grand-theatre.blend --previews /tmp/grand-previews
python projects/shanghai/source/precise/huangpu-grand-theatre/source/package_assets.py --raw /tmp/grand/huangpu-grand-theatre-raw.glb --lod /tmp/grand/huangpu-grand-theatre-lod.glb --native /tmp/grand/huangpu-grand-theatre.blend --out projects/shanghai/assets/models/candidates/huangpu-grand-theatre --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/huangpu-grand-theatre/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/huangpu-grand-theatre --out /tmp/grand-geometry.json --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

近远景保留相同外包、字牌、圆角墙带与入口层次，远景简化窗框、雨篷底部格栅和曲线分段。作者构件独立闭合，相接处未作全楼布尔并集；原生保存重开后核对建筑几何哈希，摄影棚不计入建筑。

网页检查需Playwright与Chromium，启动`python -m http.server 8782 --directory projects/shanghai`，运行`node projects/shanghai/data/audit/grand-theatre-v1/qa-browser.cjs`。默认报告与截图输出到`data/audit/grand-theatre-v1/`，可用`MODEL_URL`或`QA_OUTPUT_DIR`指定页面及输出目录。仅支持整个模型外包以外的平地漫游，沿用35米模型范围与46米场地边界，不支持室内、进入门厅或登楼。
