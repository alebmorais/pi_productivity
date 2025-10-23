# Pi Productivity Hub

Um hub de produtividade pessoal rodando em um Raspberry Pi. Este projeto integra, de maneira simples, hardware e software para ajudar no foco, organização e captura de notas:

- Display e-Paper (Waveshare) — para mostrar status e tarefas.
- Análise de postura — usa a câmera e OpenCV para checar postura.
- Digitalização de notas (OCR) — converte imagens em texto com Tesseract.
- Servidor web leve (FastAPI) — interface/API para monitorar e controlar o sistema.
- Banco de dados de tarefas — para gerenciar itens pendentes.

Este README foi escrito para quem tem pouca ou nenhuma experiência em programação. Siga os passos no terminal do Raspberry Pi, um por vez.

## Pré-requisitos (hardware & software)

- Raspberry Pi (recomendado: Pi 4 ou superior)
- Raspberry Pi OS (com acesso ao desktop e ao terminal)
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
