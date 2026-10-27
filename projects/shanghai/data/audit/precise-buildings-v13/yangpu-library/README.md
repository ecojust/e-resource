# 杨浦区图书馆 v13 实际模型与网页检查

本轮新增一栋整馆精细模型。精选导航31项、普通精模12项、目录10个宏块；源建筑替换登记17项，涉及11个宏块和15个近景分块。全市1,796,419个建筑及部件仍未逐栋完成照片复原。

| 实际检查 | 证据与范围 |
|---|---|
| 模型总审查 | [root模型记录](model-review.json)，绑定四件交付资产及九项限定范围 |
| 原始几何 | [真实缓冲区检查](geometry-actual.json)，有限数值、法线、非退化三角面、两个内院内部天空采样点 |
| 网页与LOD压缩 | [完整模型](web-compression-actual.json)、[远景模型](lod-compression-actual.json)，实际Three/Meshopt解码的有向三角位置和材质一致；法线角容差保持0.05° |
| Blender | [实际重新打开](native-reopen-actual.json)，模型365,524三角形；预览舞台不计入 |
| 原生外观 | [三图及源记录](../../../../source/precise/yangpu-library/CURRENT_STATE.md)，[独立图审](../../../../source/precise/yangpu-library/independent-native-review.json) |
| 静态场景与行走 | [实际浏览器](browser.json)、[root六图查看](visual-review.json)，完整/LOD/释放/返回、当前源、近远景owner、9邻居、W与停止 |
| 最终目录采用 | [实际浏览器](catalog/browser.json)、[root一图查看](catalog/visual-review.json)，真实session采用同一静态模型，未声称动态全生命周期 |
| 数据组合 | [实际契约检查](data-contract-check.json)，原30导航、16owner和9目录宏块保持；最终生成工具另存[接受时脚本](tools/prepare_integration.actual-accept.py)，候选阶段脚本原样保留 |
| 运行时 | [31文件基线](runtime31.json)、[54项相关回归](runtime-regression.log)，本轮没有生产运行时改动 |

本次可信W输入实际位移0.420m，松键后3次记录的坐标和累积距离完全一致。相机与人物分离，未通过直接写坐标模拟行走。实际源模式为 `overture`；[源组件结果](browser.json)只覆盖当次加载，不是强制回退演练或测绘验证。

6张静态截图包括东入口、东北俯瞰、南入口、LOD、返回、W后；目录单独1图仅证明目录采用与近景状态。软件渲染截图不代表用户设备FPS。模型缺少后侧逐跨照片/实测资料，色彩、不可见细节和部分尺寸为推估；没有室内建模或照片纹理。[完整来源限制](../../../bund/REALISM_V13.md)。

浏览器和验证工具在[tools](tools/)；模型作者脚本在[source](../../../../source/precise/yangpu-library/authoring/README.md)。公开应用可以使用普通HTTP服务运行。检查时指定真实data文件和runtime31.json，并把输出写到新的目录；不要覆盖本轮历史证据。重复运行会受网络和地图服务当时状态影响，当前产品完整模型读取超时后需要刷新，尚无自动重试。

本轮首个检查器未拼上近景对象键的宏块前缀，因而没有正确找到已加载的目标分组；该次失败记录不作为验收。最终检查器按实际运行时键匹配，保留源、邻居、模型与释放断言及产品期限，并将31件独立运行时读取并行调度。南侧截图观察位按现有邻居轮廓、高度与模型射线检查调整，避免早期视点处于邻居建筑内；离开测试也改为实际越过产品现有保留距离的位置。相应离线控制、有限净空证明与真实浏览器接受分开记录。这里公开的是实际成功六图与目录单图运行记录所绑定的同一套工具；本轮未量化或宣称检查提速，生产运行时没有因此修改。

```sh
python tools/browser_acceptance.py --url http://127.0.0.1:8000/ --output /tmp/yangpu-new-check --expected-landmarks /path/to/shanghai/data/landmarks.json --expected-registry /path/to/shanghai/data/precise-buildings-v6.json --runtime-baseline runtime31.json --catalog-stage active
```

此命令需Python Playwright、Shapely和可用Chromium；必要时显式加`--use-env-proxy`。它重新检查当前实际服务，不会改变产品网络期限或生产运行时。原始检查绝不由源码语法检查替代。

