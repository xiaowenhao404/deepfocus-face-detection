"""
DeepFocus 集成测试脚本

测试所有8张场景图的识别效果
"""

import os
import sys
import logging
from datetime import datetime

# 检查依赖
try:
    from core.face_engine import FaceEngine
    from core.image_utils import save_image
    from core.matcher import compute_confidence, calculate_match_statistics
    print("[OK] 依赖检查通过\n")
except ImportError as e:
    print(f"[ERROR] 依赖库未安装: {e}")
    print("\n请先安装依赖:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def setup_logging():
    """配置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def test_all_scenes():
    """测试所有场景图"""
    print("="*70)
    print("  DeepFocus 集成测试 - 测试所有场景图")
    print("="*70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 创建引擎
    engine = FaceEngine(model_method='hog', tolerance=0.45)
    print(f"\n[配置] 检测模型: HOG")
    print(f"[配置] 匹配阈值: 0.45")
    print(f"[配置] 上采样: 2")
    
    # 加载目标人脸
    target_path = "Images/目标脸.jpg"
    print(f"\n{'='*70}")
    print(f"  步骤 1: 加载目标人脸")
    print(f"{'='*70}")
    print(f"文件路径: {target_path}")
    
    if not os.path.exists(target_path):
        print(f"[ERROR] 目标图像不存在: {target_path}")
        return
    
    success = engine.load_target_face(target_path)
    if not success:
        print("[ERROR] 目标人脸加载失败")
        return
    
    print("[OK] 目标人脸加载成功")
    target_info = engine.get_target_info()
    print(f"  - 特征维度: {target_info['feature_dim']}")
    print(f"  - 检测模型: {target_info['model_method']}")
    
    # 处理所有场景图
    print(f"\n{'='*70}")
    print(f"  步骤 2: 批量处理场景图像")
    print(f"{'='*70}\n")
    
    results = []
    total_faces = 0
    total_matches = 0
    
    for i in range(1, 9):
        scene_path = f"Images/Image-{i}.jpg"
        print(f"[{i}/8] 处理: {os.path.basename(scene_path)}")
        
        if not os.path.exists(scene_path):
            print(f"      [SKIP] 文件不存在\n")
            continue
        
        try:
            # 处理场景图
            result_img, info = engine.process_scene(scene_path, upsample=2)
            
            # 解析结果信息
            # 格式: "检测到人脸: X 个 | 匹配目标: Y 个 | 最佳匹配距离: Z"
            parts = info.split('|')
            faces = int(parts[0].split(':')[1].strip().split()[0])
            matches = int(parts[1].split(':')[1].strip().split()[0])
            best_dist = float(parts[2].split(':')[1].strip())
            
            total_faces += faces
            total_matches += matches
            
            # 计算置信度
            if best_dist < 1.0:
                confidence = compute_confidence(best_dist, engine.tolerance)
                print(f"      {info}")
                print(f"      最佳匹配置信度: {confidence:.1f}%")
            else:
                print(f"      {info}")
                print(f"      未找到匹配")
            
            # 保存结果
            output_path = f"outputs/results/Image-{i}_result.jpg"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if save_image(result_img, output_path):
                print(f"      [OK] 结果已保存: {output_path}")
            else:
                print(f"      [WARNING] 保存失败")
            
            results.append({
                'scene': scene_path,
                'faces': faces,
                'matches': matches,
                'best_distance': best_dist,
                'success': True
            })
            
            print()  # 空行
            
        except Exception as e:
            print(f"      [ERROR] 处理失败: {e}\n")
            results.append({
                'scene': scene_path,
                'faces': 0,
                'matches': 0,
                'best_distance': 1.0,
                'success': False
            })
    
    # 生成总结报告
    print("="*70)
    print("  测试总结")
    print("="*70)
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n处理结果:")
    print(f"  - 成功处理: {success_count}/8 张图像")
    print(f"  - 总检测人脸: {total_faces} 个")
    print(f"  - 总匹配目标: {total_matches} 个")
    
    if success_count > 0:
        avg_faces = total_faces / success_count
        print(f"  - 平均每图人脸数: {avg_faces:.1f} 个")
        
        if total_matches > 0:
            match_rate = (total_matches / success_count) * 100
            print(f"  - 匹配率: {match_rate:.1f}% (每图找到目标的比率)")
    
    print(f"\n详细结果:")
    for i, result in enumerate(results, 1):
        if result['success']:
            status = "[OK]"
            detail = f"人脸:{result['faces']} 匹配:{result['matches']} 距离:{result['best_distance']:.3f}"
        else:
            status = "[FAIL]"
            detail = "处理失败"
        print(f"  Image-{i}: {status} {detail}")
    
    print("\n" + "="*70)
    print("  测试完成！")
    print("="*70)
    print(f"\n结果保存在: outputs/results/")
    print()


def test_matcher_module():
    """测试matcher模块功能"""
    print("\n" + "="*70)
    print("  Matcher 模块功能测试")
    print("="*70)
    
    from core.matcher import (
        euclidean_distance,
        compute_confidence,
        TOLERANCE_PRESETS,
        get_recommended_tolerance
    )
    
    # 测试1: 欧氏距离
    print("\n[测试1] 欧氏距离计算")
    feat1 = np.random.rand(128)
    feat2 = feat1.copy()  # 相同
    feat3 = np.random.rand(128)  # 不同
    
    dist_same = euclidean_distance(feat1, feat2)
    dist_diff = euclidean_distance(feat1, feat3)
    
    print(f"  相同特征距离: {dist_same:.6f} (应接近0)")
    print(f"  不同特征距离: {dist_diff:.6f}")
    assert dist_same < 0.001, "相同特征距离应该接近0"
    print("  [OK] 欧氏距离计算正确")
    
    # 测试2: 置信度计算
    print("\n[测试2] 置信度计算")
    test_cases = [
        (0.00, 100.0),
        (0.225, 50.0),
        (0.45, 0.0),
        (0.60, 0.0)
    ]
    
    for distance, expected in test_cases:
        conf = compute_confidence(distance, tolerance=0.45)
        print(f"  距离 {distance:.3f} -> 置信度 {conf:.1f}% (期望 {expected:.1f}%)")
        assert abs(conf - expected) < 1.0, f"置信度计算错误"
    
    print("  [OK] 置信度计算正确")
    
    # 测试3: 推荐阈值
    print("\n[测试3] 推荐阈值")
    for scenario, threshold in TOLERANCE_PRESETS.items():
        recommended = get_recommended_tolerance(scenario)
        print(f"  {scenario:12s}: {recommended:.2f}")
        assert recommended == threshold
    
    print("  [OK] 推荐阈值正确")
    
    print("\n" + "="*70)
    print("  Matcher 模块测试通过！")
    print("="*70 + "\n")


if __name__ == "__main__":
    # 配置日志
    setup_logging()
    
    # 测试matcher模块
    test_matcher_module()
    
    # 测试所有场景图
    test_all_scenes()

