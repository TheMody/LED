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
#from test import SpectralBasedOnsets, AmplitudeBasedOnsets

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

def detect_sudden_change(sound):
    return np.mean(np.abs(sound)) *1.7  <  np.mean(np.abs(sound[-1000:]))

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
        soundarray = np.asarray([0])
        save_intervall = 4
        fs=22050
        bin_number = 400
        waittime = time.time()
        waittime2 = time.time()
        j = 0
        beta1 = 0.99999
        beta2 = 0.9999
        beta3 = 0.999
        running_avg_long = 0.0
        running_avg_medium = 0.0
        running_avg_short = 0.0

        def callback(indata, frames, time, status):
            global soundarray, running_avg_long, running_avg_short, running_avg_medium
            soundarray = np.append(soundarray, indata)
            for i in indata:
                i = abs(i)
                running_avg_long = running_avg_long * beta1 + i *(1-beta1)
                running_avg_medium = running_avg_medium * beta2 + i *(1-beta2)
                running_avg_short = running_avg_short * beta3 + i *(1-beta3)
            if len(soundarray) > save_intervall*fs:
                soundarray = soundarray[int(-save_intervall*fs):]

        with sd.InputStream(channels=1, callback=callback,  samplerate=fs):
            while True:	 
            #     myrecording = sd.rec(int(buffer_intervall * fs), samplerate=fs, channels=1)
            #     sd.wait()
            #     myrecording = np.asarray(myrecording)
            #     soundarray = np.append(soundarray, myrecording)
            #     myrecording = sd.rec(int(buffer_intervall * fs), samplerate=fs, channels=1)
            #     if len(soundarray) > save_intervall*fs:
            #         soundarray = soundarray[int(-save_intervall*fs):]
            # #  print(np.max(soundarray[-1000:]))
                if len(soundarray) > int(0.1*fs):
                # lvl = np.mean(np.abs(soundarray[-1000:]))

                  #  if test:
                    # plt.plot(soundarray)
                    # plt.show()
                       # start = time.time()
                        #print(soundarray.shape)
                      #  print(detect_sudden_change(soundarray))
                    #     hop_length = 256
                    #     # tempo, beats = librosa.beat.beat_track(y=soundarray, sr=fs, hop_length=hop_length)
                    #     # print("tempo", tempo)
                    #     # print("beats", beats)
                    #     # plt.plot(soundarray)
                    #     # plt.title("Signal with Beats")
                    #     # beats = beats*hop_length
                    #     # for k in range(len(beats)):
                    #     # #  if(beats[k] < SR):
                    #     #     plt.plot([beats[k],beats[k]],[-1,1],color='r')    
                    #     # plt.show()
                    #     start = time.time()
                    #     onsets = AmplitudeBasedOnsets(soundarray, distance=10, prominence=0.4, window_size=512)#, displayAll=True)
                    #    # print(onsets)
                    #     time_diff = time.time()-start
                    #   #  print(time_diff)
                    #    # print(time.time()-start)
                    #   #  print(onsets)
                    #     if len(onsets) > 0 :
                    #         if onsets[-1] >  (len(soundarray) - 1000):
                    #             print("onset", onsets)
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
                    lvl = running_avg_short/running_avg_long 
                    bright = int(min(255,max(0,int(lvl*127.5 ))))
                    print("lvl",lvl)
                    if not test:
                        if mode == 0:
                            if time.time()-waittime2 > 0.2:
                                waittime2 = time.time()
                               # for j in range(256 * 5):
                                j = j+1
                                if j> 10:
                                    j = 0
                                for i in range(strip.numPixels()):
                                    color =  wheel( (int(i*(255/strip.numPixels())+255/ 5 * j)) & 255)
                                  #  print(color)
                                    color = Color(int(color[0]*lvl),int(color[1]*lvl),int(color[2]*lvl))
                                    strip.setPixelColor(i, color)
                                strip.show()
                        if mode == 1:
                            for i in range(strip.numPixels()):
                                strip.setPixelColor(i,  Color(bright, bright, bright))
                            strip.show()
                        
                        # onsets = AmplitudeBasedOnsets(soundarray,distance=10, prominence=0.4)
                        # if len(onsets) > 0 :
                        #     if onsets[-1] >  (len(soundarray) - 1000):
                        #         print("onset", onsets)
                        if detect_sudden_change(soundarray) & ((time.time()-waittime) > 0.500):
                            mode = mode +1
                            waittime = time.time()
                            if mode >1:
                                mode = 0

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
