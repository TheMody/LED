#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.


import sounddevice as sd
import numpy as np
import time
from rpi_ws281x import PixelStrip, Color
import argparse
import queue
#from test import SpectralBasedOnsets, AmplitudeBasedOnsets
from utils import AmplitudeBasedOnsets, processAmplitutde, AmplitudeBasedOnsets_from_processed

# LED strip configuration:
LED_COUNT = 16        # Number of LED pixels.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
test = True
save_intervall = 4
fs=44100

if test:
    import matplotlib.pyplot as plt


# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


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

def modulate_by_max(sound, intervall = 1000):
    return np.max(np.abs(sound[-intervall:]))/np.max(np.abs(sound))

def modulate_by_mean(sound, intervall = 1000):
    return np.mean(np.abs(sound[-intervall:]))/np.max(np.abs(sound))

def detect_sudden_change(sound, threshold = 1.0):
    avg_now = np.mean(np.abs(sound[-1000:])) 
    avg_before = np.mean(np.abs(sound)) 
    return avg_now  > (1 +threshold)* avg_before or avg_now  <  (1-threshold)* avg_before

    

# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    if not test:
        strip.begin()
    mode = 0

    print('Press Ctrl-C to quit.')
    try:
        soundarray = np.asarray([0])#*int(fs*save_intervall/2))
        
        bin_number = 400
        waittime = time.time()
        waittime2 = time.time()
        waittime3 = time.time()
        j = 0
        beta1 = 0.99999
        beta2 = 0.9999
        beta3 = 0.999
        time_window = 256
        running_avg_long = 0.01
        running_avg_medium = 0.01
        running_avg_short = 0.01
        un_processed_beats = np.asarray([])
        processed_beats = np.asarray([])#[0]*int(fs * save_intervall / time_window))
        previous_length = 0

        def callback(indata, frames, time, status):
            global soundarray
          #  print(len(indata))
            print(len(soundarray))
            soundarray = np.append(soundarray, indata[np.arange(0, len(indata), 2)])
          #  un_processed_beats = np.append(un_processed_beats, indata[np.arange(0, len(indata), 2)])
           # new_data = new_data + int(len(indata)/2)
            # for i in indata:
            #     i = abs(i)
            #     running_avg_long = running_avg_long * beta1 + i *(1-beta1)
            #     running_avg_medium = running_avg_medium * beta2 + i *(1-beta2)
            #     running_avg_short = running_avg_short * beta3 + i *(1-beta3)

        q = queue.Queue()


        def audio_callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            # if status:
            #     print(status, file=sys.stderr)
            # Fancy indexing with mapping creates a (necessary!) copy:
            q.put(indata[::2, 0])

        print("samplerate: ", fs)
        fulltime = time.time()
        with sd.InputStream(channels=1, samplerate=fs, callback=audio_callback) :
            while True:	 
                indata = stream.read(stream.read_available)[0]

                for i in indata:
                    i = abs(i)
                    running_avg_long = running_avg_long * beta1 + i *(1-beta1)
                    running_avg_medium = running_avg_medium * beta2 + i *(1-beta2)
                    running_avg_short = running_avg_short * beta3 + i *(1-beta3)
                soundarray = np.append(soundarray, indata[np.arange(0, len(indata), 2)])
                un_processed_beats = np.append(un_processed_beats, soundarray[previous_length:])
                previous_length = len(soundarray)
                if len(soundarray) > save_intervall*fs/2:
                    soundarray = soundarray[-int(fs*save_intervall/2):]

                

                if len(soundarray) > int(0.1*fs):
                # lvl = np.mean(np.abs(soundarray[-1000:]))
                    plt.plot(soundarray)
                    plt.show()
                    if test:
                        start = time.time()
                      #  print(len(un_processed_beats))
                       # print(len(soundarray))
                        if len(un_processed_beats)> time_window*2:
                            processed_beats = np.append(processed_beats, processAmplitutde(un_processed_beats))
                            print(len(processAmplitutde(un_processed_beats)))
                           # processed_beats.append(processAmplitutde(un_processed_beats))
                           # print("before",len(un_processed_beats))
                            un_processed_beats = un_processed_beats[ -(time_window + len(un_processed_beats) % time_window):]
                          #  print("after",len(un_processed_beats))
                      # print(len(processed_beats))
                        if len(processed_beats) > fs * save_intervall / time_window:
                            print("time to full", time.time()-fulltime)
                            processed_beats = processed_beats[-int(fs * save_intervall / time_window):]
                           # print(len(un_processed_beats))
                       # print("stuff") 
                      #  print("processed_beats", processed_beats)
                     #   start = time.time()
                        onsets, size = AmplitudeBasedOnsets_from_processed(processed_beats, distance=10, prominence=0.4, window_size=512)#, displayAll=True)
                     #   print("time to process", time.time()-start)
                     #   print(onsets)
                        # if len(onsets) > 0:
                        #     if onsets[-1] > len(processed_beats) - 10:
                        #         print("onset", size[-1])
                     #   onsets, size = AmplitudeBasedOnsets(soundarray, distance=10, prominence=0.4, window_size=512)#, displayAll=True)
                      #  print("time to process", time.time()-start)
                       # print("onsets", onsets, size)
                       # print(onsets)
                         #time_diff = time.time()-start
                        # print(time_diff)
                    #    print(time.time()-start)
                      #  print(onsets)
                        # if len(onsets) > 0 :
                        #     if onsets[-1] >  (len(soundarray) - 1025):# and size[-1]  >= 0.99:
                        #         print("onset", onsets, size)
                    #         # else:
                            #     print("no")
                      #  print(onsets)

                      #  AmplitudeBasedOnsets(soundarray, distance=10, prominence=0.1)
                        # fft = np.fft.fft(soundarray)
                        

                        # #print(fft.shape)
                        # if len(fft)>=4*fs:
                        #     binwidth = int(save_intervall*fs/bin_number)
                        #     fft_binned = [np.mean(np.abs(fft.real[i*binwidth:(i+1)*binwidth])) for i in range(int(len(fft)/binwidth))] 
                        #     fftsmall = np.abs(fft.real)[int(0.1*fs):int(0.3*fs)]
                        #     fftmedium = np.abs(fft.real)[int(0.3*fs):int(1*fs)]
                        #     fftbig = np.abs(fft.real)[int(1*fs):int(3*fs)]
                        #     print("ffts")
                        #     print((np.argmax(fftsmall)+ int(0.1*fs) ) / fs)
                        #     print((np.argmax(fftmedium)+ int(0.3*fs) ) / fs)
                        #     print((np.argmax(fftbig)+ int(1*fs) ) / fs)
                            
                        #     print((np.argmax(fft_binned[int(0.1*fs/bin_number):int(0.3*fs/bin_number)])*binwidth + int(0.1*fs) )/fs)
                        #     print((np.argmax(fft_binned[int(0.3*fs/bin_number):int(1*fs/bin_number)])*binwidth + int(0.3*fs) )/fs)
                        #     print((np.argmax(fft_binned[int(1*fs/bin_number):int(2*fs/bin_number)])*binwidth + int(1*fs) )/fs)
                      #  ind = np.argpartition(fft, -4)[-4:]
                       # top4 = (ind+ int(0.01*fs))/fs
                     #   print(top4)
                      #  print((np.argmax(fft)+ int(0.01*fs))/fs)
                      #  print(time.time()-start)
                        
                            # plt.plot(fft_binned)
                            # plt.show()
                      #      print(wheel( (int(i*(255/strip.numPixels)+255/ 5 * j)) & 256))
                  #  lvl = modulate_by_max(soundarray)# * running_avg
                   # lvl = modulate_by_mean(soundarray)
                    lvl = running_avg_short/running_avg_long -0.5
                    bright = int(min(255,max(0,int(lvl*255 ))))
                  #  print("lvl",lvl)
                    if not test:
                        if mode == 1:
                          #  if time.time()-waittime2 > 0.2:
                            #    waittime2 = time.time()
                               # for j in range(256 * 5):
                           #     j = j+1
                                rainpowpos = 20
                                if j> rainpowpos:
                                    j = 0
                                for i in range(strip.numPixels()):
                                    color =  wheel( (int(i*(255/strip.numPixels())+255/ rainpowpos * j)) % 255)
                                  #  print(color)
                                    color = Color(int(color[0]),int(color[1]),int(color[2]))
                                    strip.setPixelColor(i, color)
                                strip.show()
                        if mode == 0:
                            for i in range(strip.numPixels()):
                                strip.setPixelColor(i,  Color(bright, bright, bright))
                            strip.show()
                        start = time.time()
                      #  onsets, size = AmplitudeBasedOnsets(soundarray, distance=10, prominence=0.3, window_size=512)
                       # print(time.time()-start)
                      #  print(len(soundarray))
                        # if len(onsets) > 0 :
                        #     if onsets[-1] >  (len(soundarray) - new_data) and ((time.time()-waittime) > 2000/fs):
                        #        # print("onset", onsets, size)
                        #      #   print("TIMEsince lasts",(time.time()-waittime) )
                        #         waittime = time.time()
                        #       #  print("onset", onsets, size)
                        #         j = j+1
                        if detect_sudden_change(soundarray) & ((time.time()-waittime2) > 0.500):
                            mode = mode +1
                            waittime2 = time.time()
                            if mode >0:
                                mode = 0
                
           #     print("new data", len(soundarray))
            #    print("time since last", time.time()-waittime3)
                waittime3 = time.time()
                new_data = 0

        while True:
            print('Color wipe animations.')
            colorWipe(strip, Color(255, 0, 0))  # Red wipe
            colorWipe(strip, Color(0, 255, 0))  # Green wipe
            colorWipe(strip, Color(0, 0, 255))  # Blue wipe
            print('Theater chase animations.')
            theaterChase(strip, Color(127, 127, 127))  # White theater chase
            theaterChase(strip, Color(127, 0, 0))  # Red theater chase
            theaterChase(strip, Color(0, 0, 127))  # Blue theater chase
            print('Rainbow animations.')
            rainbow(strip)
            rainbowCycle(strip)
            theaterChaseRainbow(strip)

    except KeyboardInterrupt:
        colorWipe(strip, Color(0, 0, 0), 10)
