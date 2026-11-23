# 开普敦公寓

开普敦公寓建于1940年，位于武康路240至246号双号。上海市第五批优秀历史建筑将它登记为5D011。1947年的《上海行号路图录》将240号的三角形街屋与230号的国富门公寓分别标出。两栋都参加了近年的修缮。徐汇区刊出的两组照片可以依窗列和屋角分辨各自的街面。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [徐汇通修缮报道及档案图](https://sghexport.shobserver.com/html/baijiahao/2024/01/22/1239744.html)

南端把尖角收成了圆弧，二至四层在弧墙上沿各开一道横窗。紧邻弧墙的三扇小方窗各有突出墙面的圆形窗套，三个环口自上而下排成一列。街面中部则是六列钢窗的浅凸出面，两侧保留较窄的窗组。底层水刷石、斩假石勒脚及楼上水泥砂浆的分别有修缮记录。2017年《武康路》书摘将设计归于公和洋行。[《武康路》书摘](https://www.thepaper.cn/newsDetail_forward_1848806)

## 建模依据

立面开口取自城建档案馆图。发布报道中的图4为修缮前街面，图6为档案立面，图9为修缮后实照。两张实照按圆窗中心、窗头和女儿墙转折分别配准，像点及逐点残差可下载。2015与2020年的沿街照片提供南角、窗列和同邻楼接缝的独立对照。2022年12月的街面受脚手架遮挡。原照片由各自权利人持有，此工程中的立面对照图由三维网格投影生成。[图目、来源和署名](measurements/documentary-sources.json) · [两张实照的配准](measurements/two-registered-street-photos.json) · [独立年代记载](measurements/independent-street-observations.json)

前后檐围闭的三角形平屋面参考1947年街廓图。后墙及屋顶背侧在公开照片中多有遮挡，因此只收轮廓。楼内各户、底层以后的房间和邻楼另属其他范围。全部模型构件和两幅材质贴图为本项目原创，以MIT许可发布。[原创建模图](../../../data/audit/capetown-apartments-wukang-road-wedge-v1/street-and-plan.jpg)

沿街长度采用2015年4月和2020年2月三个独立街站对南端圆角、北侧接缝的交会，取21.60米，估计误差约1.3米。单从1947年粗线轮廓和二手资料记载的126.7平方米反推，约为21.85米。依实取街长和近似三角形取最大进深11.73米；14.48米的街面主檐高度由档案图正立面的比例换算。进深、窗套凸出和墙厚仍是形貌复原估值。[1947年轮廓像点](measurements/plot-1947.json) · [街站与交会](measurements/street-front-and-parcel.json)

带原尺寸相机的修缮前、后两张照片，分别留有20处及17处配准点。中位重投偏差为3.17与5.55像素，最大为18.62与13.14像素。近景、压缩解码近景和解码远景的103个档案断面取点均命中预期材料。原片各15处独立取点，前期命中14处、后期12处。两处街墙取点最初碰到同面的楼板边，楼板内收到墙内侧后，两处均命中水泥抹面。逐点报告保留钢梃、灰色窗套与墙面交界的四处偏差。[原始网格的逐射线结果](../../../data/audit/capetown-apartments-wukang-road-wedge-v1/raw-street-rays.json)

## 源文件和模型

[普通预览页](../../../capetown-apartments-wukang-road-wedge.html)提供九个机位、近远两级和可下载的原始网格、网页近景、远景与Blender编辑稿。可编辑稿包含钢窗竖梃、横档、玻璃、圆套、弧墙和分层涂面。两幅材质纹理已打包进工程。总览、屋顶和俯视三镜按整网外缘核过画幅，俯视中心设在实际屋盖标高。

在本项目的上海目录中，运行以下命令可重建网格、校核闭合和压缩、制作编辑工程。程序沿用同目录其他建筑共享的网格写入器、解码器和Blender校核工具。

```sh
source_dir=source/precise/xuhui-capetown-apartments-wukang-road-wedge
python "$source_dir/measurements/check_mesh.py" out/geometry
python "$source_dir/source/package_model.py" out/geometry out/models --gltfpack gltfpack
python "$source_dir/source/package_editable.py" prepare out/models out/native
python "$source_dir/source/package_editable.py" run out/models out/native
```
