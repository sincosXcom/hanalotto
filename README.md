# hanalotto
Hanafuda+Korea Lotto

# 花图乐透 · 选号器

基于 Streamlit 的韩国花图风格乐透号码查看与选号工具。

## 功能
- 查看往期开奖号码（图案 + 数字）
- 左右按钮 / 滑块切换期数
- 左侧边栏独立查询任意期数
- 基于历史频率的娱乐预测
- 点击花图下方的复选框选号（最多6个），支持保存

## 安装与运行
1. 安装依赖：`pip install -r requirements.txt`
2. 准备数据：将 `klotto.csv` 放入 `data/` 目录，花图图片放入 `images/`（命名 `1.png` ~ `45.png`）
3. 运行：`streamlit run hanafuda.py`

## 数据格式要求
CSV 需包含列：`issue, date, n1, n2, n3, n4, n5, n6, special`（或韩文列名自动映射）

Demo link
https://hanafuda.streamlit.app/
