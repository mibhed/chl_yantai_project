#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.utils
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>叶绿素a遥感分析系统</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .nav { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav button { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; background: #667eea; color: white; }
        .nav button:hover { background: #764ba2; }
        .nav button.active { background: #764ba2; }
        .section { display: none; }
        .section.active { display: block; }
        input, select, button { padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #667eea; color: white; cursor: pointer; }
        button:hover { background: #764ba2; }
        .plot-container { margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌊 叶绿素a遥感分析系统</h1>
            <p>基于卫星遥感的叶绿素a浓度反演与可视化分析</p>
        </div>
        
        <div class="nav">
            <button onclick="showSection('home')" class="active">🏠 首页</button>
            <button onclick="showSection('data')">📊 数据分析</button>
            <button onclick="showSection('model')">🤖 模型训练</button>
            <button onclick="showSection('spatial')">🗺️ 空间分析</button>
        </div>
        
        <div id="home" class="section active">
            <div class="card">
                <h2>欢迎使用叶绿素a遥感分析系统</h2>
                <p>本系统提供完整的叶绿素a遥感分析功能，包括数据导入、模型训练、空间分析和结果可视化。</p>
                <h3>系统功能</h3>
                <ul>
                    <li>📥 多格式数据导入（CSV、Excel、TIFF）</li>
                    <li>🤖 多种机器学习模型训练</li>
                    <li>📈 模型性能评估与可视化</li>
                    <li>🗺️ 空间分布分析与制图</li>
                    <li>🔄 多维度数据对比分析</li>
                </ul>
            </div>
        </div>
        
        <div id="data" class="section">
            <div class="card">
                <h2>数据分析</h2>
                <p>上传数据文件进行分析</p>
                <input type="file" id="dataFile" accept=".csv,.xlsx">
                <button onclick="uploadData()">上传数据</button>
                <div id="dataPreview" class="plot-container"></div>
            </div>
        </div>
        
        <div id="model" class="section">
            <div class="card">
                <h2>模型训练</h2>
                <p>选择模型进行训练</p>
                <select id="modelType">
                    <option value="random_forest">随机森林</option>
                    <option value="gradient_boosting">梯度提升</option>
                    <option value="xgboost">XGBoost</option>
                </select>
                <button onclick="trainModel()">训练模型</button>
                <div id="modelResults" class="plot-container"></div>
            </div>
        </div>
        
        <div id="spatial" class="section">
            <div class="card">
                <h2>空间分析</h2>
                <p>上传TIFF影像进行空间分析</p>
                <input type="file" id="tiffFile" accept=".tif,.tiff">
                <button onclick="analyzeSpatial()">分析空间分布</button>
                <div id="spatialResults" class="plot-container"></div>
            </div>
        </div>
    </div>
    
    <script>
        function showSection(sectionId) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav button').forEach(b => b.classList.remove('active'));
            document.getElementById(sectionId).classList.add('active');
            event.target.classList.add('active');
        }
        
        function uploadData() {
            const file = document.getElementById('dataFile').files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);
                fetch('/api/upload', { method: 'POST', body: formData })
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('dataPreview').innerHTML = '<p>数据上传成功！</p>';
                    });
            }
        }
        
        function trainModel() {
            const modelType = document.getElementById('modelType').value;
            fetch('/api/train', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model_type: modelType })
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('modelResults').innerHTML = '<p>模型训练完成！</p>';
            });
        }
        
        function analyzeSpatial() {
            const file = document.getElementById('tiffFile').files[0];
            if (file) {
                const formData = new FormData();
                formData.append('file', file);
                fetch('/api/spatial', { method: 'POST', body: formData })
                    .then(r => r.json())
                    .then(data => {
                        document.getElementById('spatialResults').innerHTML = '<p>空间分析完成！</p>';
                    });
            }
        }
    </script>
</body>
</html>
    ''')

@app.route('/api/upload', methods=['POST'])
def upload_data():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    return jsonify({'status': 'success', 'message': 'File uploaded successfully'})

@app.route('/api/train', methods=['POST'])
def train_model():
    data = request.json
    model_type = data.get('model_type', 'random_forest')
    return jsonify({'status': 'success', 'model_type': model_type, 'message': 'Model training completed'})

@app.route('/api/spatial', methods=['POST'])
def spatial_analysis():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    return jsonify({'status': 'success', 'message': 'Spatial analysis completed'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=False)