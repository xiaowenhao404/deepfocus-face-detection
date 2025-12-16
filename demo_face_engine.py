"""
FaceEngine 演示脚本

演示如何使用人脸识别引擎进行目标人脸识别和定位
"""

import sys
import os

# 检查依赖
try:
    from core.face_engine import FaceEngine
    import cv2
    import numpy as np
    print("[OK] 依赖检查通过")
except ImportError as e:
    print(f"[ERROR] 依赖库未安装: {e}")
    print("\n请先安装依赖:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def demo_basic_usage():
    """基本使用演示"""
    print("\n" + "="*60)
    print("  FaceEngine 基本使用演示")
    print("="*60)
    
    # 1. 创建引擎实例
    print("\n[1] 创建人脸识别引擎...")
    engine = FaceEngine(model_method='hog', tolerance=0.45)
    print("    [OK] 引擎创建成功")
    print(f"    - 检测模型: {engine.model_method}")
    print(f"    - 匹配阈值: {engine.tolerance}")
    
    # 2. 加载目标人脸
    print("\n[2] 加载目标人脸...")
    target_path = "Images/目标脸.jpg"
    
    if not os.path.exists(target_path):
        print(f"    [ERROR] 目标图像不存在: {target_path}")
        return
    
    success = engine.load_target_face(target_path)
    
    if success:
        print("    [OK] 目标人脸加载成功")
        info = engine.get_target_info()
        print(f"    - 特征维度: {info['feature_dim']}")
    else:
        print("    [ERROR] 目标人脸加载失败")
        return
    
    # 3. 处理场景图
    print("\n[3] 处理场景图像...")
    scene_path = "Images/Image-1.jpg"
    
    if not os.path.exists(scene_path):
        print(f"    [ERROR] 场景图像不存在: {scene_path}")
        return
    
    try:
        result_img, info = engine.process_scene(scene_path, upsample=2)
        print("    [OK] 场景处理成功")
        print(f"    - {info}")
        
        # 4. 保存结果
        print("\n[4] 保存识别结果...")
        try:
            output_path = "outputs/results/demo_result.jpg"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 使用cv2保存（支持中文路径）
            _, img_encode = cv2.imencode('.jpg', result_img)
            img_encode.tofile(output_path)
            print(f"    [OK] 结果已保存: {output_path}")
        except Exception as e:
            print(f"    [WARNING] 保存失败: {e}")
            
    except Exception as e:
        print(f"    [ERROR] 处理失败: {e}")
        return
    
    print("\n" + "="*60)
    print("  演示完成！")
    print("="*60 + "\n")


def demo_batch_process():
    """批量处理演示"""
    print("\n" + "="*60)
    print("  批量处理演示")
    print("="*60)
    
    engine = FaceEngine()
    
    # 加载目标
    print("\n加载目标人脸...")
    if not engine.load_target_face("Images/目标脸.jpg"):
        print("[ERROR] 目标加载失败")
        return
    print("[OK] 目标加载成功")
    
    # 批量处理
    print("\n批量处理场景图像...")
    scene_images = [f"Images/Image-{i}.jpg" for i in range(1, 9)]
    
    results = []
    for i, scene_path in enumerate(scene_images, 1):
        if not os.path.exists(scene_path):
            print(f"  [{i}/8] [SKIP] 文件不存在: {scene_path}")
            continue
        
        try:
            result_img, info = engine.process_scene(scene_path, upsample=2)
            results.append((scene_path, result_img, info))
            print(f"  [{i}/8] [OK] {os.path.basename(scene_path)}: {info}")
        except Exception as e:
            print(f"  [{i}/8] [ERROR] {os.path.basename(scene_path)}: {e}")
    
    print(f"\n[OK] 完成！成功处理 {len(results)}/8 张图像")
    print("="*60 + "\n")


if __name__ == "__main__":
    # 运行基本演示
    demo_basic_usage()
    
    # 运行批量处理演示（如果有多张测试图）
    if os.path.exists("Images/Image-2.jpg"):
        demo_batch_process()

