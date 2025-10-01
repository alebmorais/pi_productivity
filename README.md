
---

## Câmera: Postura e OCR de Anotações

### Dependências de SO
```bash
sudo apt update
sudo apt install -y python3-picamera2 tesseract-ocr
```

### Dependências Python
Instale via `pip install -r requirements.txt`:
- opencv-python
- pytesseract
- pillow

Pi Productivity (Raspberry Pi 5 + Sense HAT + Camera)

Ferramentas de produtividade com Raspberry Pi 5 (8GB), Sense HAT, câmera (Picamera2) e (opcional) display e-paper.
Funcionalidades principais:

Modos com padrões de LED (trabalho, estudo, lazer, tarefas, postura, OCR).

Monitoramento de postura contínuo, com log em CSV e feedback visual.

OCR de anotações → cria/conclui tasks no Motion (com label e due date).

Lembrete de hidratação (gota azul-clara no LED) em intervalo configurável.

Análise: gera gráficos e correlação (postura × tarefas concluídas).

1) Hardware & SO

Raspberry Pi 5 (8GB)

Sense HAT encaixado no GPIO

Camera (conector CSI) habilitada

(Opcional) e-paper 1,53" — a integração visual será configurada depois

Sistema: Raspberry Pi OS (Debian 12 Bookworm)

2) Pré-requisitos do sistema
# Atualizar índices
sudo apt update

# Bibliotecas principais (camera, opencv, tesseract, sense hat)
sudo apt install -y python3-picamera2 python3-opencv tesseract-ocr python3-sense-hat

# (opcional) idiomas extras do Tesseract
# sudo apt install -y tesseract-ocr-por tesseract-ocr-eng tesseract-ocr-osd


Importante: usamos python3-opencv do sistema para evitar conflitos com simplejpeg.
Não instale opencv-python via pip.

3) Clonar / copiar o projeto

Coloque o projeto em ~/pi_productivity (home do usuário pi):

cd ~
# se já tem a pasta copiada, pule este passo
# git clone ...  (ou scp da sua máquina)

4) Ambiente Python

Crie venv usando pacotes do sistema (para compartilhar OpenCV/numpy):

cd ~/pi_productivity
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt


Se abrir nova sessão SSH no futuro:
source ~/pi_productivity/.venv/bin/activate

5) Configuração (.env)

Crie a partir do exemplo:

cd ~/pi_productivity
cp .env.example .env
nano .env


Campos principais:

# Motion
MOTION_API_KEY=coloque_sua_chave_aqui
MOTION_ENABLE_OCR=1
OCR_DEFAULT_DUE_DAYS=2

# Loops automáticos
AUTO_POSTURE=1
POSTURE_INTERVAL_SEC=30

AUTO_OCR=1
OCR_INTERVAL_SEC=900   # 15 min

# Hidratação (LED com gota azul-clara)
HYDRATE_ENABLE=1
HYDRATE_INTERVAL_MIN=40
HYDRATE_FLASHES=6
HYDRATE_ON_SEC=0.25
HYDRATE_OFF_SEC=0.15


Segurança: não commit o .env. Trate sua MOTION_API_KEY como segredo.

6) Como rodar
cd ~/pi_productivity
source .venv/bin/activate
python main.py


Você deve ver no terminal:

[Auto] Postura ligada (cada 30s)
[Auto] OCR ligado (cada 900s)
[Auto] Hidratação ligada (cada 40 min)

7) Controles (Sense HAT — joystick)

Cima / Baixo: alterna entre os modos. Ao mudar, o LED mostra o padrão do modo.

Direita:

Em POSTURA → executa 1 ciclo de postura (pisca verde = ok, vermelho = ajustar).

Em OCR NOTAS → executa 1 ciclo de OCR (pisca ciano ao concluir).

Esquerda: reservado (ex.: abrir painel de tarefas no e-paper — implementar quando o display chegar).

Mesmo sem acionar manualmente, os loops automáticos chamam periodicamente:

Postura a cada POSTURE_INTERVAL_SEC

OCR a cada OCR_INTERVAL_SEC

8) Modos & padrões de LED

TAREFAS: tabuleiro branco/preto (mostra painel quando o e-paper estiver pronto).

TRABALHO: HAPVIDA: metade esquerda verde.

TRABALHO: CARE PLUS: “X” azul.

ESTUDO (TDAH): moldura amarela (técnica sugerida no display ao entrar no modo).

LAZER: roxo sólido.

POSTURA: cruz vermelha (monitoramento).

OCR NOTAS: moldura e diagonal ciano (leitura/automação).

Eventos:

Postura OK → pisca verde; Ajustar → vermelho.

OCR concluído → ciano.

Hidratação (a cada HYDRATE_INTERVAL_MIN) → gota azul-clara piscando; volta ao padrão do modo depois.

9) OCR → regras e integração com Motion

Formato sugerido nas anotações:

Revisão Bibliográfica
- [ ] Ler artigo X
- [x] Enviar e-mail Y
DUE: 2025-10-05


Regras:

Título da seção (“Revisão Bibliográfica”) → vira label da task.

- [ ] ou TODO: → cria tarefa (label = título).

- [x] ou DONE: → conclui tarefa; se não existir, cria e conclui.

DUE: YYYY-MM-DD → define prazo; se ausente, usa OCR_DEFAULT_DUE_DAYS (padrão 2 dias).

Arquivos gerados pelo OCR:

Imagem preprocessada: ~/pi_productivity/notes/note_YYYYmmdd_HHMMSS.png

Texto extraído: ~/pi_productivity/notes/note_YYYYmmdd_HHMMSS.txt

10) Logs e análise

Logs:

Postura (texto diário): ~/pi_productivity/logs/posture_YYYYMMDD.txt

Postura (CSV cumulativo): ~/pi_productivity/logs/posture_events.csv
Campos: timestamp, ok, reason, tilt_deg, nod_deg, session_adjustments, tasks_completed_today

OCR/Tasks (CSV): ~/pi_productivity/logs/task_events.csv
Campos: timestamp, action, section_title, task_name

Análise (opcional):

Script: analyze_productivity.py

Saídas em ~/pi_productivity/analytics/:

summary_daily.csv

posture_per_day.png

tasks_completed_per_day.png

posture_vs_tasks_scatter.png

report.txt (correlação)

Como rodar:

cd ~/pi_productivity
source .venv/bin/activate
python analyze_productivity.py

11) Dicas & solução de problemas

Camera/NumPy/simplejpeg: use pacotes do sistema:
sudo apt install -y python3-picamera2 python3-opencv python3-numpy python3-simplejpeg

OpenCV cv2.data ausente: já tratamos com paths fixos:
/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml

Sem GUI (SSH): xdg-open pode não funcionar via SSH. Para ver arquivos:

Copie para seu computador:
scp pi@<ip_do_pi>:/home/pi/pi_productivity/last_posture.jpg .

Motion 401/400: verifique MOTION_API_KEY no .env.
Teste rápido:

python - <<'PY'
import os, requests
from dotenv import load_dotenv
load_dotenv("/home/pi/pi_productivity/.env")
api=os.getenv("MOTION_API_KEY")
print(requests.get("https://api.usemotion.com/v1/tasks", headers={"X-API-Key":api}, timeout=15).status_code)
PY


Esperado: 200.

Permissão em /mnt/data: não usamos esse caminho; tudo salva em ~/pi_productivity/....

12) Próximos passos (e-paper)

Quando o e-paper estiver conectado, ativaremos:

render das tarefas do dia (Motion) com prazos

modo TAREFAS atualiza o e-paper automaticamente

atalhos no joystick (⬅️) para “atualizar painel”

13) Comandos úteis
# Ativar venv
source ~/pi_productivity/.venv/bin/activate

# Rodar app
python ~/pi_productivity/main.py

# Rodar análise
python ~/pi_productivity/analyze_productivity.py

# Editar configs
nano ~/pi_productivity/.env
