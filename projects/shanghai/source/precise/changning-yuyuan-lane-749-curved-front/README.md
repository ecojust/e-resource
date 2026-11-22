# 2018年署名「愚园路749弄65号」照片中的灰色弧面住宅

Antigng于2018年2月13日拍摄了一处灰色水刷石住宅转角，原文件题为「愚园路749弄65号住宅」。长宁区规划资源局2012年公布的65号档案图中，圆角却是连续红砖实墙，带有两道浅色横带。两张照片可见的窗列和饰面都不同，目前无法确定是同栋不同面还是不同建筑。本页据2018年照片制作，保留门牌疑问。[打开照片研究模型](../../../yuyuan-lane-749-curved-front.html) · [2018年原照裁切](measurements/antigng-rounded-street-front.jpg) · [2012年区级原页](https://www.shcn.gov.cn/col7698/20211207/1151493.html) · [两幅资料的差异](measurements/district-comparison-source.json)

模型截取照片中转角处的三个开间，保留六樘窗、弯曲檐带及左侧外挂机。上层中央钢窗有四列玻璃，下层中央的两扇金属窗同时外开。前景街线遮住了下层窗的中部，窗扇开启状态按图上仍可见的八个角估算。左、右开启角约为15度和16度，分别形成浅色、深色反光面。[转角并置图](study-views/rounded-front-in-2018.jpg) · [上层钢窗](study-views/blue-steel-window.jpg) · [下层两扇外开窗](study-views/lower-outward-casements.jpg) · [窗扇角点](measurements/lower-casement-fit.json)

## 曲面与砖缝

以照片记录的28毫米等效焦距为初值，用上、下窗洞角点和九个檐顶位置估计相机与弧墙。在中央上层窗洞净高取1.60米的条件下，拟合半径约4.63米。另取54列天空和檐口交界处的像素，逐列比对近、远景导出的压顶。两档轮廓的均方根偏差折回原照片后均约为4.84像素。半径与窗高仍待实测。[相机与曲面拟合](measurements/curved-corner-camera.json) · [檐口独立剖面](measurements/independent-coping-profile.json)

左开间和中央开间之间的窄砖带保留了39道可读水平灰缝，相邻间距中位数约9.68厘米。38层砖皮中，交替出现的19层均能读出两道明显的竖缝。近、远景均按这一顺序安排整砖面和带两道竖缝的短砖面。水刷石纹理采用程序生成，按圆弧长度和高度展开，窗洞内侧按进深展开。[砖皮的实照测量](measurements/vertical-brick-pier.json) · [嵌砖近照与模型](study-views/full-and-divided-brick-courses.jpg)

## 模型与定位

近景有21,424个三角面、116个可编辑组，远景有16,624个三角面、102个可编辑组。源网、近景和远景各经过336次实体检查，两档各有七张视图。[源程序](source/build_model.py) · [实体检查](../../../data/audit/yuyuan-lane-749-curved-front-v1/preflight/geometry-rays.json) · [弧面纹理尺度](../../../data/audit/yuyuan-lane-749-curved-front-v1/preflight/render-uv.json)

原照片保存的GPS位置只精确到整角秒。周围有多个既有房屋轮廓，邻号和航空图都不足以确定这段弧墙的起止点。模型单独展示，主图保留原有房屋。[照片、全景与旧城轮廓](measurements/final-position-from-city-and-roofs.json) · [来源与许可](SOURCES-LICENSE.md)
