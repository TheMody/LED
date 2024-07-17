#!/usr/bin/env python3
"""Show a text-mode spectrogram using live microphone data."""
import argparse
import math
import shutil

import numpy as np
import sounddevice as sd
#import time as pytime
from stripsfunctions import stripManager



usage_line = ' press <enter> to quit, +<enter> or -<enter> to change scaling '





def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


try:
    columns, _ = shutil.get_terminal_size()
except AttributeError:
    columns = 80

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__ + '\n\nSupported keys:' + usage_line,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    '-b', '--block-duration', type=float, metavar='DURATION', default=50,
    help='block size (default %(default)s milliseconds)')
parser.add_argument(
    '-c', '--columns', type=int, default=columns,
    help='width of spectrogram')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='input device (numeric ID or substring)')
parser.add_argument(
    '-g', '--gain', type=float, default=10,
    help='initial gain factor (default %(default)s)')
parser.add_argument(
    '-r', '--range', type=float, nargs=2,
    metavar=('LOW', 'HIGH'), default=[50, 500],
    help='frequency range (default %(default)s Hz)')
args = parser.parse_args(remaining)
#stripshape = [[6,6,6],[6,6,6],[6,6,6],[6,6,6],[6,6,6],[6,6,6]]
stripshape = [[12,12,12,10,6,3]]
striplength = np.max(stripshape)
low, high = args.range
if high <= low:
    parser.error('HIGH must be greater than LOW')

# Create a nice output gradient using ANSI escape sequences.
# Stolen from https://gist.github.com/maurisvh/df919538bcef391bc89f
colors = 30, 34, 35, 91, 93, 97
chars = ' :%#\t#%:'
gradient = []
for bg, fg in zip(colors, colors[1:]):
    for char in chars:
        if char == '\t':
            bg, fg = fg, bg
        else:
            gradient.append(f'\x1b[{fg};{bg + 10}m{char}')

try:
    samplerate = sd.query_devices(args.device, 'input')['default_samplerate']
    delta_f = (high - low) / (striplength- 1)
    fftsize = math.ceil(samplerate / delta_f)
    low_bin = math.floor(low / delta_f)
    sManager = stripManager(stripshape,samplerate, fftsize, low_bin ,test = True)
    buffer = []


    def callback(indata, frames, time, status):
        global buffer
        if status:
            text = ' ' + str(status) + ' '
            print('\x1b[34;40m', text.center(args.columns, '#'),
                  '\x1b[0m', sep='')
        if any(indata):
            buffer = buffer + list(indata[:, 0])
            if len(buffer) > 10000:
                sManager.visualize(np.asarray(buffer))
                buffer = []
            
        #     magnitude = np.abs(np.fft.rfft(indata[:, 0], n=fftsize))
        #     magnitude *= args.gain / fftsize
        #     spektogram = np.clip(magnitude[low_bin:low_bin + args.columns], 0, 1)
        #     spektohist = np.append(spektohist, [spektogram], axis=0)
        #     if spektohist.shape[0] > 100:
        #         spektohist = np.delete(spektohist, 0, 0)
        #     if np.mean(spektogram[:5]) > 0.3:
        #         print("bass")
            
        #     #print(len(find_peaks(spektogram,0.4,10)))
        #     spektosum = np.sum(spektogram)
        #     meanfreq = np.sum(spektogram/spektosum * np.arange(0,len(spektogram)))
        #     meanmeanfreq = meanmeanfreq*beta + meanfreq*(1-beta)
        #   #  print(meanmeanfreq)
        #     long_avg = long_avg*beta + spektosum*(1-beta)
        #    # print(long_avg)
        #     if long_avg < 3 and waittime + 2 < pytime.time():
        #         args.gain *= 1.5
        #         waittime = pytime.time()
        #         print("adjusted gain to", args.gain)
        #     if long_avg > 8 and waittime + 2 < pytime.time():
        #         args.gain /= 1.5
        #         waittime = pytime.time()
        #         print("adjusted gain to", args.gain)
        #     line = (gradient[int(np.clip(x, 0, 1) * (len(gradient) - 1))]
        #             for x in magnitude[low_bin:low_bin + args.columns])

            
        #     print(*line, sep='', end='\x1b[0m\n')
        else:
            print('no input')

    print('stream started')
    with sd.InputStream(device=args.device, channels=1, callback=callback,
                        blocksize=int(samplerate * args.block_duration / 1000),
                        samplerate=samplerate):
        while True:
            print("iterating stream")
            # response = input()
            # if response in ('', 'q', 'Q'):
            #     break
            # for ch in response:
            #     if ch == '+':
            #         args.gain *= 2
            #     elif ch == '-':
            #         args.gain /= 2
            #     else:
            #         print('\x1b[31;40m', usage_line.center(args.columns, '#'),
            #               '\x1b[0m', sep='')
            #         break
except KeyboardInterrupt:
    parser.exit('Interrupted by user')
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))