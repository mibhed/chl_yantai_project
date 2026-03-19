#!/bin/bash

echo "========================================="
echo "  烟台叶绿素a遥感分析系统 - 项目初始化"
echo "========================================="
echo ""

# 项目根目录
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 需要创建的文件夹
declare -a FOLDERS=(
    "data/raw"
    "data/processed"
    "data/samples"
    "outputs/figures"
    "outputs/maps"
    "outputs/reports"
    "outputs/models"
    "tests"
    "logs"
)

# 创建文件夹函数
create_folder() {
    local folder=$1
    local full_path="$PROJECT_DIR/$folder"

    if [ -d "$full_path" ]; then
        echo "  ✓ $folder 已存在"
    else
        mkdir -p "$full_path"
        echo "  ✓ 创建 $folder"
    fi
}

# 创建 README 函数
create_readme() {
    local folder=$1
    local full_path="$PROJECT_DIR/$folder/README.md"
    local folder_name=$(basename "$folder")

    if [ -f "$full_path" ]; then
        echo "  ✓ $folder/README.md 已存在"
    else
        case $folder_name in
            "raw")
                cat > "$full_path" << 'EOF'
# 原始数据目录

本目录用于存放原始遥感数据文件。

## 文件格式

- 支持格式：CSV, NetCDF, HDF, TIFF
- 命名规范：`{卫星}_{区域}_{时间}.{格式}`

## 数据来源

- MODIS海洋水色数据
- SeaWiFS数据
- VIIRS数据
EOF
                ;;
            "processed")
                cat > "$full_path" << 'EOF'
# 预处理数据目录

本目录用于存放经过预处理的数据文件。

## 处理流程

1. 数据清洗
2. 质量控制
3. 坐标系转换
4. 辐射定标

## 输出格式

- CSV格式（表格数据）
- TIFF格式（影像数据）
EOF
                ;;
            "samples")
                cat > "$full_path" << 'EOF'
# 样本数据目录

本目录用于存放训练和验证用的样本数据。

## 数据格式

必需列：
- `chl_a` - 叶绿素a浓度 (mg/m³)

特征列：
- Rrs_412, Rrs_443, Rrs_469, Rrs_488 (蓝光波段)
- Rrs_531, Rrs_547, Rrs_555 (绿光波段)
- Rrs_645, Rrs_667, Rrs_678 (红光波段)

可选列：
- ratio_443_555, ratio_488_555 (波段比值)
- diff_488_555, diff_555_645 (波段差值)
EOF
                ;;
            "figures")
                cat > "$full_path" << 'EOF'
# 图表输出目录

本目录用于存放生成的图表文件。

## 输出类型

- 散点图 (scatter)
- 误差直方图 (histogram)
- 时序图 (time series)
- 对比图 (comparison)
EOF
                ;;
            "maps")
                cat > "$full_path" << 'EOF'
# 地图输出目录

本目录用于存放生成的空间分布图。

## 输出格式

- PNG高清图
- TIFFGeoTIFF格式

## 包含内容

- 叶绿素a浓度空间分布
- 多区域对比图
EOF
                ;;
            "reports")
                cat > "$full_path" << 'EOF'
# 报告输出目录

本目录用于存放分析报告和模型评估结果。

## 输出文件

- model_comparison.csv - 模型对比
- best_model_predictions.csv - 预测结果
- monthly_series_*.csv - 月度数据
- multi_year_series_*.csv - 多年数据
- multi_region_series_*.csv - 多区域数据
EOF
                ;;
            "models")
                cat > "$full_path" << 'EOF'
# 模型保存目录

本目录用于存放训练好的模型文件。

## 模型格式

- joblib格式 (.joblib)
- pickle格式 (.pkl)

## 模型列表

| 模型名称 | 训练日期 | 性能(R²) |
|---------|---------|---------|
|         |         |         |
EOF
                ;;
            "tests")
                cat > "$full_path" << 'EOF'
# 测试目录

本目录用于存放项目测试文件。

## 测试类型

- 单元测试
- 集成测试
- 性能测试

## 运行测试

```bash
pytest tests/
```
EOF
                ;;
            "logs")
                cat > "$full_path" << 'EOF'
# 日志目录

本目录用于存放系统运行日志。

## 日志类型

- 应用日志
- 错误日志
- 访问日志
EOF
                ;;
        esac
        echo "  ✓ 创建 $folder/README.md"
    fi
}

echo "开始初始化项目结构..."
echo ""

# 创建所有文件夹
echo "1. 创建文件夹..."
for folder in "${Folders[@]}"; do
    create_folder "$folder"
done

# 重新定义数组（修复Bash数组问题）
for folder in "${FOLDERS[@]}"; do
    create_folder "$folder"
done

echo ""

# 创建所有README
echo "2. 创建README文件..."
for folder in "${FOLDERS[@]}"; do
    create_readme "$folder"
done

echo ""
echo "========================================="
echo "  初始化完成！"
echo "========================================="
echo ""
echo "项目结构："
tree -L 2 "$PROJECT_DIR/data" "$PROJECT_DIR/outputs" 2>/dev/null || find "$PROJECT_DIR/data" "$PROJECT_DIR/outputs" -maxdepth 2 -type d
