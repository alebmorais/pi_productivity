
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

### Novos modos (joystick)
- **POSTURA**: selecione o modo e pressione **Direita** para medir.  
  - Verde = postura ok; Vermelho = precisa ajustar.  
  - Última imagem salva em: `/mnt/data/pi_productivity/last_posture.jpg`

- **OCR NOTAS**: selecione o modo e pressione **Direita** para capturar e extrair texto.  
  - Arquivos gerados em `/mnt/data/pi_productivity/notes/` (PNG + TXT).

> A detecção de postura é heurística e leve (Haar cascades + gradientes). Podemos trocar por um modelo de landmarks caso queira algo mais preciso.
