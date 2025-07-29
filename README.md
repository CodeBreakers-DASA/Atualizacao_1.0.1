# Atualizacao_1.0.1
Sequência resumida dos comandos e ações
Backend (Flask + OpenCV + PostgreSQL)
Instalar dependências:
bash

pip install flask flask-cors flask-sqlalchemy psycopg2-binary opencv-python-headless opencv-contrib-python
Criar banco de dados PostgreSQL chamado patologista.

Executar o backend:

bash

python meu_Codigo.py
Verificar no terminal se backend rodou em:

http://127.0.0.1:5000
Testar endpoints de vídeo no navegador (para debug):

http://localhost:5000/video_feed_1
http://localhost:5000/video_feed_2
Garantir que o backend aceita requisições CORS do frontend (localhost:3000).
Frontend (React)
Criar app React (se ainda não tiver):
bash

npx create-react-app frontend
cd frontend
Configurar .env:

REACT_APP_BACKEND_URL=http://localhost:5000
Iniciar o frontend:
bash

npm start
Abrir no navegador o frontend em http://localhost:3000.

Calibrar a régua clicando 2 pontos na câmera 1 e confirmar.

Visualizar medidas ao vivo e capturar imagens.

Salvar análises no banco via botão.

Testes e ajustes úteis
Alterar índice da câmera no meu_Codigo.py se alguma câmera não abrir.
Verificar firewall e antivírus para liberar as portas 3000 e 5000.
Reiniciar backend e frontend após mudanças em .env ou código.
Usar o console de rede dos navegadores para verificar erros nas chamadas HTTP.
