from flask import Flask, render_template, request, jsonify
import backend
import os
from tkinter import filedialog
import tkinter as tk
import sys
import webbrowser
import threading

def get_resource_path(relative_path):
    """
    智能寻路系统：
    如果是开发环境，就用普通路径；
    如果是 exe 环境，就去 PyInstaller 创建的临时目录(sys._MEIPASS)里找文件。
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


app = Flask(__name__, 
            template_folder=get_resource_path('templates'),
            static_folder=get_resource_path('static'))
# ==========================================
# 页面路由
# ==========================================

@app.route('/')
def index():
    """渲染主页模板，前端分离后只负责发送纯净的 HTML 骨架"""
    return render_template('index.html')

# ==========================================
# 数据 API 接口
# ==========================================

@app.route('/api/data', methods=['GET'])
def get_data():
    """获取本地已解析的番剧数据字典"""
    data = backend.load_data()
    return jsonify(data)

@app.route('/api/scan', methods=['POST'])
def scan_folder():
    """接收前端传来的路径，触发后端扫描机制"""
    folder_path = request.json.get('path')
    
    # 防御性编程：检查路径合法性
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({"error": "路径无效或不存在，请检查后重试！"}), 400
        
    # 调用后端核心逻辑进行扫描与匹配
    new_data = backend.scan_file(folder_path)
    
    if new_data:
        backend.save_data(new_data) # 持久化保存到 JSON
        return jsonify({"message": "找 到 咯 ~", "data": new_data})
    else:
        return jsonify({"error": "该目录下没有找到支持的视频文件。"}), 400

@app.route('/api/play', methods=['POST'])
def play_video():
    """桥接 Web 与本地系统的核心：调用本地播放器"""
    video_path = request.json.get('path')
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({"error": "找不到文件，可能已经被移动或删除！"}), 404
        
    print(f"\n[系统调用] 准备唤起本地播放器: {video_path}\n")
    
    try:
        # os.startfile 利用 Windows 系统的文件关联机制，安全且解耦
        os.startfile(video_path)
        return jsonify({"message": "播放指令已成功发送"})
    except Exception as e:
        print(f"打开播放器失败: {e}")
        return jsonify({"error": f"系统调用失败: {str(e)}"}), 500

@app.route('/api/select-folder', methods=['POST'])
def select_folder():
    """
    打破浏览器沙盒限制：通过后端唤起系统的文件夹选择器。
    注意：Tkinter 在 Flask 多线程下可能有隐患，若发生卡死可尝试在 app.run 加 threaded=False
    """
    try:
        root = tk.Tk()
        root.withdraw()                   # 隐藏主窗口，只留对话框
        root.attributes('-topmost', True) # 强制对话框置顶，防止被浏览器挡住
        
        folder_path = filedialog.askdirectory(title="选择包含番剧视频的文件夹")
        root.destroy()                    # 及时销毁，释放内存
        
        if folder_path:
            return {'status': 'success', 'path': folder_path}
        else:
            return {'status': 'cancelled', 'path': ''}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    print("===================================================")
    print("  AniManager 启 动 ！ ")
    print("===================================================")
    
    threading.Timer(0.5, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
    
    app.run(debug=False, port=5000)