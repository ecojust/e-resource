# 龙华塔 V9 / v3 最小脊座修订

v2实际原生全塔、中层及低机位图已检查：顶层封顶、塔刹、栏纹、檐下斗拱/椽子/平台承托改善，但曲脊仍与瓦面脱开，未通过最终验收。独立actual GLB在90点测得脊底离底板141–264mm、60个命中瓦片的点离瓦顶11–204mm；这些点均t≤.95，不能解释为檐外装饰悬挑。

本版仅新增56条窄连续灰脊基。两侧脚分别沿已有相邻坡面嵌入底板顶20mm，中心底点同样嵌入；顶部收窄并嵌到原曲脊下部。底部转折用正确的六点截面和显式端盖三角化，不以非凸扇形填洞。0≤t≤1连续，t>1保留原来可悬挑的装饰末梢。95mm侧脚宽、20mm埋入和15mm顶中线偏移均为施工表达估计，不称照片测量。

**其余构造不变**：全部瓦排及已验搭接、L7收口、六层连续芯墙、栏纹、塔刹、色彩材料、校准参数和三个镜头保留v2。`calibration.json`及未修改依赖/照片为硬链接共享不可变字节；修改文件已独立复制，v2和v1未覆盖。版本范围见 `revision-plan.json`。独立actual raw旧part保留检查将在新raw出现后运行，不能只凭这个说明宣称已通过。

## Root运行

先在本目录生成新raw：

```bash
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python run_root.py --output run-v3 --raw-only --execute
```

实际v3结构、旧part保留及新增脊座有限接触检查通过后，再由root独占运行：

```bash
/usr/bin/blender -b -t 2 --python render_previews.py -- --glb run-v3/raw/xuhui-longhua-pagoda-raw.glb --output run-v3/native --samples 48 --threads 2 --only all
```

保持全塔1000×1400、中层1200×900、1.65m低机位透视1200×900；相机为构件观察而非摄影测量配准。支持判断后的降噪策略与压缩可编辑blend不变。生成目录必须不存在，每文件严格<100,000,000B。agent只写小源码/元数据和内存部件检查，不运行大资产、Blender或浏览器。

源八角owner不变；40.64m/32.3m为官方名义口径，非实测。逐层尺度/隐藏面/首层绝对门向仍估计或未知，四张合法照片仅参考、不嵌图。程序MIT、新几何CC BY-SA4.0、源轮廓ODbL-1.0，四摄影作者各自CC0/BY-SA3/BY-SA4不改变。v2视觉缺陷证据保留历史，不混为v3已验。

最终native通过后才执行web/LOD打包和实际解码、生成模型交付证据；浏览器/owner/第三人称视野还需之后独立验收，未提前标记accepted。
