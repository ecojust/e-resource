# 杨树浦救火会旧望塔圆眼与敞亭塔冠

上海市房屋管理局第五批优秀历史建筑名录将杨树浦路1307号登记为「公共租界杨树浦救火会旧址」，编号5G010，原编YP-J-010-V。杨浦区融媒体中心刊载的历史照片在「杨树浦救火会」图题下拍到方塔的两面。模型取自该照，截取下部两块矩形饰面以上的塔身、两道挑檐与旧亭帽。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [杨浦区融媒体中心旧照与图题](https://m.thepaper.cn/newsDetail_forward_19513921)

区刊记载，工部局于1921年购地建立杨树浦桥救火会。文章所记31.5米是整座历史望塔的高度。2020年上海发布的文章另记1982年邻近禽蛋三厂屋顶新建了一座55米高塔，两项高度描述的对象不同。旧照片的曝光时间和旧冠改建年代仍待考。[区刊旧照](https://m.thepaper.cn/newsDetail_forward_19513921) · [上海发布的历史沿革](https://finance.sina.com.cn/jjxw/2020-11-07/doc-iiznezxs0487916.shtml)

## 照片能辨认的部分

朝向相机的宽面有带横竖细梃的圆眼，右侧返面也有圆眼，照片只把它记录成暗面。两面均见浅拱线框、下部矩形饰面和塔冠挑出的暗檐。小亭的深色开口、窄柱和多面帽檐可以从旧照片辨出。低角度观看，四处暗孔的视线在柱后首中亭帽底面。未入镜的两个侧面采用平整收边。亭帽背侧采用八边对称补全，细缝、颜色和小亭的实际边数均缺少可量的同年代资料。

Fayhoo的具名照片在2015年4月6日16时04分摄于此址。照片里方塔仍在，顶部已有封闭亭身。作品使用旧照的敞亭样式。杨途所供黑白照片保留在原文，2015年照片的许可为CC BY-SA 3.0。本模型的矿物纹理和金属面的细纹由程序生成。[Fayhoo原图与许可](https://commons.wikimedia.org/wiki/File:Gonggongzujie_Yangshupujiuhuohui_Jiuzhi.JPG)

## 比例与复核

作者以方塔身外宽为一个展示单位。2022年文章中的旧图为1080×768像素。两面方檐的六个角点、三个竖棱位置和圆眼近似居中的条件共同给出局部透视。最高点、下方饰面底边及其暗部的进深主要靠此一视角，缺少换算成现场绝对尺寸的资料。40个像点按各自的可见材料检验，分别求原网、网页近景独立解码和远景独立解码的首次交点。首轮35处相符，剩余五点分布在亭帽和柱间。将帽下的反影底面与深色帽边单独成件后，三档各40处相符。[图像坐标与镜头灵敏度](measurements/historical-crown-camera.json) · [三档首交结果](../../../data/audit/yangshupu-fire-brigade-historic-tower-crown-v1/historical-image-rays.json) · [首轮逐点结果](../../../data/audit/yangshupu-fire-brigade-historic-tower-crown-v1/first-study-image-rays.json)

## 重建

从上海项目根目录运行。gltfpack负责压缩。替换WORK、OUT、AUDIT、NATIVE为本次数据目录。原生版分别保留饰面、圆眼、柱和亭帽，可独立编辑。

~~~sh
python source/precise/yangpu-yangshupu-fire-brigade-historic-tower-crown/measurements/register_historic.py
python source/precise/yangpu-yangshupu-fire-brigade-historic-tower-crown/measurements/package_models.py WORK OUT AUDIT --gltfpack gltfpack
python source/precise/yangpu-yangshupu-fire-brigade-historic-tower-crown/source/build_blender_source.py prepare WORK/full-source.glb NATIVE
python source/precise/yangpu-yangshupu-fire-brigade-historic-tower-crown/source/build_blender_source.py run WORK/full-source.glb NATIVE
~~~
