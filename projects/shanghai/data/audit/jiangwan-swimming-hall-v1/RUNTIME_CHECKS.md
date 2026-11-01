# 江湾游泳馆运行时增量检查

本节预检使用基线 `225af1b75c235177ca23c775b9a9d3483eb032ba` 的79处目录（40处既有入口、39件候选）。队列中的游泳馆只用于80条灯牌压力输入；最终资产、定位合同、80处实际登记与网页画面需要分别验收。

## 灯牌与当前目录

灯牌生产代码未改。[布局预检](beacon-capacity-preflight.json)在4个视口内验证旧79条布局逐字段相同；加入队列中的游泳馆后，80条均可独立命中、无重叠或fallback。最紧凑243×138像素净区沿用20×18编号格和12像素字，84格容量余4格。纯布局测试不代替实际标题高度、地图投影、字形或原生触屏检查。

[35项灯牌／镜头预检](beacon-camera-preflight.tap)是在实际79处目录上执行；套件中固定历史数量的显式夹具不代表当前目录画面。[预检执行记录](runtime-preflight.json)保留这个时点与输入哈希，后续80处检查另写，不覆盖此处结果。

## 显示裁剪预算

当前生产容量仍为224行、4×224 RGBA纹理共14,336字节。[预算预检](clipping-budget-preflight.json)将基线39件候选的元数据分别交给基线类与当前类，旧202行12,928字节、顺序和owner全部相同，尾部空行保持零。主场西源、主场东侧共享组、既有体育馆共享组、尚未加入的泳馆5-owner组、带逐顶点ID的far组，共5种明确夹具，在颜色／深度／距离三类材质中得到相同shader文本、缓存键及uniform。这里只构造shader，实际GPU编译留给网页验收。

泳馆原源18个独立顶点的显示遮罩前置检查给出16个新三角，预期总218／224，仍有6行余量，不需要改容量常量或裁剪算法。它只涉及原源遮罩；最终三档资产、地面碰撞和源保留仍等正式合同冻结后核验。全目录三角总数与当前视口激活的三角数分别统计，浏览器必须按当前已激活clip集合求和，不能要求所有历史模型同时加载。

[10项现有裁剪测试](clipping-budget-tests.tap)覆盖行寻址、225行越界拒绝且保持既有状态、owner过滤与阴影材质。没有修改生产代码或重放历史GLB资产矩阵。

## 复验

从仓库根目录执行：

```sh
node --test projects/shanghai/tests/candidate-city-clipping.test.mjs
node --test projects/shanghai/tests/building-beacons.test.mjs projects/shanghai/tests/candidate-overview-camera.test.mjs
node projects/shanghai/data/audit/jiangwan-swimming-hall-v1/check-clipping-budget.mjs
node projects/shanghai/data/audit/jiangwan-swimming-hall-v1/check-beacon-capacity.mjs
```

`global-integration-checks.mjs` 是预先准备的最终7组检查脚本，必须在正式资产清单、footprint合同及80处目录冻结后执行；准备或语法通过不等于最终检查通过。

## 最终80处登记检查

正式v8四资产清单、最终定位合同和80处目录冻结后，[最终运行记录](runtime-checks.json)与[7组增量检查](global-integration-checks.json)均已通过。目录为40处既有入口＋40件候选，杨浦5处、黄浦28处；旧39条候选、41份资产清单和此前定位保持原值，只增量登记本栋4资产。

新泳馆仅给1666源加入16个显示三角，总计218／224，旧202行12,928字节完全相同，生产裁剪代码未改。实际近景组包含 `[1162,1666,1870,769,1110]` 五个owner；颜色、深度、距离三种测试材质都只收到1666的16行，另外4个owner不受此修正。全目录218行是登记预算，网页当前视口的活跃行数必须按实际激活集合求和。

最终碰撞为一片99个闭环点的有效多边形。8个实体正控、64个合法外部负控以及9片范围检查均通过。9片范围包含6片外部区域和3条道路肩带，只证明本栋模型没有增加遮挡，不能由此认定整条道路可通行；已被保留邻源1870覆盖的两个肩带点明确不进入全局开放负探针集合。最终合同仍单列22条道路肩带检查及这些原始邻源冲突。

[35项最终灯牌／镜头输出](final-beacon-camera-tests.tap)在实际80处目录下执行并通过。测试套件同时包含其固定70项、历史78项等显式夹具；这些夹具不冒称当前全目录网页画面。真实80灯牌字形、标题净区、触屏跳转、实际WebGL编译和屏幕取景由唯一浏览器QA另验。

最终轻量复验命令：

```sh
node projects/shanghai/data/audit/jiangwan-swimming-hall-v1/global-integration-checks.mjs
node --test projects/shanghai/tests/building-beacons.test.mjs projects/shanghai/tests/candidate-overview-camera.test.mjs
```

上述检查没有读取历史GLB资产矩阵。当前运行只处理正式元数据、显式shader夹具及生产2D碰撞；实际三档三角形解码和来源范围由建模、定位及独立审查报告分别绑定。
