# 江湾体育馆运行时增量

这些预检运行时，目录仍为基线 `a47e69e9cbde689266855d573aa8d1f25b02944d` 的78处（40处既有入口、38件候选）。队列中的体育馆只作为79条布局压力输入；这里不把预检当成最终模型或实际网页验收。

## 裁剪容量

体育馆保留原12顶点凹轮廓，仅为旧外檐显示外扩0.12米，预期新增10行，原192行需增至202。生产代码只将 `MAX_TRIANGLES` 从192改为224，增加32行、每张纹理2048字节，最终预计余22行。CPU碰撞格式、显示轮廓点数上限、owner判定和所有几何算法没有放宽。

[容量复核](clipping-budget-preflight.json)将实际旧38条候选交给基线与当前生产类，旧192行共12288字节、顺序和owner完全一致；新增空白填充保持零。主场西半、东半共享组、未加入的体育馆和带顶点ID的far组，共4种情况、颜色／深度／距离三类材质的输入一致，shader文本只差循环边界与纹理行中心分母。程序缓存键随容量改变，因此旧编译程序不会误复用新纹理高度。这里只构造shader源；真正WebGL编译和画面由唯一浏览器QA另验。

[10项裁剪测试](clipping-budget-tests.tap)检验第193行和最后224行的全球／owner范围寻址、225行拒绝且不损坏已有纹理和uniform、共享邻体排除与缓存holder重新绑定。

## 79处灯牌

灯牌生产代码完全未改。[布局复核](beacon-capacity-preflight.json)中，旧78处在4个视口逐字段保持一致；新增队列中的体育馆后，4个79条压力布局全部独立命中、无重叠。最紧凑243×138像素净区仍使用既有20×18编号格、12像素文字，84格容量余5格。实际标题高度、地图投影、SDF字形和原生触屏跳转不由这项纯布局检查替代。

[35项当前目录灯牌／镜头输出](beacon-camera-preflight.tap)与[执行及输入绑定](runtime-preflight.json)明确保留78处时点；最终79处登记后，实际集成检查另写 `global-integration-checks.json`，不覆盖本次预检口径。

## 复验

从仓库根目录执行：

```sh
node --test projects/shanghai/tests/candidate-city-clipping.test.mjs
node --test projects/shanghai/tests/building-beacons.test.mjs projects/shanghai/tests/candidate-overview-camera.test.mjs
node projects/shanghai/data/audit/jiangwan-gymnasium-v1/check-clipping-budget.mjs
node projects/shanghai/data/audit/jiangwan-gymnasium-v1/check-beacon-capacity.mjs
```

两个独立脚本读取冻结基线及当前生产代码，只处理元数据和显式测试几何，不重放历史资产矩阵。

## 最终79处登记检查

[最终运行记录](runtime-checks.json)已绑定79处（39件候选、杨浦4处）的正式目录、四资产清单及最终定位合同。[7组增量检查](global-integration-checks.json)全部通过；旧38条候选、40份库存清单与既有定位保持不变，旧192行12288字节仍完全相同。体育馆只增1558的10行，实际共202／224；12-owner近景组中的另外11个owner不会接收此裁剪，颜色／深度／距离三类材质均核对。

最终CPU碰撞是一片109个闭环点的有效多边形，9个实际低位实体正控、57个开放负控及9片开放区域全部通过，包括正门架空阳台下、相邻道路中心与肩带和三侧开敞面。几何／显示掩膜和通行范围分开，未开放体育馆室内或阳台步行。

[35项灯牌／镜头最终输出](final-beacon-camera-tests.tap)在实际79处目录生成后执行通过；套件同时保留其通用70项、固定历史78项等显式测试夹具，不把这些夹具说成全目录画面。浏览器真实79灯牌、标题净区、触屏和GPU编译由QA另行绑定。

正式目录可用时，从仓库根目录复验：

```sh
node projects/shanghai/data/audit/jiangwan-gymnasium-v1/global-integration-checks.mjs
```
