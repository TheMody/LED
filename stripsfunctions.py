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

allmodes = ["fillchunksbyspekto", "fillchunksbymag", "fillchunksbymagcurrent"]
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

def average_into_bins(arr, n_bins):
    # Ensure the array can be divided into bins evenly
  #  bin_size = len(arr) // n_bins
    # Reshape the array to have n_bins rows and bin_size columns
  #  reshaped_arr = arr[:bin_size * n_bins].reshape(n_bins, bin_size)
    bin_length = 2
    bins = []
    pos = 0
    for i in range(0,n_bins):
        bins.append(arr[pos:int(pos+bin_length)].mean())
        pos += int(bin_length)
        bin_length *= 1.15
        #print(pos)
    # Calculate the mean for each bin
    bin_averages = np.asarray(bins)
    return bin_averages

class stripManager():

### layout is an array of chunks defining the strip configuration:
    # strips are configured in chunks which are defined as 2D arrays which are defining the number of strips as well as the number of pixels per strip
    def __init__(self, layout, stripoffset,samplerate ,fftsize, low_bin,test = False, gain = 10):
        self.layout = layout
        self.stripoffset = stripoffset
        self.chunks = [chunk for chunk in self.layout]
        self.max_width = np.max([len(chunk) for chunk in self.layout])
        self.lines = [line for chunk in self.layout for line in chunk]
        self.max_length = np.max(self.lines)
        print("max_length", self.max_length, "max_width", self.max_width)
        self.gain = gain
        self.low_bin = low_bin
        self.samplerate = samplerate
        self.fftsize = fftsize
        self.num_leds = np.sum([np.sum(partiallayout) for partiallayout in self.layout])
        self.max_value = 0
        print("num_leds", self.num_leds)
        self.mode = "startup"#"fillchunksbyspekto"
        self.startuptime = 0
        self.pixel_values = np.zeros((self.max_width,self.max_length))
        if not test:    
            self.visualizeascii = False
            self.strip = PixelStrip(int(self.num_leds), LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
            self.strip.begin()
        else:
            self.visualizeascii = True
            import visualizer
            self.displays = visualizer.display()

        self.waittime =  time.time()
        self.long_avg = 100
        
        self.spektohist = np.zeros((20,12))
        self.meanmeanfreq = 0

    def changevisualization(self):
        for i in range(len(allmodes)):
            if self.mode == allmodes[i]:
                if i == len(allmodes) - 1:
                    self.mode = allmodes[0]
                else:
                    self.mode = allmodes[i+1]
                break



    def visualize(self,indata):
        starttime = time.time()
        beta = 0.9
        magnitude = np.abs(np.fft.rfft(indata, n=self.fftsize))

        #average the magnitude over the bins
        spektogram = average_into_bins(magnitude[:70], self.max_length)
     #   print(spektogram)

      #  print("time it took for fft", time.time() - starttime)
       # starttime = time.time()

        self.spektohist = np.append(self.spektohist, [spektogram], axis=0)
        if self.spektohist.shape[0] > 20:
            self.spektohist = np.delete(self.spektohist, 0, 0)

        #print("time it took for stuff", time.time() - starttime)
        #starttime = time.time()
        if self.mode == "startup":
            #for i in range(self.max_width):
            for a in range(self.max_length):
                self.pixel_values[:,-a-1] =  1 if a <= self.startuptime else 0#np.mean(self.spektohist[-i,:])
        self.startuptime += 1
        if self.startuptime >= self.max_length+5:
            self.mode = "fillchunksbyspekto"
            self.startuptime = 0
        if self.mode == "fillchunksbyspekto":
            for i in range(self.max_width):
                self.pixel_values[i,:] =  self.spektohist[-i-1,:]
 
        if self.mode == "fillchunksbymag":
            for i in range(self.max_width):
                self.pixel_values[i,:] =  np.mean(self.spektohist[-i-1,:])

        if self.mode == "fillchunksbymagcurrent":
            for i in range(self.max_width):
                self.pixel_values[i,:] =  np.mean(self.spektohist[-1,:])
            self.max_value = 0.98 * self.max_value + 0.02 * np.max(self.pixel_values)
            self.pixel_values = self.pixel_values / self.max_value
            self.pixel_values = np.clip(self.pixel_values, 0, 1)
        else:
       # print("time it took for pixel wise assignemnt", time.time() - starttime)
       # starttime = time.time()
            max_val = np.max(self.pixel_values)
            min_val = np.min(self.pixel_values)
            self.max_value *= 0.96
            self.max_value = max(self.max_value, max_val)
            max_val = self.max_value
            if not max_val - min_val <= 0:
                self.pixel_values = (self.pixel_values - min_val)/(max_val - min_val)
        # if np.min(self.pixel_values) < 0:
        #     print("min value is", np.min(self.pixel_values))
        # if np.max(self.pixel_values) > 1:
        #     print("max value is", np.max(self.pixel_values))
            #self.pixel_values = self.pixel_values - np.min(self.pixel_values)
     #   print("time it took for normalization", time.time() - starttime)
      #  starttime = time.time()

        self.pixel_values *= 255
        self.pixel_values = np.asarray(self.pixel_values, dtype = int)
        if self.visualizeascii:

            self.displays.draw(self.pixel_values/255.0, layout = self.layout, stripoffset = self.stripoffset)
            # for k,chunk in enumerate(self.layout):
            #         printline = ""
            #         for a,line in enumerate(chunk):
            #          #   print(self.pixel_values[k,a])
            #             printline = printline + "".join([vishelper[int(self.pixel_values[a,x] * (len(vishelper) - 1))] for x in range(line)]) + "\n"  
            #         print(printline, sep='')

        else:
            pos = 0
            for k,chunk in enumerate(self.layout):
                invert = True
                for a,line in enumerate(chunk):
                    invert = not invert
                    for i in range(line):
                        x = a
                        y = i + self.stripoffset[k][a]
                        if invert:
                            color = Color(self.pixel_values[x,-y-1],self.pixel_values[x,-y-1],self.pixel_values[x,-y-1])
                        else:
                            color = Color(self.pixel_values[x,y],self.pixel_values[x,y],self.pixel_values[x,y])
                        if not pos  >= self.num_leds: 
                            self.strip.setPixelColor(pos, color)
                        pos = pos + 1
                self.strip.show()
     #   print("time it took for visualization", time.time() - starttime)
      #  starttime = time.time()

    def __delete__(self):
        colorWipe(self.strip, Color(0, 0, 0))
        super.__delete__(self)
        
        