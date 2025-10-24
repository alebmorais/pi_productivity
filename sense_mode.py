import time, threading, math

class MockSenseHat:
    """A mock class for SenseHat for development on non-Raspberry Pi machines."""
    def __init__(self):
        self.low_light = False
        self.pixels = [[0,0,0]] * 64
        self.stick = None
        self.stick = None

    def get_temperature(self):
        return 22.5
    
    def get_humidity(self):
        return 45.0
    
    def get_pressure(self):
        return 1013.0

    def get_temperature(self):
        return 22.5
    
    def get_humidity(self):
        return 45.0
    
    def get_pressure(self):
        return 1013.0

    def get_accelerometer_raw(self):
        return {'x': 0.0, 'y': 0.0, 'z': 1.0}

    def set_pixels(self, pixels):
        self.pixels = pixels
        print("[MockSenseHat] Set pixels.")

    def clear(self, color=None):
        color = color or [0,0,0]
        print(f"[MockSenseHat] Cleared display with color {color}.")

    def show_letter(self, letter, text_colour=None, back_colour=None):
        print(f"[MockSenseHat] Displayed letter '{letter}'.")

try:
    from sense_hat import SenseHat
    sense = SenseHat()
    sense.low_light = True
except (ImportError, RuntimeError):
    print("Warning: 'sense_hat' library not found or failed to initialize. Using mock display.")
    sense = MockSenseHat()

BLACK = [0,0,0]
WHITE = [255,255,255]
RED = [255,0,0]
GREEN = [0,255,0]
BLUE = [0,0,255]

def rainbow_colors(i):
    i = i % 256
    if i < 85:
        return [i*3, 255 - i*3, 0]
    elif i < 170:
        i -= 85
        return [255 - i*3, 0, i*3]
    else:
        i -= 170
        return [0, i*3, 255 - i*3]

def show_rainbow(pulse=False, step=5, duration=0.1):
    for i in range(0,256,step):
        c = rainbow_colors(i)
        if pulse:
            sense.clear(c if i % (step*2) == 0 else BLACK)
        else:
            sense.clear(c)
        time.sleep(duration)

ROBOT_FRAMES = [
    [
        0,0,1,1,1,1,0,0,
        0,1,0,0,0,0,1,0,
        1,0,1,0,0,1,0,1,
        1,0,0,0,0,0,0,1,
        1,0,1,1,1,1,0,1,
        1,0,0,1,1,0,0,1,
        0,1,0,0,0,0,1,0,
        0,0,1,1,1,1,0,0,
    ],
    [
        0,0,1,1,1,1,0,0,
        0,1,0,0,0,0,1,0,
        1,0,0,1,1,0,0,1,
        1,0,0,0,0,0,0,1,
        1,0,1,1,1,1,0,1,
        1,0,1,0,0,1,0,1,
        0,1,0,0,0,0,1,0,
        0,0,1,1,1,1,0,0,
    ]
]

def draw_frame(frame, color=WHITE, bg=BLACK):
    pixels = []
    for v in frame:
        pixels.append(color if v else bg)
    sense.set_pixels(pixels)

def animate_robot(times=6, delay=0.15):
    for _ in range(times):
        for f in ROBOT_FRAMES:
            draw_frame(f)
            time.sleep(delay)
    sense.clear()

class BaseTimerMode:
    '''Base para modos com cronômetro/ciclos'''
    def __init__(self):
        self._running = False
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self._running: 
                return
            self._running = True
            self._thread = threading.Thread(target=self.run, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False
        sense.clear()

    def is_running(self):
        with self._lock:
            return self._running

    def run(self):
        raise NotImplementedError

class HapvidaMode(BaseTimerMode):
    '''Timer de 1h, no fim anima robô'''
    def run(self):
        start = time.time()
        duration = 60*60
        while self.is_running():
            elapsed = time.time() - start
            if elapsed >= duration:
                animate_robot(times=10, delay=0.1)
                start = time.time()
            else:
                pct = elapsed / duration
                bars = int(pct * 8)
                pixels = []
                for y in range(8):
                    row = []
                    for x in range(8):
                        row.append(GREEN if x < bars else BLACK)
                    pixels += row
                sense.set_pixels(pixels)
                time.sleep(2)

class CarePlusMode(BaseTimerMode):
    '''Ciclos de 30 min; arco-íris pisca nos últimos 5 min'''
    def run(self):
        block = 30*60
        warn = 5*60
        start = time.time()
        while self.is_running():
            elapsed = time.time() - start
            remaining = block - elapsed
            if remaining <= 0:
                sense.clear(WHITE); time.sleep(0.5)
                sense.clear(BLACK); time.sleep(0.5)
                start = time.time()
                continue
            if remaining <= warn:
                show_rainbow(pulse=True, step=16, duration=0.08)
            else:
                pct = elapsed / block
                bars = int(pct * 8)
                pixels = []
                for y in range(8):
                    row = []
                    for x in range(8):
                        row.append(BLUE if x < bars else BLACK)
                    pixels += row
                sense.set_pixels(pixels)
                time.sleep(2)

class StudyADHDMode(BaseTimerMode):
    '''Pomodoro adaptado: 20 foco (verde) + 10 pausa (azul)'''
    def run(self):
        FOCUS = 20*60
        BREAK = 10*60
        while self.is_running():
            start = time.time()
            while self.is_running() and (time.time()-start) < FOCUS:
                elapsed = time.time()-start
                remain = FOCUS - elapsed
                if remain <= 60:
                    sense.clear([255,255,0]); time.sleep(0.5)
                    sense.clear(BLACK); time.sleep(0.5)
                else:
                    sense.clear(GREEN); time.sleep(1)
            if not self.is_running(): break
            start = time.time()
            while self.is_running() and (time.time()-start) < BREAK:
                sense.clear([0,0,128]); time.sleep(1)
        sense.clear()

class LeisureMode(BaseTimerMode):
    '''Animação de respiração/relax'''
    def run(self):
        t = 0.0
        while self.is_running():
            val = int((1 + math.sin(t))*127)
            sense.clear([0,0,val])
            time.sleep(0.08)
            t += 0.2

def check_for_movement():
    acceleration = sense.get_accelerometer_raw()
    x = acceleration['x']
    y = acceleration['y']
    z = acceleration['z']

    x = abs(x)
    y = abs(y)
    z = abs(z)

    if x > 1 or y > 1 or z > 1:
        sense.show_letter("!")
    else:
        sense.clear()
