import os
import json
import socket
import subprocess
import threading
import time
import re
import sys
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')

ANNOTATION_IMG_DIR = os.path.join(UPLOAD_DIR, 'annotation')
ANNOTATION_JSON_DIR = os.path.join(DATA_DIR, 'annotations')
TRAINING_IMG_DIR = os.path.join(UPLOAD_DIR, 'training')
TRAINING_JSON_DIR = os.path.join(DATA_DIR, 'training')
PROOFREADING_IMG_DIR = os.path.join(UPLOAD_DIR, 'proofreading')
PROOFREADING_JSON_DIR = os.path.join(DATA_DIR, 'proofreading')

for d in [ANNOTATION_IMG_DIR, ANNOTATION_JSON_DIR,
          TRAINING_IMG_DIR, TRAINING_JSON_DIR,
          PROOFREADING_IMG_DIR, PROOFREADING_JSON_DIR]:
    os.makedirs(d, exist_ok=True)

IS_CLOUD = os.environ.get('RENDER', '') == '1' or os.environ.get('DYNO', '') != ''

tunnel_url = None
tunnel_process = None
tunnel_starting = False


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))


def get_all_network_ips():
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith('127.'):
                ips.append(ip)
    except Exception:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        default_ip = s.getsockname()[0]
        s.close()
        if default_ip not in ips:
            ips.insert(0, default_ip)
    except Exception:
        pass
    return ips if ips else ['127.0.0.1']


def is_campus_network(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    first = int(parts[0])
    second = int(parts[1])
    if first == 100 and 64 <= second <= 127:
        return True
    return False


def find_cloudflared():
    cloudflared_path = os.path.join(BASE_DIR, 'cloudflared.exe')
    if os.path.exists(cloudflared_path):
        return cloudflared_path
    import shutil
    found = shutil.which('cloudflared')
    if found:
        return found
    return None


def start_cloudflared_tunnel(port):
    global tunnel_url, tunnel_process
    try:
        cloudflared_path = find_cloudflared()
        if not cloudflared_path:
            return None, 'cloudflared未安装'

        tunnel_process = subprocess.Popen(
            [cloudflared_path, 'tunnel', '--url', f'http://localhost:{port}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        start_time = time.time()
        while time.time() - start_time < 45:
            line = tunnel_process.stdout.readline()
            if not line:
                if tunnel_process.poll() is not None:
                    return None, 'cloudflared进程意外退出'
                time.sleep(0.5)
                continue
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                tunnel_url = match.group()
                return tunnel_url, None
            if 'error' in line.lower() or 'failed' in line.lower():
                return None, f'cloudflared错误: {line.strip()}'

        return None, '等待隧道URL超时'
    except FileNotFoundError:
        return None, 'cloudflared未找到'
    except Exception as e:
        return None, f'启动隧道失败: {str(e)}'


def auto_start_tunnel(port):
    global tunnel_url, tunnel_starting
    tunnel_starting = True
    cloudflared_path = find_cloudflared()
    if cloudflared_path:
        safe_print('  [隧道] 正在自动启动公网隧道...')
        url, err = start_cloudflared_tunnel(port)
        if url:
            safe_print(f'  [隧道] 公网地址: {url}')
            safe_print('  [隧道] 国内任何网络均可访问此地址')
        else:
            safe_print(f'  [隧道] 自动启动失败: {err}')
    else:
        safe_print('  [隧道] 未找到cloudflared.exe，跳过公网隧道')
    tunnel_starting = False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/annotation')
def annotation():
    return render_template('annotation.html')


@app.route('/training')
def training():
    return render_template('training.html')


@app.route('/proofreading')
def proofreading():
    return render_template('proofreading.html')


@app.route('/api/network-info')
def network_info():
    if IS_CLOUD:
        host = request.host
        cloud_url = f'https://{host}'
        return jsonify({
            'ips': [],
            'campus_network_detected': False,
            'tunnel_url': cloud_url,
            'tunnel_active': True,
            'tunnel_starting': False,
            'port': 443,
            'cloudflared_available': False,
            'is_cloud': True
        })

    ips = get_all_network_ips()
    campus_detected = any(is_campus_network(ip) for ip in ips)
    return jsonify({
        'ips': ips,
        'campus_network_detected': campus_detected,
        'tunnel_url': tunnel_url,
        'tunnel_active': tunnel_url is not None,
        'tunnel_starting': tunnel_starting,
        'port': 5000,
        'cloudflared_available': find_cloudflared() is not None,
        'is_cloud': False
    })


@app.route('/api/tunnel/start')
def start_tunnel():
    global tunnel_url
    if IS_CLOUD:
        return jsonify({'success': True, 'url': f'https://{request.host}'})
    if tunnel_url:
        return jsonify({'success': True, 'url': tunnel_url})
    if tunnel_starting:
        return jsonify({'success': False, 'message': '隧道正在启动中，请稍后刷新页面'})
    if not find_cloudflared():
        return jsonify({'success': False, 'message': 'cloudflared.exe未找到'})

    def run_tunnel():
        url, err = start_cloudflared_tunnel(5000)
        if err:
            safe_print(f'  [隧道错误] {err}')

    t = threading.Thread(target=run_tunnel, daemon=True)
    t.start()
    time.sleep(5)
    if tunnel_url:
        return jsonify({'success': True, 'url': tunnel_url})
    return jsonify({'success': False, 'message': '隧道启动中，请稍后刷新页面查看'})


@app.route('/api/annotation/list')
def annotation_list():
    images = []
    if os.path.exists(ANNOTATION_IMG_DIR):
        for f in sorted(os.listdir(ANNOTATION_IMG_DIR)):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                name = os.path.splitext(f)[0]
                json_path = os.path.join(ANNOTATION_JSON_DIR, name + '.json')
                has_json = os.path.exists(json_path)
                json_data = None
                if has_json:
                    try:
                        with open(json_path, 'r', encoding='utf-8') as jf:
                            json_data = json.load(jf)
                    except Exception:
                        json_data = {"error": "无法解析JSON文件"}
                images.append({
                    'name': name,
                    'filename': f,
                    'image_url': f'/static/uploads/annotation/{f}',
                    'has_json': has_json,
                    'json_data': json_data
                })
    return jsonify(images)


@app.route('/api/annotation/upload', methods=['POST'])
def annotation_upload():
    if 'image' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
        return jsonify({'error': '不支持的图片格式'}), 400
    filepath = os.path.join(ANNOTATION_IMG_DIR, file.filename)
    file.save(filepath)
    return jsonify({'success': True, 'filename': file.filename})


@app.route('/api/annotation/json/upload', methods=['POST'])
def annotation_json_upload():
    if 'json_file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    file = request.files['json_file']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if not file.filename.lower().endswith('.json'):
        return jsonify({'error': '只支持JSON文件'}), 400
    filepath = os.path.join(ANNOTATION_JSON_DIR, file.filename)
    file.save(filepath)
    return jsonify({'success': True, 'filename': file.filename})


@app.route('/api/training/list')
def training_list():
    results = []
    if os.path.exists(TRAINING_JSON_DIR):
        for f in sorted(os.listdir(TRAINING_JSON_DIR)):
            if f.lower().endswith('.json'):
                json_path = os.path.join(TRAINING_JSON_DIR, f)
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    name = os.path.splitext(f)[0]
                    img_path = os.path.join(TRAINING_IMG_DIR, name + '.png')
                    has_image = os.path.exists(img_path)
                    if not has_image:
                        img_path = os.path.join(TRAINING_IMG_DIR, name + '.jpg')
                        has_image = os.path.exists(img_path)
                    results.append({
                        'name': name,
                        'filename': f,
                        'data': data,
                        'has_image': has_image,
                        'image_url': f'/static/uploads/training/{os.path.basename(img_path)}' if has_image else None
                    })
                except Exception as e:
                    results.append({
                        'name': os.path.splitext(f)[0],
                        'filename': f,
                        'data': {'error': f'解析失败: {str(e)}'},
                        'has_image': False,
                        'image_url': None
                    })
    return jsonify(results)


@app.route('/api/training/upload', methods=['POST'])
def training_upload():
    json_file = request.files.get('json_file')
    image_file = request.files.get('image_file')
    if not json_file:
        return jsonify({'error': '请上传JSON结果文件'}), 400
    json_path = os.path.join(TRAINING_JSON_DIR, json_file.filename)
    json_file.save(json_path)
    if image_file and image_file.filename:
        img_path = os.path.join(TRAINING_IMG_DIR, image_file.filename)
        image_file.save(img_path)
    return jsonify({'success': True})


@app.route('/api/proofreading/list')
def proofreading_list():
    results = []
    if os.path.exists(PROOFREADING_JSON_DIR):
        for f in sorted(os.listdir(PROOFREADING_JSON_DIR)):
            if f.lower().endswith('.json'):
                json_path = os.path.join(PROOFREADING_JSON_DIR, f)
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    name = os.path.splitext(f)[0]
                    img_path = os.path.join(PROOFREADING_IMG_DIR, name + '.png')
                    has_image = os.path.exists(img_path)
                    if not has_image:
                        img_path = os.path.join(PROOFREADING_IMG_DIR, name + '.jpg')
                        has_image = os.path.exists(img_path)
                    results.append({
                        'name': name,
                        'filename': f,
                        'data': data,
                        'has_image': has_image,
                        'image_url': f'/static/uploads/proofreading/{os.path.basename(img_path)}' if has_image else None
                    })
                except Exception as e:
                    results.append({
                        'name': os.path.splitext(f)[0],
                        'filename': f,
                        'data': {'error': f'解析失败: {str(e)}'},
                        'has_image': False,
                        'image_url': None
                    })
    return jsonify(results)


@app.route('/api/proofreading/upload', methods=['POST'])
def proofreading_upload():
    json_file = request.files.get('json_file')
    image_file = request.files.get('image_file')
    if not json_file:
        return jsonify({'error': '请上传JSON结果文件'}), 400
    json_path = os.path.join(PROOFREADING_JSON_DIR, json_file.filename)
    json_file.save(json_path)
    if image_file and image_file.filename:
        img_path = os.path.join(PROOFREADING_IMG_DIR, image_file.filename)
        image_file.save(img_path)
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    if IS_CLOUD:
        safe_print('=' * 60)
        safe_print('  OCR手稿识别项目展示平台 (云端部署)')
        safe_print('=' * 60)
        app.run(host='0.0.0.0', port=port)
    else:
        ips = get_all_network_ips()

        safe_print('=' * 60)
        safe_print('  OCR手稿识别项目展示平台 已启动')
        safe_print('=' * 60)
        safe_print(f'  本机访问: http://localhost:{port}')
        safe_print('')
        safe_print('  局域网IP地址:')
        for ip in ips:
            marker = ' (校园网)' if is_campus_network(ip) else ''
            safe_print(f'    http://{ip}:{port}{marker}')
        safe_print('')

        tunnel_thread = threading.Thread(target=auto_start_tunnel, args=(port,), daemon=True)
        tunnel_thread.start()

        safe_print('  正在自动开启公网隧道，请稍候...')
        safe_print('')

        def print_tunnel_url():
            waited = 0
            while waited < 40 and tunnel_url is None and tunnel_starting:
                time.sleep(1)
                waited += 1
            if tunnel_url:
                safe_print('')
                safe_print('=' * 60)
                safe_print('  [公网隧道已开启]')
                safe_print(f'  公网地址: {tunnel_url}')
                safe_print('  国内任何网络均可访问此地址')
                safe_print('=' * 60)
            elif not tunnel_starting:
                safe_print('')
                safe_print('  [公网隧道未能自动开启，可在网页上手动启动]')

        t = threading.Thread(target=print_tunnel_url, daemon=True)
        t.start()

        app.run(host='0.0.0.0', port=port, debug=False)
