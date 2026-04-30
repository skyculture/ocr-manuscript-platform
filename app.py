import os
import json
import socket
import subprocess
import threading
import time
import re
import sys
from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads')
DIST_DIR = os.path.join(BASE_DIR, 'static', 'dist')

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

if IS_CLOUD:
    database_url = os.environ.get('DATABASE_URL', '')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    if not database_url:
        database_url = f'sqlite:///{os.path.join(BASE_DIR, "instance", "app.db")}'
        os.makedirs(os.path.join(BASE_DIR, 'instance'), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    mysql_user = os.environ.get('MYSQL_USER', 'root')
    mysql_password = os.environ.get('MYSQL_PASSWORD', 'oyhm070429')
    mysql_db = os.environ.get('MYSQL_DB', 'ocr_platform')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}?charset=utf8mb4'
    )

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)


class Annotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    image_filename = db.Column(db.String(256), nullable=True)
    json_filename = db.Column(db.String(256), nullable=True)
    json_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        parsed_data = None
        if self.json_data:
            try:
                parsed_data = json.loads(self.json_data)
            except Exception:
                parsed_data = {"error": "无法解析JSON数据"}

        return {
            'name': self.name,
            'filename': self.image_filename or self.json_filename or self.name,
            'image_url': f'/static/uploads/annotation/{self.image_filename}' if self.image_filename else None,
            'has_json': self.json_data is not None,
            'json_data': parsed_data
        }


class TrainingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    json_data = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        parsed_data = None
        try:
            parsed_data = json.loads(self.json_data)
        except Exception:
            parsed_data = {"error": "无法解析JSON数据"}

        has_image = self.image_filename is not None and os.path.exists(
            os.path.join(TRAINING_IMG_DIR, self.image_filename))

        return {
            'name': self.name,
            'filename': self.filename,
            'data': parsed_data,
            'has_image': has_image,
            'image_url': f'/static/uploads/training/{self.image_filename}' if has_image else None
        }


class ProofreadingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    json_data = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        parsed_data = None
        try:
            parsed_data = json.loads(self.json_data)
        except Exception:
            parsed_data = {"error": "无法解析JSON数据"}

        has_image = self.image_filename is not None and os.path.exists(
            os.path.join(PROOFREADING_IMG_DIR, self.image_filename))

        return {
            'name': self.name,
            'filename': self.filename,
            'data': parsed_data,
            'has_image': has_image,
            'image_url': f'/static/uploads/proofreading/{self.image_filename}' if has_image else None
        }


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


def migrate_file_data_to_db():
    if Annotation.query.first() is not None:
        return

    safe_print('  [迁移] 检测到数据库为空，正在从文件系统迁移数据...')

    if os.path.exists(ANNOTATION_IMG_DIR):
        for f in sorted(os.listdir(ANNOTATION_IMG_DIR)):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
                name = os.path.splitext(f)[0]
                json_path = os.path.join(ANNOTATION_JSON_DIR, name + '.json')
                json_data = None
                json_filename = None
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as jf:
                            json_data = json.load(jf)
                        json_filename = name + '.json'
                    except Exception:
                        pass
                record = Annotation(
                    name=name,
                    image_filename=f,
                    json_filename=json_filename,
                    json_data=json.dumps(json_data, ensure_ascii=False) if json_data else None
                )
                db.session.add(record)

    if os.path.exists(TRAINING_JSON_DIR):
        for f in sorted(os.listdir(TRAINING_JSON_DIR)):
            if f.lower().endswith('.json'):
                json_path = os.path.join(TRAINING_JSON_DIR, f)
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    name = os.path.splitext(f)[0]
                    img_path_png = os.path.join(TRAINING_IMG_DIR, name + '.png')
                    img_path_jpg = os.path.join(TRAINING_IMG_DIR, name + '.jpg')
                    img_filename = None
                    if os.path.exists(img_path_png):
                        img_filename = name + '.png'
                    elif os.path.exists(img_path_jpg):
                        img_filename = name + '.jpg'
                    record = TrainingResult(
                        name=name,
                        filename=f,
                        json_data=json.dumps(data, ensure_ascii=False),
                        image_filename=img_filename
                    )
                    db.session.add(record)
                except Exception:
                    pass

    if os.path.exists(PROOFREADING_JSON_DIR):
        for f in sorted(os.listdir(PROOFREADING_JSON_DIR)):
            if f.lower().endswith('.json'):
                json_path = os.path.join(PROOFREADING_JSON_DIR, f)
                try:
                    with open(json_path, 'r', encoding='utf-8') as jf:
                        data = json.load(jf)
                    name = os.path.splitext(f)[0]
                    img_path_png = os.path.join(PROOFREADING_IMG_DIR, name + '.png')
                    img_path_jpg = os.path.join(PROOFREADING_IMG_DIR, name + '.jpg')
                    img_filename = None
                    if os.path.exists(img_path_png):
                        img_filename = name + '.png'
                    elif os.path.exists(img_path_jpg):
                        img_filename = name + '.jpg'
                    record = ProofreadingResult(
                        name=name,
                        filename=f,
                        json_data=json.dumps(data, ensure_ascii=False),
                        image_filename=img_filename
                    )
                    db.session.add(record)
                except Exception:
                    pass

    db.session.commit()
    safe_print('  [迁移] 数据迁移完成')


with app.app_context():
    db.create_all()
    migrate_file_data_to_db()


@app.route('/api/network-info')
def network_info():
    if IS_CLOUD:
        host = request.host
        cloud_url = f'https://{host}'
        return jsonify({
            'ips': [],
            'local_ip': '',
            'campus_network_detected': False,
            'public_url': cloud_url,
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
        'local_ip': ips[0] if ips else '',
        'campus_network_detected': campus_detected,
        'public_url': tunnel_url,
        'tunnel_url': tunnel_url,
        'tunnel_active': tunnel_url is not None,
        'tunnel_starting': tunnel_starting,
        'port': 5000,
        'cloudflared_available': find_cloudflared() is not None,
        'is_cloud': False
    })


@app.route('/api/network/info')
def network_info_alt():
    return network_info()


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
    records = Annotation.query.order_by(Annotation.created_at.desc()).all()
    return jsonify([r.to_dict() for r in records])


@app.route('/api/annotation/upload', methods=['POST'])
def annotation_upload():
    if 'image' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '文件名为空'}), 400
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')):
        return jsonify({'error': '不支持的图片格式'}), 400

    name = os.path.splitext(file.filename)[0]
    filepath = os.path.join(ANNOTATION_IMG_DIR, file.filename)
    file.save(filepath)

    record = Annotation.query.filter_by(name=name).first()
    if record:
        record.image_filename = file.filename
    else:
        record = Annotation(name=name, image_filename=file.filename)
        db.session.add(record)
    db.session.commit()
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

    name = os.path.splitext(file.filename)[0]
    filepath = os.path.join(ANNOTATION_JSON_DIR, file.filename)
    file.save(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception:
        return jsonify({'error': 'JSON文件解析失败'}), 400

    record = Annotation.query.filter_by(name=name).first()
    if record:
        record.json_filename = file.filename
        record.json_data = json.dumps(json_data, ensure_ascii=False)
    else:
        record = Annotation(name=name, json_filename=file.filename,
                            json_data=json.dumps(json_data, ensure_ascii=False))
        db.session.add(record)
    db.session.commit()
    return jsonify({'success': True, 'filename': file.filename})


@app.route('/api/annotation/<name>', methods=['DELETE'])
def annotation_delete(name):
    record = Annotation.query.filter_by(name=name).first()
    if not record:
        return jsonify({'error': '记录不存在'}), 404
    if record.image_filename:
        img_path = os.path.join(ANNOTATION_IMG_DIR, record.image_filename)
        if os.path.exists(img_path):
            os.remove(img_path)
    if record.json_filename:
        json_path = os.path.join(ANNOTATION_JSON_DIR, record.json_filename)
        if os.path.exists(json_path):
            os.remove(json_path)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/training/list')
def training_list():
    records = TrainingResult.query.order_by(TrainingResult.created_at.desc()).all()
    return jsonify([r.to_dict() for r in records])


@app.route('/api/training/upload', methods=['POST'])
def training_upload():
    json_file = request.files.get('json_file')
    image_file = request.files.get('image_file')
    if not json_file:
        return jsonify({'error': '请上传JSON结果文件'}), 400

    try:
        data = json.load(json_file)
    except Exception:
        return jsonify({'error': 'JSON文件解析失败'}), 400

    name = os.path.splitext(json_file.filename)[0]
    json_path = os.path.join(TRAINING_JSON_DIR, json_file.filename)
    json_file.seek(0)
    json_file.save(json_path)

    img_filename = None
    if image_file and image_file.filename:
        img_path = os.path.join(TRAINING_IMG_DIR, image_file.filename)
        image_file.save(img_path)
        img_filename = image_file.filename

    record = TrainingResult.query.filter_by(name=name).first()
    if record:
        record.filename = json_file.filename
        record.json_data = json.dumps(data, ensure_ascii=False)
        if img_filename:
            record.image_filename = img_filename
    else:
        record = TrainingResult(
            name=name, filename=json_file.filename,
            json_data=json.dumps(data, ensure_ascii=False),
            image_filename=img_filename
        )
        db.session.add(record)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/training/<name>', methods=['DELETE'])
def training_delete(name):
    record = TrainingResult.query.filter_by(name=name).first()
    if not record:
        return jsonify({'error': '记录不存在'}), 404
    json_path = os.path.join(TRAINING_JSON_DIR, record.filename)
    if os.path.exists(json_path):
        os.remove(json_path)
    if record.image_filename:
        img_path = os.path.join(TRAINING_IMG_DIR, record.image_filename)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/proofreading/list')
def proofreading_list():
    records = ProofreadingResult.query.order_by(ProofreadingResult.created_at.desc()).all()
    return jsonify([r.to_dict() for r in records])


@app.route('/api/proofreading/upload', methods=['POST'])
def proofreading_upload():
    json_file = request.files.get('json_file')
    image_file = request.files.get('image_file')
    if not json_file:
        return jsonify({'error': '请上传JSON结果文件'}), 400

    try:
        data = json.load(json_file)
    except Exception:
        return jsonify({'error': 'JSON文件解析失败'}), 400

    name = os.path.splitext(json_file.filename)[0]
    json_path = os.path.join(PROOFREADING_JSON_DIR, json_file.filename)
    json_file.seek(0)
    json_file.save(json_path)

    img_filename = None
    if image_file and image_file.filename:
        img_path = os.path.join(PROOFREADING_IMG_DIR, image_file.filename)
        image_file.save(img_path)
        img_filename = image_file.filename

    record = ProofreadingResult.query.filter_by(name=name).first()
    if record:
        record.filename = json_file.filename
        record.json_data = json.dumps(data, ensure_ascii=False)
        if img_filename:
            record.image_filename = img_filename
    else:
        record = ProofreadingResult(
            name=name, filename=json_file.filename,
            json_data=json.dumps(data, ensure_ascii=False),
            image_filename=img_filename
        )
        db.session.add(record)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/proofreading/<name>', methods=['DELETE'])
def proofreading_delete(name):
    record = ProofreadingResult.query.filter_by(name=name).first()
    if not record:
        return jsonify({'error': '记录不存在'}), 404
    json_path = os.path.join(PROOFREADING_JSON_DIR, record.filename)
    if os.path.exists(json_path):
        os.remove(json_path)
    if record.image_filename:
        img_path = os.path.join(PROOFREADING_IMG_DIR, record.image_filename)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(record)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_vue(path):
    if path and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, 'index.html')


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
