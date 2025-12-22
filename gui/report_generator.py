"""
DeepFocus HTML 报告生成器 v3.0

生成美观的识别结果报告，包含：
- 概览统计（饼图/柱状图）
- 目标人脸信息
- 场景分析结果
- 处理参数记录
"""

import os
import base64
import cv2
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 检测jinja2是否可用
_JINJA2_AVAILABLE = False
try:
    from jinja2 import Template
    _JINJA2_AVAILABLE = True
except ImportError:
    logger.warning("jinja2 未安装，HTML报告功能不可用。安装命令: pip install jinja2")


def is_report_available() -> bool:
    """检查报告生成功能是否可用"""
    return _JINJA2_AVAILABLE


def image_to_base64(image: np.ndarray, format: str = "jpg", quality: int = 85) -> str:
    """
    将OpenCV图像转换为Base64字符串
    
    Args:
        image: BGR格式的OpenCV图像
        format: 图像格式 ("jpg" 或 "png")
        quality: JPEG质量 (0-100)
    
    Returns:
        Base64编码的图像字符串
    """
    if image is None:
        return ""
    
    if format.lower() == "png":
        _, buffer = cv2.imencode('.png', image)
        mime_type = "image/png"
    else:
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        mime_type = "image/jpeg"
    
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:{mime_type};base64,{b64_str}"


# HTML模板（内嵌，无需外部文件）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepFocus 识别报告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --primary: #007AFF;
            --success: #34C759;
            --warning: #FF9500;
            --danger: #FF3B30;
            --bg: #F5F5F7;
            --card-bg: #FFFFFF;
            --text: #1D1D1F;
            --text-secondary: #86868B;
            --border: #E5E5EA;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--primary), #5856D6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header .subtitle {
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        .card {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .card-title::before {
            content: '';
            width: 4px;
            height: 20px;
            background: var(--primary);
            border-radius: 2px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }
        
        .stat-item {
            text-align: center;
            padding: 20px;
            background: var(--bg);
            border-radius: 12px;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            color: var(--primary);
        }
        
        .stat-value.success { color: var(--success); }
        .stat-value.warning { color: var(--warning); }
        .stat-value.danger { color: var(--danger); }
        
        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            margin-top: 4px;
        }
        
        .target-section {
            display: flex;
            gap: 24px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .target-image {
            width: 120px;
            height: 120px;
            object-fit: cover;
            border-radius: 12px;
            border: 3px solid var(--primary);
        }
        
        .target-info {
            flex: 1;
            min-width: 200px;
        }
        
        .target-info p {
            margin-bottom: 8px;
            color: var(--text-secondary);
        }
        
        .target-info strong {
            color: var(--text);
        }
        
        .scene-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .scene-item {
            background: var(--bg);
            border-radius: 12px;
            overflow: hidden;
        }
        
        .scene-image {
            width: 100%;
            max-height: 350px;
            height: auto;
            object-fit: contain;
            background: var(--bg);
        }
        
        .scene-info {
            padding: 16px;
        }
        
        .scene-name {
            font-weight: 600;
            margin-bottom: 8px;
            word-break: break-all;
        }
        
        .scene-stats {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }
        
        .scene-stat {
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        .scene-stat span {
            font-weight: 600;
            color: var(--text);
        }
        
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .badge-success { background: rgba(52, 199, 89, 0.15); color: var(--success); }
        .badge-warning { background: rgba(255, 149, 0, 0.15); color: var(--warning); }
        .badge-danger { background: rgba(255, 59, 48, 0.15); color: var(--danger); }
        
        .chart-container {
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }
        
        .chart-box {
            flex: 1;
            min-width: 280px;
            max-width: 400px;
        }
        
        .params-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .params-table th,
        .params-table td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }
        
        .params-table th {
            color: var(--text-secondary);
            font-weight: 500;
            width: 40%;
        }
        
        .footer {
            text-align: center;
            color: var(--text-secondary);
            font-size: 13px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .scene-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <h1>🎯 DeepFocus 识别报告</h1>
            <p class="subtitle">生成时间: {{ report_time }}</p>
        </div>
        
        <!-- 概览统计 -->
        <div class="card">
            <div class="card-title">概览统计</div>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">{{ total_scenes }}</div>
                    <div class="stat-label">处理场景数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ total_faces }}</div>
                    <div class="stat-label">检测人脸数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value success">{{ total_matches }}</div>
                    <div class="stat-label">匹配成功数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value warning">{{ match_rate }}%</div>
                    <div class="stat-label">匹配率</div>
                </div>
            </div>
        </div>
        
        <!-- 图表 -->
        <div class="card">
            <div class="card-title">数据可视化</div>
            <div class="chart-container">
                <div class="chart-box">
                    <canvas id="pieChart"></canvas>
                </div>
                <div class="chart-box">
                    <canvas id="barChart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 目标人脸 -->
        {% if target_images %}
        <div class="card">
            <div class="card-title">目标人脸</div>
            <div class="target-section">
                {% for target in target_images %}
                <img src="{{ target.image_b64 }}" class="target-image" alt="目标人脸">
                {% endfor %}
                <div class="target-info">
                    <p>目标照片数: <strong>{{ target_images|length }}</strong></p>
                    <p>特征向量数: <strong>{{ total_encodings }}</strong></p>
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- 场景结果 -->
        {% if scenes %}
        <div class="card">
            <div class="card-title">场景分析结果</div>
            <div class="scene-grid">
                {% for scene in scenes %}
                <div class="scene-item">
                    <img src="{{ scene.image_b64 }}" class="scene-image" alt="{{ scene.name }}">
                    <div class="scene-info">
                        <div class="scene-name">{{ scene.name }}</div>
                        <div class="scene-stats">
                            <div class="scene-stat">检测: <span>{{ scene.total }}</span>人</div>
                            <div class="scene-stat">匹配: <span>{{ scene.matches }}</span>人</div>
                            <div class="scene-stat">距离: <span>{{ scene.best_dist }}</span></div>
                            <div class="scene-stat">耗时: <span>{{ scene.time }}s</span></div>
                        </div>
                        <div style="margin-top: 8px;">
                            {% if scene.matches > 0 %}
                            <span class="badge badge-success">✓ 找到目标</span>
                            {% else %}
                            <span class="badge badge-danger">✗ 未找到</span>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <!-- 处理参数 -->
        <div class="card">
            <div class="card-title">处理参数</div>
            <table class="params-table">
                <tr><th>检测模型</th><td>{{ params.model }}</td></tr>
                <tr><th>匹配阈值</th><td>{{ params.tolerance }}</td></tr>
                <tr><th>上采样</th><td>{{ params.upsample }}</td></tr>
                <tr><th>CLAHE增强</th><td>{{ "启用" if params.use_clahe else "禁用" }}</td></tr>
                <tr><th>Gamma校正</th><td>{{ params.gamma }}</td></tr>
                <tr><th>GPU加速</th><td>{{ "是" if params.cuda_used else "否" }}</td></tr>
            </table>
        </div>
        
        <!-- 页脚 -->
        <div class="footer">
            <p>由 DeepFocus Pro v3.0 最终版 生成 | © 2024 DeepFocus Team</p>
        </div>
    </div>
    
    <script>
        // 饼图 - 匹配统计
        new Chart(document.getElementById('pieChart'), {
            type: 'doughnut',
            data: {
                labels: ['匹配成功', '未匹配'],
                datasets: [{
                    data: [{{ total_matches }}, {{ total_faces - total_matches }}],
                    backgroundColor: ['#34C759', '#FF3B30'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: '匹配统计' }
                }
            }
        });
        
        // 柱状图 - 各场景检测数
        new Chart(document.getElementById('barChart'), {
            type: 'bar',
            data: {
                labels: [{% for scene in scenes %}'{{ scene.name[:15] }}'{% if not loop.last %},{% endif %}{% endfor %}],
                datasets: [
                    {
                        label: '检测数',
                        data: [{% for scene in scenes %}{{ scene.total }}{% if not loop.last %},{% endif %}{% endfor %}],
                        backgroundColor: '#007AFF'
                    },
                    {
                        label: '匹配数',
                        data: [{% for scene in scenes %}{{ scene.matches }}{% if not loop.last %},{% endif %}{% endfor %}],
                        backgroundColor: '#34C759'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: { display: true, text: '各场景统计' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>
"""


class ReportGenerator:
    """
    HTML报告生成器
    
    用法:
        generator = ReportGenerator()
        generator.set_targets(target_images, encoding_count)
        generator.add_scene_result(image, stats, path)
        generator.set_params(params)
        generator.generate("report.html")
    """
    
    def __init__(self):
        self.target_images: List[Dict] = []
        self.total_encodings: int = 0
        self.scenes: List[Dict] = []
        self.params: Dict = {}
    
    def set_targets(self, images: List[np.ndarray], encoding_count: int):
        """
        设置目标人脸信息
        
        Args:
            images: 目标人脸裁剪图列表
            encoding_count: 特征向量总数
        """
        self.target_images = []
        for img in images:
            self.target_images.append({
                "image_b64": image_to_base64(img, "jpg", 80)
            })
        self.total_encodings = encoding_count
    
    def add_scene_result(self, image: np.ndarray, stats: Dict, path: str):
        """
        添加场景识别结果
        
        Args:
            image: 标注后的结果图像
            stats: 统计信息字典
            path: 场景文件路径
        """
        # 缩小图像以减少报告大小
        h, w = image.shape[:2]
        max_dim = 800
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        self.scenes.append({
            "name": os.path.basename(path),
            "image_b64": image_to_base64(image, "jpg", 75),
            "total": stats.get("total", 0),
            "matches": stats.get("matches", 0),
            "best_dist": f"{stats.get('best_dist', 1.0):.3f}",
            "time": f"{stats.get('process_time', 0.0):.2f}"
        })
    
    def set_params(self, params: Dict):
        """设置处理参数"""
        self.params = {
            "model": params.get("model", "unknown").upper(),
            "tolerance": params.get("tolerance", 0.45),
            "upsample": params.get("upsample", 1),
            "use_clahe": params.get("use_clahe", True),
            "gamma": params.get("gamma", 1.0),
            "cuda_used": params.get("cuda_used", False)
        }
    
    def generate(self, output_path: str) -> bool:
        """
        生成HTML报告
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """
        if not _JINJA2_AVAILABLE:
            logger.error("jinja2 未安装，无法生成报告")
            return False
        
        try:
            # 计算统计数据
            total_scenes = len(self.scenes)
            total_faces = sum(s["total"] for s in self.scenes)
            total_matches = sum(s["matches"] for s in self.scenes)
            match_rate = round(total_matches / total_faces * 100, 1) if total_faces > 0 else 0
            
            # 渲染模板
            template = Template(HTML_TEMPLATE)
            html_content = template.render(
                report_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                total_scenes=total_scenes,
                total_faces=total_faces,
                total_matches=total_matches,
                match_rate=match_rate,
                target_images=self.target_images,
                total_encodings=self.total_encodings,
                scenes=self.scenes,
                params=self.params
            )
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"报告已生成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return False
    
    def clear(self):
        """清空所有数据"""
        self.target_images = []
        self.total_encodings = 0
        self.scenes = []
        self.params = {}

