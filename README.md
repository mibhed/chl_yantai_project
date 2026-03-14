# 烟台近岸海域叶绿素a遥感分析与可视化系统

## 项目定位
本项目参考黄河口邻近海域叶绿素a机器学习反演论文的方法框架，
在没有烟台本地原位 Chl-a 数据的前提下，采用“论文方法复现 + 区域迁移应用”的思路，
构建烟台近岸海域叶绿素a遥感分析与可视化系统。

## 项目目标
1. 复现多波段遥感特征 + 特征降维 + 机器学习回归的流程
2. 将模型框架迁移应用到烟台近岸区域
3. 实现叶绿素a时空分析与可视化展示

## 目录结构
- data/raw: 原始数据
- data/processed: 预处理后数据
- data/samples: 样本表
- src: 核心代码
- app: Streamlit 可视化页面
- outputs/figures: 图表输出
- outputs/maps: 地图输出
- outputs/reports: 报告输出

## 当前阶段
第一阶段：项目初始化与基础页面搭建

## 运行方式
```bash
source venv/bin/activate
streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501