# Pi Productivity – Guia rápido para Raspberry Pi

Automatize postura, OCR de anotações e lembretes de hidratação usando Raspberry Pi 5, Sense HAT e câmera oficial. O projeto também integra um display e-paper opcional para mostrar tarefas sincronizadas em um banco SQLite local.

## Antes de começar
- Raspberry Pi 5 (8 GB) com Raspberry Pi OS (Debian 12 Bookworm) atualizado.
- Sense HAT encaixado na GPIO.
- Câmera conectada ao conector CSI e habilitada nas configurações.
- (Opcional) display e-paper Waveshare 1,53".

## Passo a passo (sem precisar ser programador)

### 1. Atualize o Raspberry Pi
```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-opencv tesseract-ocr python3-sense-hat
# Extras do OCR (opcional)
# sudo apt install -y tesseract-ocr-por tesseract-ocr-eng tesseract-ocr-osd
Use o OpenCV do sistema (python3-opencv). Evite instalar opencv-python via pip.

2. Copie o projeto para ~/pi_productivity
Escolha a alternativa que preferir:

Via Git (mais fácil para atualizar depois)

No GitHub do projeto, clique em Code → HTTPS e copie o link.

No terminal do Raspberry:

bash
Copy code
cd ~
git clone <cole_o_link_aqui> pi_productivity
Sem Git (baixando ZIP)

No GitHub, clique em Code → Download ZIP.

No seu computador, descompacte o arquivo.

Copie a pasta para o Raspberry (ex.: com FileZilla ou usando scp):

bash
Copy code
scp -r /caminho/no_seu_pc/pi_productivity pi@IP_DO_PI:/home/pi/
3. Crie o ambiente Python uma vez
bash
Copy code
cd ~/pi_productivity
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt
Sempre que abrir um novo terminal/SSH, ative o ambiente com:

bash
Copy code
source ~/pi_productivity/.venv/bin/activate
4. Configure o arquivo .env
bash
Copy code
cd ~/pi_productivity
cp .env.example .env
nano .env
Preencha:

MOTION_API_KEY: sua chave da Motion.

MOTION_ENABLE_OCR, AUTO_POSTURE, AUTO_OCR: use 1 para ativar.

Intervalos (POSTURE_INTERVAL_SEC, OCR_INTERVAL_SEC, HYDRATE_INTERVAL_MIN, etc.) podem ser ajustados se quiser.

5. Rode o aplicativo principal
bash
Copy code
cd ~/pi_productivity
source .venv/bin/activate
python main.py
Aparecem mensagens como:

scss
Copy code
[Auto] Postura ligada (cada 120s)
[Auto] OCR ligado (cada 30s)
[Auto] Hidratação ligada (cada 40 min)
6. Entenda os controles do Sense HAT
Cima / Baixo: troca de modo (trabalho, estudo, lazer, tarefas, postura, OCR).

Direita: executa postura (modo POSTURA) ou OCR (modo OCR NOTAS) na hora.

Esquerda: reservado para atualizar o e-paper quando estiver instalado.

Sinais visuais:

Postura OK pisca verde; ajuste necessário pisca vermelho.

OCR concluído pisca ciano.

Lembrete de hidratação mostra uma gota azul-clara.

7. Onde ficam os arquivos
Imagens e textos do OCR: ~/pi_productivity/notes/.

Logs de postura diários: ~/pi_productivity/logs/posture_YYYYMMDD.txt.

CSVs cumulativos:

Postura: ~/pi_productivity/logs/posture_events.csv.

OCR/Tarefas: ~/pi_productivity/logs/task_events.csv.

8. Relatórios opcionais
Gere gráficos e correlações:

bash
Copy code
cd ~/pi_productivity
source .venv/bin/activate
python analyze_productivity.py
Os resultados ficam em ~/pi_productivity/analytics/.

9. Ajuda rápida
Reinstalar pacotes principais (caso algo falhe):

bash
Copy code
sudo apt install -y python3-picamera2 python3-opencv python3-numpy python3-simplejpeg
Conferir o arquivo da câmera do OpenCV: /usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml.

Sem interface gráfica? Copie arquivos com:

bash
Copy code
scp pi@IP_DO_PI:/home/pi/pi_productivity/last_posture.jpg .
Motion retornou erro 401/400? Revise MOTION_API_KEY no .env. Teste rápido:

bash
Copy code
python - <<'PY'
import os, requests
from dotenv import load_dotenv
load_dotenv("/home/pi/pi_productivity/.env")
api=os.getenv("MOTION_API_KEY")
print(requests.get("https://api.usemotion.com/v1/tasks",
                   headers={"X-API-Key": api}, timeout=15).status_code)
PY
10. Display e-paper opcional
Com o display Waveshare 1,53" conectado via SPI:

```
source ~/pi_productivity/.venv/bin/activate
python epaper_display.py --limit 6
```

O script lê tarefas do banco `~/pi_productivity/data/tasks.db`. O banco é atualizado automaticamente a cada alguns minutos (valor ajustável por `MOTION_SYNC_INTERVAL_SEC`) sempre que o app principal consegue acessar a Motion API. Caso queira rodar manualmente, você pode popular o banco via `TaskDatabase` ou inserir tarefas diretamente na tabela `tasks`.

Para personalizar:

- `EPAPER_ENABLE=0` desativa as atualizações automáticas.
- `EPAPER_ROTATE_180=1` gira a renderização quando o display estiver invertido.
- `EPAPER_OUTPUT_PATH` muda o arquivo PNG gerado (padrão `/mnt/data/pi_productivity/last_epaper.png`).

11. Comandos úteis do dia a dia
bash
Copy code
# Ativar o ambiente virtual
source ~/pi_productivity/.venv/bin/activate

# Rodar o app principal
python ~/pi_productivity/main.py

# Rodar a análise
python ~/pi_productivity/analyze_productivity.py

# Editar configurações
nano ~/pi_productivity/.env
12. Interface Web (opcional)
Para iniciar o painel FastAPI:

bash
Copy code
pip install fastapi "uvicorn[standard]" jinja2 watchdog opencv-python numpy
cd ~/pi_productivity
source .venv/bin/activate
python WebApp
# ou
uvicorn WebApp:app --host 0.0.0.0 --port 8090
ruby
Copy code

Esta versão reorganiza as mesmas funcionalidades, comandos e caminhos já documentados no README atual do projeto.​:codex-file-citation[codex-file-citation]{line_range_start=18 line_range_end=291 path=README.md git_url="https://github.com/alebmorais/pi_productivity/blob/main/README.md#L18-L291"}​

Testing:
⚠️ Não executado (análise apenas de documentação).

