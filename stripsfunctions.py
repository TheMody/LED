from rpi_ws281x import PixelStrip, Color
import time
import numpy as np


#LED_COUNT = 16        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        #time.sleep(wait_ms / 1000.0)


def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, color)
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return (pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return (255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return (0, pos * 3, 255 - pos * 3)


def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i + j) & 255))
        strip.show()
        time.sleep(wait_ms / 1000.0)


def rainbowCycle(strip, wait_ms=20, iterations=5, lvl = 1):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256 * iterations):
        for i in range(strip.numPixels()):
            color =  wheel( (int(i * 256 / strip.numPixels()) + j) & 255)
            color = Color(int(color[0]*lvl),int(color[1]*lvl),int(color[2]*lvl))
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)

def blink(strip, wait_time = 100):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i,  Color(255,255,255))
    strip.show()
    time.sleep(wait_time/1000.0)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0,0,0))
    strip.show()	

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, wheel((i + j) % 255))
            strip.show()
            time.sleep(wait_ms / 1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i + q, 0)


#test layout is 2x3x3
testlayout = [[3,3,3],[3,3,3]]
colors = 30, 34, 35, 91, 93, 97
chars = ' :%#\t#%:'
vishelper =  []
for bg, fg in zip(colors, colors[1:]):
    for char in chars:
        if char == '\t':
            bg, fg = fg, bg
        else:
            vishelper.append(f'\x1b[{fg};{bg + 10}m{char}')

class stripManager():

### layout is an array of chunks defining the strip configuration:
    # strips are configured in chunks which are defined as 2D arrays which are defining the number of strips as well as the number of pixels per strip
    def __init__(self, layout,samplerate ,fftsize, low_bin,test = False, gain = 10):
        self.layout = layout
        self.chunks = [chunk for chunk in self.layout]
        self.lines = [line for chunk in self.layout for line in chunk]
        self.max_length = np.max(self.lines)

        print("max_length", self.max_length)
        self.gain = gain
        self.low_bin = low_bin
        self.samplerate = samplerate
        self.fftsize = fftsize
        self.num_leds = np.sum(self.layout)
        self.mode = "fillchunksbyspekto"
        self.pixel_values = [[[0 for pixel in range(line)] for line in chunk] for chunk in self.layout]
        #[[ PixelStrip(self.num_leds, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
         #for led_count in chunk] for chunk in self.layout ]
        #PixelStrip(300, 18, 800000, 5, False, 255, 0)
        if not test:    
            self.visualizeascii = False
            self.strip = PixelStrip(int(self.num_leds), LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
            self.strip.begin()
        else:
            self.visualizeascii = True
        self.waittime =  time.time()
        self.long_avg = 100
        
        self.spektohist = np.zeros((200,self.num_leds))
        self.meanmeanfreq = 0

    def visualize(self,indata):
        beta = 0.9
        magnitude = np.abs(np.fft.rfft(indata[:, 0], n=self.fftsize))
        magnitude *= self.gain / self.fftsize
        spektogram = np.clip(magnitude[self.low_bin:self.low_bin + self.num_leds], 0, 1)
        self.spektohist = np.append(self.spektohist, [spektogram], axis=0)
        if self.spektohist.shape[0] > 200:
            self.spektohist = np.delete(self.spektohist, 0, 0)
        if np.mean(spektogram[:int(self.num_leds/16)]) > 0.3:
            print("bass")
        
        #print(len(find_peaks(spektogram,0.4,10)))
        spektosum = np.sum(spektogram)
        meanfreq = np.sum(spektogram/spektosum * np.arange(0,len(spektogram)))
       # meanmeanfreq = meanmeanfreq*beta + meanfreq*(1-beta)
        #  print(meanmeanfreq)
        self.long_avg = self.long_avg*beta + np.sum(magnitude)*(1-beta)
        # print(long_avg)
        if self.long_avg < 3 and self.waittime + 2 < time.time():
            self.gain *= 1.5
            self.waittime = time.time()
            print("adjusted gain to", self.gain)
        if self.long_avg > 8 and self.waittime + 2 < time.time():
            self.gain /= 1.5
            self.waittime = time.time()
            print("adjusted gain to", self.gain)

        if self.mode == "fillchunksbyspekto":
              for k,chunk in enumerate(self.layout):
                    printline = ""
                    for a,line in enumerate(chunk):
                            self.pixel_values[k][a] = [np.mean(self.spektohist[-((a+1)*5+1):-((a)*5+1),int(i*len(spektogram)/line):int((i+1)*len(spektogram)/line)], axis = (0,1)) for i in range(line)]
        
        if self.mode == "fillchunksbymag":
              for k,chunk in enumerate(self.layout):
                    printline = ""
                    for a,line in enumerate(chunk):
                            self.pixel_values[k][a] = [np.mean(self.spektohist[-((a+1)*5+1):-((a)*5+1),:], axis = (0,1))*3 for i in range(line)]

        if self.mode == "fillchunksbymagcurrent":
              for k,chunk in enumerate(self.layout):
                    printline = ""
                    for a,line in enumerate(chunk):
                            self.pixel_values[k][a] = [np.mean(self.spektohist[0], axis = (0))*3 for i in range(line)]
        
        
        if self.visualizeascii:
            for k,chunk in enumerate(self.layout):
                    printline = ""
                    for a,line in enumerate(chunk):
                          
                          #  print(self.pixel_values[k][a][i])
                         #   printline = printline + "".join([str(x) + " " for x in self.pixel_values[k][a]]) + "\n"
                            printline = printline + "".join([vishelper[int(x * (len(vishelper) - 1))] for x in self.pixel_values[k][a]]) + "\n"  
                    print(printline, sep='')

        else:
        #    print("test")
            pos = 0
            for k,chunk in enumerate(self.layout):
                for a,line in enumerate(chunk):
                    for i in range(line):
                        color = Color(int(self.pixel_values[k][a][i]*255),int(self.pixel_values[k][a][i]*255),int(self.pixel_values[k][a][i]*255))
                        if not pos  >= self.num_leds: 
                            self.strip.setPixelColor(pos, color)
                        pos = pos + 1
                self.strip.show()
            #     time.sleep(0.01)
            # for i in range(self.strip.numPixels()):
            #     self.strip.setPixelColor(i,  Color(255, 255, 255))
            # self.strip.show()

    def __delete__(self):
        colorWipe(self.strip, Color(0, 0, 0))
        super.__delete__(self)
        
        