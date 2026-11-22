# 梁氏民宅的砖券铁花窗

山西北路457弄61号的院窗分为上下两层。高窗两侧各有一列回卷的铁花，下部短窗以环形花心为中心。木框上方，两层放射砖从两侧向中央键砖收拢。石窗台则向院内挑出，下接收腰的砖裙。[打开三维模型](../../../liang-residence-arched-iron-window.html) · [原照与模型并排](study-views/window-source-and-model.jpg) · [窗门原照](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E9%97%B8%E5%8C%97%E5%8C%BA%E5%B1%B1%E8%A5%BF%E5%8C%97%E8%B7%AF457%E5%BC%8461%E5%8F%B7%E4%B9%8B%E7%AA%97%E9%97%A8_-_panoramio.jpg)

## 照片与门牌

Aaron Zhu于2012年7月4日拍摄的照片明确题为“山西北路457弄61号之窗门”。他在2015年另外拍摄了梁宅山墙，画面中没有这扇窗。两照片分别用于辨认窗饰与门牌。市级第四批优秀历史建筑名录的4H005项为“梁氏民宅”。修建于1898年、二层砖木和占地223.59平方米的记述可追溯至《静安石库门》书目引文，未能核对该书页的原图。[原窗照片资料](measurements/window-photo-source.json) · [山墙照片资料](measurements/gable-photo-source.json) · [市表条目](measurements/listed-house.json)

建筑底图101与带有4H005编号的地图足印相交约209.1平方米，两轮廓交并比为97.77%。照片所示窗户在院内哪一段墙上仍待测绘，模型以独立院窗展示。[门牌、相邻宅及城市底图](measurements/site-and-owner-101.json)

## 怎样读出铁花

原图为3240 × 4320像素，镜头等效焦距26毫米。照片记录没有窗宽，模型以木框外宽约1.46米作尺度，拟合窗高约2.66米。先估计相机与窗所在的平面，再以四角作正面校正。校正图上的铁条中心线转成有宽度和厚度的独立金属截面，玻璃退进木框内。上窗右下有杂物遮挡，该处花纹参考了完整的左侧对称图案。[相机、尺度与角点](measurements/window-camera.json) · [上下层铁花中心线](measurements/iron-grille-traces.json) · [左右补画范围](measurements/trace-window-scrolls.py)

窗顶的双层砖券和三角键帽、石窗台的前缘和斜下沿分别建模。遮住砖券的电缆保留在参考照片中，砖缝的位置据未遮挡的区域推算。远景保留卷草中心线，铁条断面由八边简化为四边。在未参与建模的52处砖缝，原图与三档模型轮廓的最大偏差均小于1个校正图像素。墙后不可见的砌筑和铁条厚度为估计。[砖券与石台的测量](measurements/brick-surround.json) · [52处砖缝与10处表面核对](measurements/brick-surround-final-three-glbs.json) · [石台细部](study-views/sill.jpg)

另由参照照片选出19对开孔和相邻铁条位置，对应上下两层共38个独立点。三档模型的实际网格分别检验前景是否碰到铁条，又在木框范围内检查玻璃覆盖。铁条前后有真实间隙。对初稿发现的上框漏光，成品将玻璃边缘藏进木框，保住仰角下的视线。[独立取点](measurements/independent-window-apertures.json) · [三档首交结果](../../../data/audit/liang-residence-arched-iron-window-v1/preflight/iron-apertures.json) · [玻璃覆盖核查](../../../data/audit/liang-residence-arched-iron-window-v1/preflight/render-uv.json)

## 文件与再现

模型页提供原始、近景、远景 GLB 和可编辑 Blender 工程。受 Aaron Zhu 照片启发并据照片描出的铁花及成品模型按 CC BY-SA 3.0 共享，代码和程序生成的红木纹理按 MIT 许可分发。三维文件内附原图链接和署名。[来源及许可](SOURCES-LICENSE.md)

```sh
python source/build_model.py --output liang-iron-window.glb
python source/build_model.py --lod --output liang-iron-window-lod.glb
python source/build_model.py --blender blender --out ./exports --audit ./audit
```

为重算照片测量，将 `LIANG_WINDOW_PHOTO` 指向原始窗照，按顺序运行 `measurements/register-iron-window.py`、`measurements/trace-window-scrolls.py`。已有测量数据随仓库提供，重建资产可以直接使用。
