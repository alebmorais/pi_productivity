# Pi Productivity Hub

Um hub de produtividade pessoal rodando em um Raspberry Pi. Este projeto integra, de maneira simples, hardware e software para ajudar no foco, organização e captura de notas:

- **Sense HAT** — 6 modos de trabalho com controle via joystick e feedback visual LED 8×8
- **Display e-Paper (Waveshare)** — para mostrar status e tarefas
- **Análise de postura** — usa a câmera e OpenCV para checar postura
- **Digitalização de notas (OCR)** — converte imagens em texto com Tesseract
- **Motion API** — sincroniza tarefas automaticamente
- **Servidor web leve (FastAPI)** — interface/API para monitorar e controlar o sistema
- **Banco de dados de tarefas** — para gerenciar itens pendentes

Este README foi escrito para quem tem pouca ou nenhuma experiência em programação. Siga os passos no terminal do Raspberry Pi, um por vez.

## Pré-requisitos (hardware & software)

- Raspberry Pi (recomendado: Pi 4 ou superior)
- Raspberry Pi OS (com acesso ao desktop e ao terminal)
- **Sense HAT** conectado nos pinos GPIO
- Raspberry Pi Camera Module conectado
- Display e-Paper Waveshare (conectado via SPI)
- Python 3 instalado
- Git instalado

Execute os comandos abaixo diretamente no terminal do Raspberry Pi.

## Passo a passo de instalação

1) Clone o repositório para sua pasta pessoal:

```bash
cd ~
git clone https://github.com/alebmorais/pi_productivity.git
cd pi_productivity
```

2) Atualize o sistema e instale dependências essenciais (no Raspberry Pi OS):

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y \
  libcamera-dev \
  libcap-dev \
  python3-opencv \
  python3-spidev \
  python3-rpi.gpio \
  tesseract-ocr \
  libatlas-base-dev
```

Observações:
- O `tesseract-ocr` é necessário para a funcionalidade de OCR (pytesseract).
- Se você usar outra distribuição (Ubuntu/Debian), alguns pacotes podem ter nomes diferentes.

3) Habilite interfaces no Raspberry Pi (camera e I2C):

```bash
sudo raspi-config
```

Vá em "Interface Options" e habilite:
- Camera
- I2C

Reinicie se o sistema pedir.

4) Configure um ambiente virtual Python (recomendado):

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
```

O uso de `--system-site-packages` permite que o ambiente use pacotes do sistema (útil para bibliotecas com integração ao hardware).

5) Instale dependências Python do projeto:

```bash
pip install -r requirements.txt
```

6) Instale o driver da Waveshare e-Paper (correção do caminho):

```bash
# 1. Clone o repositório de drivers
git clone https://github.com/waveshare/e-Paper.git

# 2. Obtenha a pasta site-packages do venv
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")

# 3. Copie a biblioteca correta para o venv
cp -r e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd "$SITE_PACKAGES/"

# 4. Limpe o repositório local de drivers (opcional)
rm -rf e-Paper
```

7) Configure variáveis de ambiente e chaves

Crie seu arquivo de configuração a partir do exemplo:

```bash
cp env.example .env
nano .env
```

Edite as chaves (ex.: MOTION_API_KEY) e salve.

## Como rodar (iniciar o servidor)

Ative o ambiente virtual e rode o servidor FastAPI com Uvicorn:

```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

- --host 0.0.0.0 torna a interface acessível por outros dispositivos na mesma rede (use o IP do seu Pi).
- Acesse em: http://[IP_DO_SEU_PI]:8000

## 🎮 Modos de Trabalho do Sense HAT

O sistema possui **6 modos** que você controla pelo joystick do Sense HAT. Cada modo tem feedback visual no LED 8×8.

### Controle via Joystick

**Navegação (←→↑↓):**
- Alterna entre os 6 modos disponíveis
- Mostra uma letra colorida no Sense HAT indicando o modo ativo

**Botão do Meio (pressionar):**
- Em `posture_check`: Captura e analisa sua postura
- Em `ocr_capture`: Captura uma nota e processa OCR

### Lista de Modos

#### 1. **Posture Check** (Modo Passivo)
```
Visual: Letra "P" azul escuro
Ação: Captura postura quando apertar o botão do meio
  ✓ Postura OK → Mostra "OK" verde
  ✗ Postura ruim → Mostra "!" vermelho
Uso: Verificação manual de postura
```

#### 2. **OCR Capture** (Modo Passivo)
```
Visual: Letra "O" verde escuro
Ação: Captura nota via câmera e processa OCR
  → Mostra "T" azul após captura
  → Envia automaticamente para Motion API (se habilitado)
Uso: Digitalizar notas manuscritas rapidamente
```

#### 3. **Hapvida Mode** (Timer de 1 hora)
```
Visual: Letra "H" verde → Barra verde progressiva
Duração: 60 minutos
Alerta Final: Animação do robô (10x)
Uso: Turnos longos de trabalho focado
Progresso: Barra de 8 pixels avançando
```

#### 4. **CarePlus Mode** (Ciclos de 30 min)
```
Visual: Letra "C" azul → Barra azul progressiva
Duração: 30 minutos por ciclo
Alerta: Últimos 5 min = arco-íris piscando
Final: Flash branco/preto + reinicia ciclo
Uso: Blocos médios com avisos de tempo
```

#### 5. **Study ADHD Mode** (Pomodoro 20+10)
```
Visual: Letra "S" laranja → Verde/Azul alternado
Foco: 20 min (tela verde contínua)
  └─ Último 1 min: pisca amarelo
Pausa: 10 min (azul escuro contínuo)
Ciclo: Repete automaticamente
Uso: Estudo com TDAH - Pomodoro adaptado
```

#### 6. **Leisure Mode** (Relaxamento)
```
Visual: Letra "L" roxo → Azul pulsando
Efeito: Onda senoidal suave (respiração)
Duração: Contínua até trocar de modo
Uso: Relaxamento, meditação, pausas
```

### Exemplo de Uso

1. Ligue o sistema → Modo inicial: `posture_check` (letra "P" azul)
2. Mova joystick para a direita → Alterna para `ocr_capture` (letra "O" verde)
3. Continue navegando → `hapvida`, `careplus`, `study_adhd`, `leisure`
4. Escolha `study_adhd` → Tela mostra "S" laranja por 0.5s
5. Timer inicia → Tela fica verde (período de foco 20min)
6. Último minuto → Pisca amarelo (aviso)
7. Após 20min → Troca para azul (pausa de 10min)
8. Ciclo se repete automaticamente

### Monitoramento Automático

O sistema também executa automaticamente:

- **Sync Motion API**: A cada 15 minutos (900s) - sincroniza tarefas
- **Posture Check**: A cada 5 minutos (300s) - verifica postura automaticamente
- **E-Paper Update**: Atualiza display quando há novas tarefas

Configure os intervalos no arquivo `.env`:

```bash
MOTION_SYNC_INTERVAL=900    # Segundos entre syncs Motion
POSTURE_INTERVAL=300        # Segundos entre checks postura
OCR_INTERVAL=600            # (Não usado atualmente)
```

## 🌐 Interface Web

Acesse a interface web pelo navegador em `http://[IP_DO_PI]:8000`

### Funcionalidades

- **Dashboard em tempo real**: Temperatura, umidade, pressão do Sense HAT
- **Status do modo ativo**: Visualize qual modo está rodando
- **Lista de tarefas**: Sincronizadas automaticamente com Motion API
- **Calendário semanal**: Visualize tarefas organizadas por dia
- **Feed da câmera**: Visualização ao vivo (atualiza a cada 2s)
- **Controle de modos**: Troque o modo via dropdown
- **Captura OCR**: Botão para capturar nota manualmente

### Endpoints da API

- `GET /` - Interface principal (HTML)
- `GET /api/status` - Status completo (JSON): modo, sense, tarefas
- `POST /sense/mode` - Alterar modo programaticamente
- `POST /ocr` - Disparar captura OCR
- `GET /camera.jpg` - Frame atual da câmera
- `GET /api/week-calendar` - Calendário da semana
- `WebSocket /ws` - Updates em tempo real a cada 2s

## Protegendo a interface (login/senha básico)

A aplicação expõe dados pessoais — é recomendado adicionar autenticação básica no FastAPI. Exemplo simples à parte (incluir no código do FastAPI):

- Use dependências do FastAPI para proteger rotas com BasicAuth ou OAuth2.
- Para um começo rápido, adicione uma dependência que verifique usuário/senha antes de acessar rotas principais.

(Se quiser, eu gero um exemplo de código de autenticação básico para você inserir no `main.py`.)

## Limpeza e manutenção

- Para parar o servidor: pressione Ctrl+C no terminal onde o uvicorn está rodando.
- Para remover arquivos temporários (ex.: drivers baixados): veja os comandos acima onde usamos `rm -rf`.

## Estrutura do projeto (visão rápida)

- main.py — ponto de entrada do servidor FastAPI
- epaper.py — lógica de controle do display e-paper
- camera_posture.py — análise de postura com OpenCV
- ocr_notes.py — captura e OCR de notas (Tesseract)
- task_database.py — gerenciamento de tarefas
- requirements.txt — dependências Python

## Dicas rápidas para iniciantes

- Faça tudo com calma e copie/cole os comandos no terminal.
- Se algo der erro, copie a mensagem e pesquise; posso ajudar a interpretar.
- Guarde o arquivo `.env` com cuidado (contém chaves).
- Reinicie o Raspberry Pi se hardware não for detectado na primeira vez.

Se quiser, eu atualizo o arquivo `main.py` adicionando um exemplo de autenticação (usuário/senha) e forneço instruções passo a passo para iniciantes.
