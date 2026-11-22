# 联市联谊会中华路东立面

第四批市级名录4A036列在中华路55号。街面七开间的上层有七座石栏小阳台，中央一座较宽。下面的通长露台交替设置实板和透空栏，中央三角楣、塔冠及两翼双窗山墙都以2021年1月8日的街照核对。[市表、摄影站位及其原件](../../../source/precise/huangpu-lianshi-association-east-front/reference-review.json) · [三处摄影站的110个同名点](../../../source/precise/huangpu-lianshi-association-east-front/source/frontage-solution.json)

原始和网页近档各19,236面，远档14,576面。三档共382次首交检查覆盖外窗、两种石栏、透空位置、屋冠和底层玻璃。配准保留原建筑520后部及19幢邻屋。49个地面点沿七个开间从人行道一直验入楼体，地图案例另检查原楼剩余部分的内部地面。[几何射线](preflight-surface-checks.json) · [地面和邻屋](placement-geometry.json) · [两种矢量底图六态](final-31267.json)

从中华路向庭院后侧看，默认方位为−108度、俯角51度。两种屏幕、两档模型各查12个临街特征，实际原城近档83,672面、远档12面上逐射线核对。初验发现中央三角楣的墙心被向外挑出的檐石遮住，保留原记录；在同机位核实檐口的街侧外表面。照度与细饰不能仅靠默认远景认定。[首轮中央墙心射线](initial-pediment-field-visibility.json) · [终版首碰](both-lod-self-visibility.json) · [原城遮挡](actual-camera-city-triangles.json)

以存档的模型机位和真实街区瓦片复算视线，可在上海项目目录运行下列命令。命令末尾还可指定包含相同瓦片的站点地址，脚本会逐件复核原始字节。

```sh
node data/audit/renji-silversmith-east-front-v1/trace-registered-city.mjs data/audit/lianshi-association-east-front-v1/actual-city-ray-inputs.json /tmp/city-rays-298.json
```
