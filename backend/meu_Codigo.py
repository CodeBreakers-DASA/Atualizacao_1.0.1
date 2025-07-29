# Código backend Flask + OpenCV para medir objetos com duas câmeras USB,
# salvar dados completos paciente + medidas + imagens no PostgreSQL,
# e transmitir vídeos com medidas em tempo real.

import cv2
import os
import time
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# configuração CORS para aceitar requests do frontend react em localhost:3000
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

@app.after_request
def after_request_func(response):
    # define os cabeçalhos HTTP necessários para permitir CORS com métodos e headers adequados
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# configuração da conexão com PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/patologista'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# modelo simples da tabela medidas com dados do paciente, análise, medidas e caminhos das imagens
class Medida(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_paciente = db.Column(db.String(100))
    idade = db.Column(db.Integer)
    data_nascimento = db.Column(db.Date)
    tipo_analise = db.Column(db.String(200))
    data_analise = db.Column(db.Date)
    horario_analise = db.Column(db.Time)
    altura_cm = db.Column(db.Float)
    largura_cm = db.Column(db.Float)
    comprimento_cm = db.Column(db.Float)
    imagem_c1_path = db.Column(db.String)
    imagem_c2_path = db.Column(db.String)
    data_captura = db.Column(db.DateTime, default=db.func.now())

with app.app_context():
    db.create_all()

# Inicializa as câmeras
cap1 = cv2.VideoCapture(1)
cap2 = cv2.VideoCapture(2)

# 1 e 2 pois é a entrada que está do usb


# Cria pasta local para armazenar as imagens
if not os.path.exists('capturas'):
    os.makedirs('capturas')

cm_por_pixel = None
altura_estavel = largura_estavel = comprimento_estavel = None

# Parâmetros para detectar estabilidade das medidas (número de frames e tolerância)
TOLERANCIA = 0.1
FRAMES_ESTAVEIS_PARA_CAPTURA = 5

frames_estaveis_c1 = 0
frames_estaveis_c2 = 0
ultima_medida_c1 = (0, 0)  # largura, comprimento
ultima_medida_c2 = 0       # altura

# Função que verifica se as medidas atuais estão estáveis em relação às anteriores
def medidas_estaveis(med_atual, med_antiga, tolerancia=TOLERANCIA):
    if med_antiga is None:
        return False
    if isinstance(med_atual, tuple):
        return all(abs(a - b) < tolerancia for a, b in zip(med_atual, med_antiga))
    else:
        return abs(med_atual - med_antiga) < tolerancia

# Segmenta a imagem, encontra o maior contorno e o retângulo que o contém
def segmenta_e_measures(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    contornos, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return frame, (0, 0, 0, 0)
    maior_contorno = max(contornos, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(maior_contorno)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return frame, (x, y, w, h)

# Desenha linhas indicativas de largura, comprimento e altura e respectivos textos no frame
def desenha_medidas_no_frame(frame, x, y, w, h, cm_por_pixel, camera_id):
    cor_linha = (0, 255, 0)
    cor_texto = (255, 255, 255)
    esp_linha = 2
    esp_texto = 2
    font = cv2.FONT_HERSHEY_SIMPLEX
    escala_texto = 0.7
    seta = 10

    if cm_por_pixel is None:
        cv2.putText(frame, "Calibre a régua para medir", (10, 30), font, 0.7, (0, 0, 255), 2)
        return frame, 0, 0, 0

    if camera_id == 1:
        largura_cm = w * cm_por_pixel
        comprimento_cm = h * cm_por_pixel

        pt1 = (x, y + h + 20)
        pt2 = (x + w, y + h + 20)
        cv2.line(frame, pt1, pt2, cor_linha, esp_linha)
        cv2.line(frame, (pt1[0], pt1[1] - seta), pt1, cor_linha, esp_linha)
        cv2.line(frame, (pt2[0], pt2[1] - seta), pt2, cor_linha, esp_linha)
        texto_largura = f'{largura_cm:.2f} cm'
        tamanho_texto, _ = cv2.getTextSize(texto_largura, font, escala_texto, esp_texto)
        x_texto = pt1[0] + (pt2[0] - pt1[0]) // 2 - tamanho_texto[0] // 2
        y_texto = pt1[1] + 20
        cv2.putText(frame, texto_largura, (x_texto, y_texto), font, escala_texto, cor_texto, esp_texto)
        texto_lar = "Largura"
        cv2.putText(frame, texto_lar, (pt2[0] + 10, y_texto), font, 0.6, cor_texto, 2)

        pt3 = (x - 20, y)
        pt4 = (x - 20, y + h)
        cv2.line(frame, pt3, pt4, cor_linha, esp_linha)
        cv2.line(frame, (pt3[0] - seta, pt3[1]), pt3, cor_linha, esp_linha)
        cv2.line(frame, (pt4[0] - seta, pt4[1]), pt4, cor_linha, esp_linha)
        texto_comp = f'{comprimento_cm:.2f} cm'
        tamanho_texto_v, _ = cv2.getTextSize(texto_comp, font, escala_texto, esp_texto)
        x_texto_v = pt3[0] - tamanho_texto_v[0] - 10
        y_texto_v = pt3[1] + (pt4[1] - pt3[1]) // 2 + tamanho_texto_v[1] // 2
        cv2.putText(frame, texto_comp, (x_texto_v, y_texto_v), font, escala_texto, cor_texto, esp_texto)
        texto_comp_text = "Comprimento"
        cv2.putText(frame, texto_comp_text, (x_texto_v - 85, y_texto_v), font, 0.6, cor_texto, 2)

        return frame, largura_cm, comprimento_cm, 0

    else:
        altura_cm = h * cm_por_pixel
        pt1 = (x + w + 20, y)
        pt2 = (x + w + 20, y + h)
        cv2.line(frame, pt1, pt2, cor_linha, esp_linha)
        cv2.line(frame, (pt1[0] + seta, pt1[1]), pt1, cor_linha, esp_linha)
        cv2.line(frame, (pt2[0] + seta, pt2[1]), pt2, cor_linha, esp_linha)
        texto_alt = f'{altura_cm:.2f} cm'
        tamanho_texto, _ = cv2.getTextSize(texto_alt, font, escala_texto, esp_texto)
        x_texto = pt1[0] + 10
        y_texto = pt1[1] + (pt2[1] - pt1[1]) // 2 + tamanho_texto[1] // 2
        cv2.putText(frame, texto_alt, (x_texto, y_texto), font, escala_texto, cor_texto, esp_texto)
        texto_alt_text = "Altura"
        cv2.putText(frame, texto_alt_text, (x_texto, y_texto - 30), font, 0.6, cor_texto, 2)

        return frame, 0, 0, altura_cm


def gera_frames(cap, camera_id):
    global cm_por_pixel, frames_estaveis_c1, frames_estaveis_c2
    global ultima_medida_c1, ultima_medida_c2
    global largura_estavel, comprimento_estavel, altura_estavel

    frames_estaveis_c1 = 0
    frames_estaveis_c2 = 0
    ultima_medida_c1 = (0, 0)
    ultima_medida_c2 = 0
    largura_estavel = None
    comprimento_estavel = None
    altura_estavel = None

    while True:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
        frame = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
        frame, (x, y, w, h) = segmenta_e_measures(frame)
        if cm_por_pixel is None or w == 0 or h == 0:
            cv2.putText(frame, "Por favor, calibre a régua", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            encodedImage = cv2.imencode('.jpg', frame)[1].tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + encodedImage + b'\r\n')
            continue

        if camera_id == 1:
            frame, largura_cm, comprimento_cm, _ = desenha_medidas_no_frame(frame, x, y, w, h, cm_por_pixel, camera_id)
            medida_atual_c1 = (largura_cm, comprimento_cm)
            if medidas_estaveis(medida_atual_c1, ultima_medida_c1):
                frames_estaveis_c1 += 1
            else:
                frames_estaveis_c1 = 0
            ultima_medida_c1 = medida_atual_c1
            if frames_estaveis_c1 >= FRAMES_ESTAVEIS_PARA_CAPTURA:
                largura_estavel, comprimento_estavel = medida_atual_c1
        else:
            frame, _, _, altura_cm = desenha_medidas_no_frame(frame, x, y, w, h, cm_por_pixel, camera_id)
            medida_atual_c2 = altura_cm
            if medidas_estaveis(medida_atual_c2, ultima_medida_c2):
                frames_estaveis_c2 += 1
            else:
                frames_estaveis_c2 = 0
            ultima_medida_c2 = medida_atual_c2
            if frames_estaveis_c2 >= FRAMES_ESTAVEIS_PARA_CAPTURA:
                altura_estavel = medida_atual_c2

        # Aqui da para capturar automaticamente as imagens sincronizadas mas esta dando problema!!!

        encodedImage = cv2.imencode('.jpg', frame)[1].tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + encodedImage + b'\r\n')


@app.route('/video_feed_1')
def video_feed_1():
    return Response(gera_frames(cap1, 1), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video_feed_2')
def video_feed_2():
    return Response(gera_frames(cap2, 2), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/set_calibracao', methods=['POST'])
def set_calibracao():
    global cm_por_pixel
    data = request.json
    try:
        cm_por_pixel = float(data.get('cm_por_pixel'))
        return jsonify({'status': 'ok', 'cm_por_pixel': cm_por_pixel})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/medidas_atualizadas')
def medidas_atualizadas():
    return jsonify({
        'camera1': {'largura': largura_estavel or 0, 'comprimento': comprimento_estavel or 0},
        'camera2': {'altura': altura_estavel or 0}
    })


@app.route('/salvar_analise', methods=['POST'])
def salvar_analise():
    data = request.json
    try:
        nova = Medida(
            nome_paciente=data.get('nome_paciente'),
            idade=int(data.get('idade')),
            data_nascimento=datetime.strptime(data.get('data_nascimento'), '%Y-%m-%d').date(),
            tipo_analise=data.get('tipo_analise'),
            data_analise=datetime.strptime(data.get('data_analise'), '%Y-%m-%d').date(),
            horario_analise=datetime.strptime(data.get('horario_analise'), '%H:%M').time(),
            altura_cm=data.get('altura_cm'),
            largura_cm=data.get('largura_cm'),
            comprimento_cm=data.get('comprimento_cm'),
            imagem_c1_path=data.get('imagem_c1_path'),
            imagem_c2_path=data.get('imagem_c2_path')
        )
        db.session.add(nova)
        db.session.commit()
        return jsonify({'status': 'sucesso', 'id': nova.id})
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400


@app.route('/lista_analises')
def lista_analises():
    analises = Medida.query.order_by(Medida.data_captura.desc()).all()
    lista = []
    for a in analises:
        lista.append({
            'id': a.id,
            'nome_paciente': a.nome_paciente,
            'idade': a.idade,
            'data_nascimento': a.data_nascimento.strftime('%Y-%m-%d') if a.data_nascimento else '',
            'tipo_analise': a.tipo_analise,
            'data_analise': a.data_analise.strftime('%Y-%m-%d') if a.data_analise else '',
            'horario_analise': a.horario_analise.strftime('%H:%M') if a.horario_analise else '',
            'altura_cm': a.altura_cm,
            'largura_cm': a.largura_cm,
            'comprimento_cm': a.comprimento_cm,
            'imagem_c1_path': a.imagem_c1_path,
            'imagem_c2_path': a.imagem_c2_path,
            'data_captura': a.data_captura.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(lista)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
