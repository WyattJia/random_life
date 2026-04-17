# random_life

## random_destination

用 `uv` 创建并安装依赖：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

运行默认配置（以上海为圆心，半径 600 公里）：

```bash
.venv/bin/python random_destination.py '全国县级以上地名代码及经纬度.csv'
```

默认只会在第三级行政单位中抽取，也就是区、县、县级市这一层。

自定义筛选范围、圆心和权重：

```bash
.venv/bin/python random_destination.py '全国县级以上地名代码及经纬度.csv' \
  --max-distance 300 \
  --reference-coords 30.2741,120.1551 \
  --province-weights '浙江省:0.4,江苏省:0.8,上海市:0.6'
```

刷新地名数据：

```bash
uv pip install --python .venv/bin/python py7zr
.venv/bin/python scripts/repair_place_data.py
```
