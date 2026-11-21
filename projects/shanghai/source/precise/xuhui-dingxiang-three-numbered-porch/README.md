# 丁香花园三号楼门廊与弧形石阶

华山路849号丁香花园的三号楼建于1918年，曾作藏书楼。上海市登记表将三号楼单列为4D023。2015年的入口近照中，左侧木柱上挂着数字3。2024年发表的庭院照片也拍到了这块门牌，以及门廊背墙右边的弧顶门口。园内一号楼入口另有独立模型。[市级登记](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [2015年三号楼摄影记录](https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480102wgib.html) · [院内分栋照片](https://www.meipian.cn/4zzeigyo)

从院中登上五级弧形石阶，台阶逐级收窄。两侧上缘的红褐色扶手沿外弧展开，黑铁栏下方可见圆环和绞铁杆。柱脚镶有斜向浅色砖，柱身的窄木条留出透口。屋面红瓦下端是深绿色檐板。[入口与石阶尺寸假设](measurements/porch-and-steps.json) · [楼号与屋顶核对](measurements/building-identity.json)

门廊内的两种红色铺面在后门前相接；台阶上方，左侧铺面前缘装饰一列浅色菱形。木柱基部的粉色长条砖作人字拼，长椅扶手和吊灯收边均取自入口近照。[铺面、砖缝与廊内构件](measurements/entrance-finishes.json)

两张近照共同约束扶手与踏步。以靠楼端两根铁杆的间距为一，最外两杆间距约一点五；扶手走到一半时只展开约三成，越靠庭院越向外弯。最下级石阶在跨度为零点九的中段弦线上向院中鼓出约零点零七五。外侧被木栏遮挡的部分按切线延伸。[两机位控制点与误差](measurements/two-view-stair-and-rail.json)

在仓库根目录重建门廊及其可编辑 Blender 工程。

```sh
python projects/shanghai/source/precise/xuhui-dingxiang-three-numbered-porch/source/build_model.py \
  --out out/dingxiang-three/assets --audit out/dingxiang-three/audit
```

[独立校核照片控制点](measurements/verify-stair-survey.py) · [手绘取点与镜位](measurements/two-view-stair-and-rail.json) · [来源及模型许可](SOURCES-LICENSE.md)

[门廊斜视](study-views/oblique-porch.jpg) · [五级弧阶与扶手](study-views/arc-steps.jpg) · [券洞与长椅](study-views/door-and-bench.jpg)
