# 黑石公寓弧形柱廊与原城外墙

在上海项目目录运行以下命令。量测使用 Python 3、NumPy、Shapely 以及支持 module.registerHooks 的 Node.js。signed-files.json 给出原城网格和三档柱廊模型的固定版本与文件摘要。程序用原照片的两根柱轴建立局部坐标，逐束保存柱廊表面和原城表面的交点，单位为米。

```sh
python source/precise/xuhui-blackstone-apartments-east-portico/measurements/city-contact/measure.py --project . --output portico-and-street.json
```

输出文件旁的 portico-and-street-rays.json.gz 保存三档全部4005束测线。每档横向89点，垂直15层。三维地块远档只取原2369，近档取柱对周围16米的真实三角网。再用四个建筑高度的闭合截面检查15个原户，分别统计柱脚、柱身、弯檐和石栏的面积与间隔。原图的两个端柱轴见 footprint-review.json，详细出处见 reference-review.json。
