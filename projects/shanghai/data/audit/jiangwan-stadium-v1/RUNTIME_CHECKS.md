# 本轮运行时补丁检查

这些补丁测试执行时，全局目录仍为基线 `96e4dfaff588222475c25a66af1c84a24b45a475` 的77处（40处既有入口、37件候选）。78号体育场在灯牌边界回归中采用队列身份及名称，仅作为布局测试输入；这些记录不代表其实际模型或最终78处目录已通过验收。

- [灯牌记录](runtime-beacon-preflight.json)：27项测试通过，[完整输出](beacon-tests.tap)。现有档位容不下78个编号时增加20×18像素精灵，文字保持12像素；旧77处在四种既有视口中的布局逐字段相同。243×138像素净区可容纳84个独立格，78个编号无重叠并逐个命中。
- [碰撞预算记录](collision-budget-checks.json)：17项JS检查（7项新增几何边界、10项既有GPU裁剪）和12项Python检查通过，[执行输出](collision-budget-test-execution.json)。只对CPU碰撞允许每闭环256点、每多边形32环、总4096点，最多32个多边形；显示替换和场址替换仍为65点／8环，GPU仍为192行。
- [旧目录对照](collision-budget-previous-models.json)：使用基线模块和新模块分别合并原40处与旧37件候选，结果逐字段相同。只读目录元数据，没有重新打开历史模型资产。
- [实际字体度量](actual-glyph-metrics.json)：下载生产字体的数字字形PBF并解码度量；1–99中最宽双位数字连同0.5像素描边为13.5像素，距新精灵边框内侧至少1.5像素。原PBF留在私人研究目录，未随仓库分发。该计算不代替最终浏览器SDF字形实看和触屏检查。

从仓库根目录复验：

```sh
node --test projects/shanghai/tests/building-beacons.test.mjs
node --test projects/shanghai/tests/candidate-geometry.test.mjs projects/shanghai/tests/candidate-city-clipping.test.mjs
python -B projects/shanghai/tests/candidate-catalog-increment.test.py
node projects/shanghai/data/audit/jiangwan-stadium-v1/check-beacon-capacity.mjs
node projects/shanghai/data/audit/jiangwan-stadium-v1/check-collision-budget.mjs
python -B projects/shanghai/data/audit/jiangwan-stadium-v1/check-number-glyph-metrics.py
```

字体复验脚本验证原字节哈希；若上游字形改变，应另行检查新输入，不能覆盖旧检查口径。脚本输出 `glyph-metrics-reproduction.json`，与首次下载记录分开。

最终78处目录生成后，[运行时正式记录](runtime-checks.json)另验35项灯牌／镜头检查及[7组集成检查](global-integration-checks.json)。旧147行裁剪数据的9408字节保持一致，西看台25行和东看台20行正好组成192行；两个原源向量残留为零，独立邻源继续保留。最终碰撞为11个多边形、43个环、956个闭合点，单环最多227点；8个实体正控、56个开放点负控，以及内场、两短端通道和三处入口凹区的6项面积交集检查均通过。

[首跑记录](runtime-integration-attempts.json)保留了目录已为78而index静态计数仍为77的失败；补齐该标签后重新通过，未借此更改模型或生产渲染。最终35项测试的[完整输出](final-beacon-camera-tests.tap)与最初77处目录阶段的27项输出分开。浏览器中的实际模型、近景源、数字字形和触屏效果另行验收。
