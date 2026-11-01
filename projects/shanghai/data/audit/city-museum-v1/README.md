# 旧上海市博物馆江湾馆舍接入主地图

[全局主图直达](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=yangpu-former-shanghai-city-museum&mode=overview) · [来源与重建](../../../source/precise/yangpu-former-shanghai-city-museum/README.md) · [四资产清单](../../../assets/models/candidates/yangpu-former-shanghai-city-museum/manifest.json)

现存地图主源1860完整轮廓与重叠门楼1931接入；西正面、现存两层南北翼部和黄瓦重檐门楼按照片详化。东中后厅仅作同低翼级的简化估计体量，当前具体范围、年代、屋面和门窗细部未核。院凹小源510/1262独立保留，室内、医院邻楼及院区地面不并入。

## 来源与年代

对象为长海路174号长海医院内旧上海市博物馆江湾馆舍，与同院飞机楼、人民广场上海博物馆及四川北路1844号1946年复馆地点分开。正式来源记录包含实际阅读的建筑条目、上海地方志目标小节、杨浦政府配图页及相关图文段落；13张视觉参考包含现代和历史外观、室内及扩建设想图，具体看图范围见[photo-review.json](photo-review.json)。室内照片不能证明现状后厅外轮廓；扩建设想图没有实施证明，不照搬其大院和高阶。

名录1935、条目1934开工／1936完成、1937开馆与地图built1933分别保留。历史单层翼与现存两层翼不混为同一时期。24米门楼、10.5米外墙只核到次级文字，未取得对应原设计或实测依据；主源30.1米也是粗源预测值。现状后厅范围、年代和细部未核，不宣称1935原貌复原或全立面照片验收。三份正式来源JSON保持冻结；第三方网页、照片和手绘只保留私缓存，公开仅列独立摘要、链接及哈希。

## 最终模型与原生检查

原始档96,016个三角面，网页档96,016个，远景档48,348个；四资产共13,809,214字节，含可编辑Blender。模型外包高度约23.962米，仍为作者估计。 原创模型几何与源码采用MIT，地图参考为ODbL-1.0。作者的独立目录重建、压缩前后有向FLOAT32三角比较及针对性射线分别记录在[作者重建](author-portable-rebuild.json)、[压缩几何核验](author-packaged-geometry-checks.json)和三档射线文件中。Blender实际保存重开，最终八图由Root逐张查看，见[native-visual-review.json](native-visual-review.json)。早期私有原型不是最终接受依据。

## 独立源与地图边界

主源1860的UUID为`cdc86c9b-dee5-4342-a7ee-e962fa0d030e`；重叠门楼1931的UUID为`d54de774-0952-43c1-98a0-c9cbeaf207b1`，两者在合同top与site_replacement中分别登记。小源510/1262未加入替换集合。它们实解粗模屋面高度分别约31.400000与28.700001米，属于地图原几何，不是现实建筑实测。

北侧独立小源1262上方的原1860悬置边片另采用GPU高度分段裁剪，只处理指定平面范围内28.705000—30.110000米的原近景本地高度区间。高度参考沿用真实far宏锚点并在运行时换算为GPU世界Y；低于起始高度的部分和独立小源屋檐保留。

原二维掩膜统计保持不变：主源轮廓内残量1.023006平方米，未应用补充高度裁剪前的可严格归属主源屋顶投影残量1.927832平方米。应用补充高度裁剪后，该主源高位屋顶投影残量为1.154982平方米；这是可严格归属屋顶的统计，不是共享近景owner所有构件的完整精确分解。最终范围与保护检查见[footprint-review.json](footprint-review.json)；不宣称所有旧源完全消失。

原二维裁剪新增40行保持不变，补充高度裁剪增加4行，本轮共新增44行，全目录262／288行。replacement_geometry、site_replacement、source IDs和collision保持原值；高度片只进入GPU显示集合，不加入二维源替换或地面碰撞。运行时专项证据见[height-clipping-checks.json](height-clipping-checks.json)。原生模型、四资产与作者原生图不因此重建。

## 目录与剩余任务

主目录81处、16区，杨浦6处、黄浦28处；40处原有建筑保留漫游，41件候选提供近似定位全局俯瞰。README模型“查看网页”均接入index主图，灯牌与目录使用同一模型登记；实际网页拾取和触屏验收见下方最终浏览器记录。

35项已交付任务与46项既有模型退出重复制作。已完成主楼隐藏10条，活动名录／构件1048条；博物馆两个源UUID均不在原1036条具名快照内，具名关联保持19条，待查1017条。所有旧完成范围保持不变；本轮仅新增b2-012记录，明确保留“东中后厅范围、年代与外观细化”和“院内小源510/1262与保护范围调查”两项，不关闭整条旧市博物馆名录。

下一项为中国航空协会旧址（长海医院飞机楼），ID`yangpu-china-aviation-association-building`、名录sh-historic-b4-177／4G011。已实际读取百科建筑沿革并看2013俯照；地图源、尺寸、地面前后侧照片与官方修缮原文仍需核实。

## 复验

```sh
python projects/shanghai/tools/build_candidate_city_integrations.py --catalog-only --check
python projects/shanghai/tools/build_model_todo.py --check
python projects/shanghai/tools/build_landmark_directory.py --check
python projects/shanghai/data/audit/city-museum-v1/todo-directory-checks.py
node --test projects/shanghai/tests/building-beacons.test.mjs projects/shanghai/tests/landmark-navigation.test.mjs
```

资产、模型几何、原生图、地图范围与实际网页各自绑定最终输入。目录数量和程序检查不能代替逐图审查；最终网页与集成结果见下节。

## 网页与集成验收

[Root检查](root-checks.json)9组通过；[最终运行时检查](runtime-checks.json)包含7组实际增量集成检查和35项灯牌／镜头测试，失败均为0。最终显示裁剪新增44行，全目录262／288；原218行共13,952字节保持不变。最终数字来自本轮实际报告。

[独立最终几何检查](independent-geometry-review.json)绑定当前manifest和raw/full/lod/native四资产；[独立地图审查](independent-placement-review.json)与[独立元数据审查](independent-metadata-review.json)分别记录对应范围。主源保护接口、院凹独立小源、碰撞与显示裁剪按足迹合同保留；几何验证不提升后厅来源的确定性，也不表示整栋历史原貌或室内已制作。

此前真实GPU诊断发现世界坐标Z分量插值约21.3—24.1毫米误差，导致北院指定悬片边缘未完全裁掉。同页可逆诊断确认：顶点阶段传递不含平移的相对坐标，片元阶段再恢复世界坐标后判定裁剪，可消除该残片，同时保留邻体屋檐。生产着色器采用相同修复；裁剪262行载荷、模型资产和地图几何不变，详情见[GPU坐标稳定核验](fragment-coordinate-stability.json)。诊断运行及恢复记录按阶段保留；最终结论另以本次fragment-rebased-final浏览器和逐图审查为准。

[真实浏览器记录](browser.json)完成56个实际地面碰撞检查、81个灯牌逐项拾取及原生触屏切换到博物馆，目标资产实际可见。共15张博物馆浏览器截图由QA和Root分别逐张实际查看并核对SHA256；其中15张被QA接受为相应范围的证据。参见[QA像素审查](qa-visual-review.json)和[Root像素审查](browser-visual-review.json)。 同一浏览器另以小型独立场景完成4项实际GPU检查，覆盖共享材质的逐物体平移、实例化深度与距离材质，以及透射材质；均通过且测试资源已清理。最终没有JavaScript错误、警告、HTTP错误或关键响应核验失败，实际浏览器会话已关闭。辅助页与主图的不同视角、后厅简化估计及保留邻源遮挡，应结合各帧真实观察理解；各帧的邻体遮挡与标签遮挡已在图像记录中注明。

本次最终浏览器记录没有失败项；此前未通过的运行按阶段保留，不作为最终验收证据。

后厅现状范围、年代及屋面门窗细部调查，以及小源510/1262的身份与保护范围调查继续保留。README链接修正见[导航审计](../readme-navigation-v1/README.md)；另行开展的公共网页诊断独立保存，不计入本轮博物馆截图数量或模型通过结论。
