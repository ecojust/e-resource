# 上海跑马总会历史东楼与主钟塔：外观候选

[模型查看与外围漫游](../../../race-club.html) · [资产清单](../../../assets/models/candidates/huangpu-shanghai-race-club-east-building/manifest.json) · [检查记录](../../../data/audit/race-club-v1/README.md)

参照Livelikerw摄于2013-12-22的整体外观照片，制作东楼长主体与一座高主钟塔。包含深柱廊、浅色楼层带与凸出翼、红褐墙面、后部红色坡屋顶、两面钟盘、开放塔亭及红瓦塔顶。西楼、庭院连接体、另记副钟塔及邻楼不在本件范围，照片前方工商银行弧形楼、后方上海大剧院均未并入。

## 尺寸及形态依据

2018年澎湃文章记东楼四层、局部五层，西楼三层，中庭地下室一层，另区分主钟塔与副钟塔。次级百科条目记长逾100米、塔高53米和塔八层；这些数字不是测绘资料，且高度端点未说明。本件选择104米主体设计长、20米主体设计深；加前廊与凸出翼总深约27米，全部平面尺寸为估计。采用53米至候选小顶饰的高度，不表示已核实文献的计高端点。

主体设计层标高为0／5／11／18／23米，凸出翼局部墙顶25米、屋脊28米；主塔墙顶45.2米，开放塔亭45.6–49.4米，屋脊52.8米。这些分层并非照片逐层测量，也不以等层高代替史料楼层口径。地图约98.45×32.58米外框与“逾100米”文字边界不一致，未将地图轮廓作为历史建筑平面，也未按总建筑面积反推边长。

两段柱廊具有真实进深和开放柱间，后墙退至Y−7米；下部5–18米为通高浅色柱廊，上部18–23米为较矮的细红柱廊带，露台采用实心浅色女儿墙。六／八开间、层高、柱形、栏杆与窗格数量属于设计估计。长红屋顶置于主体后部，与前方平台及凸出翼小屋顶分开。主塔两面钟盘、上方拱冠与竖向长窗参照可见照片，钟针10:10仅为展示时间；未核实实际钟面数字与细部。照片中较低凸出翼的圆形细节尚未绑定为文献副塔，本件没有据此另造第二座高塔。

单张高位斜照片无法确认背面、底部遮挡处、完整平面与屋面交接；这些部分规则化补全。现代棚架、露台覆盖物、餐饮家具、设备和植物未建。纯色材质没有照片像素或扫描纹理。内部楼板只支持外观结构，不代表开放室内或完整结构设计。

[来源及短引](source-register.json) · [设计参数](design-input.json) · [照片与文献复核](../../../data/audit/race-club-v1/reference-review.json)。照片作者Livelikerw，CC BY-SA 3.0（https://creativecommons.org/licenses/by-sa/3.0/），仅本地参照，未重发照片或采样贴图。文献网页未确认开放许可，仅记录事实、短引与出处。原创代码及几何MIT。1933开工、1934建成与后期改造分别记录；2013照片不代表1934完整原貌或2026实测现状。

## 复跑

仓库根目录执行，Python依赖见`source/requirements.txt`；Blender4.3.2、gltfpack1.3.0：

```sh
python -m pip install -r projects/shanghai/source/precise/huangpu-shanghai-race-club-east-building/source/requirements.txt
npm ci --prefix projects/shanghai/source/city/detail/tooling
python projects/shanghai/source/precise/huangpu-shanghai-race-club-east-building/source/build_model.py --out /tmp/race
python projects/shanghai/source/precise/huangpu-shanghai-race-club-east-building/source/build_model.py --out /tmp/race --lod
blender --background --python-exit-code 1 --python projects/shanghai/source/precise/huangpu-shanghai-race-club-east-building/source/build_native.py -- --raw /tmp/race/huangpu-shanghai-race-club-east-building-raw.glb --out /tmp/race/huangpu-shanghai-race-club-east-building.blend --previews /tmp/race-previews
python projects/shanghai/source/precise/huangpu-shanghai-race-club-east-building/source/package_assets.py --raw /tmp/race/huangpu-shanghai-race-club-east-building-raw.glb --lod /tmp/race/huangpu-shanghai-race-club-east-building-lod.glb --native /tmp/race/huangpu-shanghai-race-club-east-building.blend --out projects/shanghai/assets/models/candidates/huangpu-shanghai-race-club-east-building --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/huangpu-shanghai-race-club-east-building/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/huangpu-shanghai-race-club-east-building --out /tmp/race-geometry.json --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

近远景保留相同总体外包、廊道深度、窗台与塔顶；远景简化窗框、栏杆与瓦垄。墙角内侧斜接，作者构件各自闭合，相接构件未作整楼布尔并集。原生保存后重开比较建筑几何哈希，预览地面不计入建筑。

网页检查需Playwright与Chromium。启动`python -m http.server 8782 --directory projects/shanghai`后运行`node projects/shanghai/data/audit/race-club-v1/qa-browser.cjs`；输出`/workspace/race-browser*`，可用`MODEL_URL`指定页面。运动边界回归运行`node projects/shanghai/data/audit/race-club-v1/qa-walk-motion.cjs`。当前仅允许整个楼体外包外的平地漫游；廊道虽有开放几何，仍不支持进入、登楼或登屋顶。未原址配准、未替换城市源对象，40处城市入口不变。
