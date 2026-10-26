# City-only 水平投影单位校正候选

这是独立stage，基线为已经安装镜头revision/24上限的 `candidate23-v2-app`。不修改或覆盖旧 `final-camera-fix` 证据，不重建任何GLB/native或全城数据。

冻结city builder将X/Z定义为 EPSG:3857 半径6,378,137m下、宏原点纬度缩放后的米。MapLibre的`meterInMercatorCoordinateUnits()`使用平均地球半径6,371,008.8m。旧运行时将这两种水平单位直接等同，造成宏内偏移放大1.0011188495。1148距宏原点约一公里，结果与源轮廓错开约一米；v2真实eye在源外0.8069m，却在实际显示足迹内0.1831m。

独立actual GLB证据：`../../integration-ab/navigation-b-v3-candidates/actual-neighbor-raycast.json` 使用实际GLTFLoader/Meshopt和所有instance矩阵，旧真实运行时1148有FrontSide3hit/DoubleSide7hit，最近约0.328m；用作者坐标解释则0hit。`../vendored-city-projection.json`又用实际MapLibre/Three验证坐标映射，不依赖猜测半径。

最小改动只在`prepareCityObject`：

- X/Z使用作者EPSG:3857单位到Mercator的尺度。
- Y仍使用原MapLibre米尺度，地理anchor完全保留。
- 普通near和精确owner override继续复制同一far对象的position/quaternion/scale，无单独再缩放。
- 不改变普通邻楼、UUID、geometry、owner、材质、碰撞数据或精模资产。

精确安装白名单在 `installation-plan.json`：`src/map-scene.js`、新`tests/city-projection.test.mjs`、仅追加测试命令的`package.json`。须核旧SHA；root只安装白名单，不递归复制payload中用于测试的vendor/data symlink。

5项测试通过，原基线负控2项失败。测试执行实际vendored MapLibre/Three和真实scene变换函数：1148四个源点、旧错误倍率重现、Y/anchor不变、far/near/override同路线、16区各9个局部样点。

水平容差2mm包含作者Float32坐标舍入；未声称所有真实模型顶点/全部城市坐标逐位精确。冻结builder的northing本身使用非线性Mercator公式，测试按该公式生成输入。单原点的均匀Y尺度仍有跨纬度非线性高度残差，刻意维持现状；测试边界为相对原点±1.5km、300m高，残差小于6cm。这是明确的样本范围，不是任意距离/高度保证。

root受控安装后，应先用一个短诊断页面比较已核的B候选walk/oblique姿态，再冻结导航与正式AB11验收。源码单位修复并不证明任意相机都有完整可见立面，也不把旧视觉失败变为通过。
