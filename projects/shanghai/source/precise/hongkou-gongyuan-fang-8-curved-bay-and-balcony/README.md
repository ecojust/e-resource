# 公园坊8号弧窗与退台阳台

西江湾路476弄8号二层有三扇窄高窗。红色窗框各有一道横向中梃和细竖梃，三块浅色窗楣、窄窗台随砖墙转过弧面。上方阳台的曲形挑檐分为浅色缘带与偏红的下缘，铁栏后方另有一排向内退的玻璃窗。模型截在二层窗台以下少量砖皮，窗后进深与檐端厚度采用图像估值。[两机位模型图](../../../data/audit/gongyuan-fang-8-curved-bay-and-balcony-v1/photo-review/two-views.jpg)

## 照片与户号

2019年9月16日刊登的图07题为“公园坊8号现状”。图08从同一弄内偏侧的位置拍摄，两图的绿色门牌均可辨出8号。两图可交叉核对左侧石粒墙窗、三层曲栏外轮廓及后方直线窗。图08中花木与晾晒物遮住二层窗口下半部，所以三窗的分格以图07为主。另有2017年的报道记述连横一家在8号的居住往事。24号另有野风画会旧址。[图07](https://boot-img.xuexi.cn/contribute_img/20190912160103/30762293038669391.jpg) · [图08](https://boot-img.xuexi.cn/contribute_img/20190912160103/30762333466312830.jpg) · [门牌及图源记录](measurements/2019-views-and-address.json) · [解放日报报道](https://www.jfdaily.com/wx/detail.do?id=65384)

## 几何与核验

以二层窗台为高度原点，拟合把可辨砖皮的名义高度设为63毫米，窗洞约宽0.80米、高1.58米，栏顶约高出阳台板0.94米。这处局部没有实地尺寸。栏杆花饰的遮挡段参照可见段续接，曲墙半径及阳台退距随尺度假设变化。图07采用24个标点拟合，重投中位2.27像素，另留出的6个窗横梃端点中位偏差2.97像素。图08采用10个标点，中位3.66像素，最大16.39像素。两机的檐口另有12个天空边缘采点。[相机、标点与逐点误差](measurements/bay-camera-fit.json)

三档分别在原始与独立解码的成品三角网上，对同一组64个原像位置从相机发射射线。每档有56个位置首先击中预期材质。其余8处中，7处预选的细铁线位置先看见后方封窗，距离最近可见铁件1至5.1像素；图08另有1处落在窗侧砖墙。所有首交、偏移及坐标均可复算。[原网结果](../../../data/audit/gongyuan-fang-8-curved-bay-and-balcony-v1/photo-review/raw.json) · [解码近网结果](../../../data/audit/gongyuan-fang-8-curved-bay-and-balcony-v1/photo-review/near.json) · [解码远网结果](../../../data/audit/gongyuan-fang-8-curved-bay-and-balcony-v1/photo-review/far.json)

原始网与近档均有14,416个三角面，远档有8,344个。按建模分组，近档73组、远档70组可分别选取。每个实体分别核过面面积、共享棱朝向和正体积。[可编辑部件](source/curved_bay.py) · [闭体检验](../../../data/audit/gongyuan-fang-8-curved-bay-and-balcony-v1/photo-review/editable-parts.json) · [使用许可](SOURCES-LICENSE.md)
