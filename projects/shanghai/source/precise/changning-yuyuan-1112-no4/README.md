# 愚园路1112弄4号蒋光鼐旧居

长宁区规划资源局记载两栋住宅同建于1928年，合占地1321平方米。4号建筑面积897平方米，20号853平方米。上海市房屋管理局第三批名录编号3M009同时列出这两个门牌。2019年的愚园路踏查将蒋光鼐旧居明确到4号。[区规划资源局档案](https://www.shcn.gov.cn/col7698/20211207/1152658.html) · [上海市优秀历史建筑名录](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) · [愚园路踏查](https://www.sohu.com/a/318121827_781305)

2011年12月4日12时24分拍摄的弄内斜照，门墙上能读出绿色的4号牌。正对相机的弧形墙头、它右侧的窄凹间、再往右凸出的三窗宽侧翼，在2020年2月从愚园路拍的正面街景中均可辨认。区规划资源局还保存了另一张独立角度的照片，能看到弧形墙头的压顶、铁窗以及相邻的折墙。2012与2021年区局页面复用同一张照片。[2011年实地摄影原件](https://a2-q.mafengwo.net/s1/M00/C7/B6/wKgBm07esLfIQ1biAAGNiSj3xTI64.jpeg) · [带图片上下文的转载](https://bbs.wenxuecity.com/rdzn/3860710.html) · [区局照片原件](https://static.shcn.gov.cn/cncms/gtj/20101230182350279694059.jpg)

首个可编辑构件组覆盖凸翼的两个外墙面。南面上层是三樘带折肩的窗，下层是三樘缓拱窗。西返墙有两道窄窗、上层带折肩的宽窗、下层缓拱窗。墙体保留净洞、窗洞侧壁和退进的窗框，每个窗格、窗台和檐带都能在生成器中定位。首稿暂定的标高已由六个街景站位校正，现有模型将腰带顶置于街面以上约5.25米，主檐唇12.62米，檐宽9.71米，东西券窗中轴相距5.01米。六站共41个观察，中位重投影残差1.98像素。留一站重算的檐高范围11.25–13.20米，院内外地坪高差未知。临街围墙与北栋20号另行辨认。[窗洞读点](source/window-readings.json) · [斜照轴线与残差](source/camera-2011.json)

第二阶段补录了弄侧四组不同节奏的窗洞、较低的楼梯间开窗、横腰线及两根落水管。弄侧山墙的曲线在2011年原照中完整，门外侧另一片弧墙用区局照片补上取景之外的顶段，两片曲线单独重建。2015年11月16日的另一组步行摄影确认了4号牌、公告箱和右侧铁门的位置。[六站约束](measurements/forward-wing-constrained.json) · [两片弧墙](source/lane-and-crown-readings.json) · [2015年原照题签](measurements/november-2015-walk.json)

下列命令在仓库根目录生成两个细度。需要 Python、NumPy、Shapely 及仓库的建筑几何工具。

```sh
python projects/shanghai/source/precise/changning-yuyuan-1112-no4/source/build_model.py --output /tmp/yuyuan-4.glb
python projects/shanghai/source/precise/changning-yuyuan-1112-no4/source/build_model.py --lod --output /tmp/yuyuan-4-lod.glb
```

原创几何及代码按仓库 MIT 许可发布。参考相片版权归原作者及提供方，源包保留出处、日期、哈希、像素控制与尺寸判断。
