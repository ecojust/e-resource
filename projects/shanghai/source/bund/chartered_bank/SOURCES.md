> 当前发布模型为 [v4.3比例修正与局部照片纹理版](photo-v4.3/README.md)。下文为v3原始几何资料；旧高度与“照片仅作参考”表述不用于描述v4.3新增材质。

# 外滩18号：麦加利银行大楼精细模型

本模型依据2021年正立面照片与当前OpenStreetMap轮廓重新建模，提供真实几何层次。它不是激光扫描、摄影测量或建筑竣工图的精确数字化成果。

- 建筑轮廓：OpenStreetMap way [1196704498](https://www.openstreetmap.org/way/1196704498)，© OpenStreetMap contributors，ODbL-1.0；完整原始坐标及Overture对应ID在 `building-source.json`。
- 正立面照片：ScareCriterion12，*上海外滩麦加利银行旧址2021.jpg*，[Commons原页](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E5%A4%96%E6%BB%A9%E9%BA%A6%E5%8A%A0%E5%88%A9%E9%93%B6%E8%A1%8C%E6%97%A7%E5%9D%802021.jpg)，[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)；下载地址及校验和保存在 `photo-source.json`。照片仅用于观察比例、开间与装饰，未作为纹理嵌入模型。
- 几何、代码及材质由本项目重新制作；没有嵌入第三方3D模型、Google Earth几何或商业图库纹理。照片本身的CC BY-SA条件和OSM的ODbL来源须在单独复制它们时保留，不应把第三方资料整体改标为项目代码许可证。

已建的主要细部：中央三个深凹开间、两根完整通高圆柱及爱奥尼螺旋柱头；独立玻璃、窗框与细窗棂；底层五个开口、中央双扇饰面门与凸出石门框；两侧挑阳台、栏杆、券石和三角山花；顶部狭窗、放射纹浮雕、真实挑檐/托牙、屋顶栏杆及后退阁楼。侧后墙也有真实窗洞和墙厚，非实心体块上贴窗片。

尺度以实际前沿29.973m、现状轮廓进深约58.723m约束。正立面主檐约24.65m、阁楼山花约28.36m、旗杆约34.45m，属于**照片比例估算**；源数据只有7层，没有已核实实测总高。后侧开窗节奏和屋顶纵深、少量浮雕图案是依据建筑语言的简化推断，未获得对应立面图核实。`metadata.json`明确保留这些边界，不能标注成全楼测绘精度。

GLB：X向东、Y向上、Z向南，米制，地面0；以 `metadata.json` 的WGS84原点放置。模型已经旋转到实际临江方向，不能再次按朝向旋转。仅精确替换Overture UUID `31b91d93-cb3b-4203-afb8-8656dfc0277e`，不要按半径删相邻字林西报或和平饭店建筑。

```bash
blender -b -t 6 --python build_chartered_bank.py -- --render
```

需要Blender4.3+；脚本、`building-source.json`、`photo-source.json`放在同一目录即可，不需要本工作环境的绝对路径。输出GLB和Blender工程，另有正立面、三分之四视角、柱廊门窗细部三张渲染。GLB只包含模型；工程中的摄影机、灯光和灰色地面位于QA集合，未导出。

随附 `reference-facade.jpg` 是上述 ScareCriterion12 的 CC BY-SA 4.0 参考照片缩略版本，许可和作者保留在 `photo-source.json`。交付PNG为导出的真实GLB在Three.js PBR查看器中的截图；无摄影纹理叠加。Blender脚本也可独立生成Cycles渲染。
