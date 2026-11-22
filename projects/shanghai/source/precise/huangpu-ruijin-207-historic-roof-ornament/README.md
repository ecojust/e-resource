# 瑞金二路207号公董局医学化验所历史立面

上海市第五批优秀历史建筑名录将瑞金二路207号列为“公董局公共卫生救济处医学化验所”。同时代名册使用法文路名 Route Père Robert。法国在华历史学会记载，该建筑由 Léonard 与 Veysseyre 于1934年设计。上海巴斯德研究所于1938年在原公董局化验所内成立。两张历史照片所见的主楼都有九跨长立面、两端玻璃带与中央深色格窗。[上海市名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [法国在华历史学会文章](https://wiki.histoire-chine.fr/index.php?title=Il_%C3%A9tait_une_fois..._l%27Institut_Pasteur_de_Shanghai) · [Virtual Shanghai 建筑记录](https://www.virtualshanghai.net/Data/Buildings?ID=249)

美国摄影师 Malcolm Rosholt 约在1938年拍下正面。布里斯托大学 Historical Photographs of China 已为原底片背面所写的“可能是医院”订正题名。另一张约1934至1938年间的照片从短侧翼拍摄，能看到两个窗跨、侧墙转角和檐口。模型保留两图可辨的26组常规钢窗、中央深色格窗、两扇外挑上悬窗、21个墙面小通风孔、四道水平挑片和两个屋顶通风帽。[Rosholt 原片 Ro-s018](https://www.hpcbristol.net/visual/Ro-s018) · [两图穿插复核的墙端和窗位](measurements/historic-two-view-registration.json) · [钢窗测点](measurements/historic-front-windows.json)

以层高3.50米估算整体尺度，3.0至4.0米是保留的尺度范围。长立面实际建模长度约45米，侧翼照片可辨的部分进深约11米。两次摄影均有树木、围墙和行人遮挡楼脚，模型在可辨的外墙范围收束。玻璃色阶以黑白照片为依据，顶部与内墙的遮蔽面按外轮廓估算。[长立面相机](measurements/rosholt-long-front-registration.json) · [中央深色格窗](measurements/ro-s018-central-glazing.json) · [屋顶挑片](measurements/ro-s018-ornament.json)

打开模型页可在整座历史立面、上悬窗、中央深色格窗、旗杆座和短侧翼之间切换。按下列命令可从上海项目根目录重建。照片、计算脚本与模型各自的使用条件见附页。[素材与许可](SOURCES-LICENSE.md)

```sh
python source/precise/huangpu-ruijin-207-historic-roof-ornament/source/paint.py
python source/precise/huangpu-ruijin-207-historic-roof-ornament/source/build_model.py --output historic-laboratory.glb
python source/precise/huangpu-ruijin-207-historic-roof-ornament/source/build_model.py --lod --output historic-laboratory-lod.glb
```
