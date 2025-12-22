"""
下载 OpenCV Zoo 模型文件

YuNet: 人脸检测模型
SFace: 人脸识别模型
"""

import os
import urllib.request
import sys

# 模型下载信息
MODELS = {
    "face_detection_yunet_2023mar.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "desc": "YuNet 人脸检测模型"
    },
    "face_recognition_sface_2021dec.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
        "desc": "SFace 人脸识别模型"
    }
}


def download_model(filename: str, url: str, desc: str):
    """下载单个模型文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    if os.path.exists(filepath):
        print(f"[跳过] {desc} 已存在: {filename}")
        return True
    
    print(f"[下载] {desc}: {filename}")
    print(f"       URL: {url}")
    
    try:
        # 显示下载进度
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                sys.stdout.write(f"\r       进度: {percent:.1f}% ({downloaded}/{total_size} bytes)")
                sys.stdout.flush()
        
        urllib.request.urlretrieve(url, filepath, reporthook=report_progress)
        print(f"\n[完成] {filename} 下载成功")
        return True
        
    except Exception as e:
        print(f"\n[错误] 下载失败: {e}")
        return False


def main():
    """下载所有模型"""
    print("=" * 60)
    print("OpenCV Zoo 模型下载工具")
    print("=" * 60)
    
    success_count = 0
    for filename, info in MODELS.items():
        if download_model(filename, info["url"], info["desc"]):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"下载完成: {success_count}/{len(MODELS)} 个模型")
    
    if success_count < len(MODELS):
        print("\n提示: 如果下载失败，请手动从以下地址下载：")
        for filename, info in MODELS.items():
            print(f"  - {info['url']}")
        print(f"\n将文件放置到: {os.path.dirname(os.path.abspath(__file__))}")
    
    return success_count == len(MODELS)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

