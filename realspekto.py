#!/usr/bin/env python3
"""Show a text-mode spectrogram using live microphone data."""
import argparse
import math
import shutil

import numpy as np
import sounddevice as sd
#import time as pytime
from stripsfunctions import stripManager
from gpiozero import Button
from screeninfo import get_monitors

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
    metavar=('LOW', 'HIGH'), default=[10, 500],
    help='frequency range (default %(default)s Hz)')
args = parser.parse_args(remaining)
#stripshape = [[6,6,6],[6,6,6],[6,6,6],[6,6,6],[6,6,6],[6,6,6]]
stripshape = [[12,12,12,10,6,3],[12,12,12,10,6,3],[6,10,12,12,12,10,6],[6,10,12,12,12,10,6]]
stripoffset = [[0,0,0,0,0,0], [0,0,0,0,0,0], [3,1,0,0,0,1,3], [3,1,0,0,0,1,3]]
striplength = 0
for i in stripshape:
    for j in i:
        if j > striplength:
            striplength = j
#print(stripshape)
#striplength = np.max(np.asarray(stripshape))
#print("max strip length: ",striplength)
low, high = args.range
if high <= low:
    parser.error('HIGH must be greater than LOW')

test = bool(get_monitors())


try:
    samplerate = sd.query_devices(args.device, 'input')['default_samplerate']
    delta_f = (high - low) / (striplength- 1)
    fftsize = math.ceil(samplerate / delta_f)
    low_bin = math.floor(low / delta_f)
    sManager = stripManager(stripshape, stripoffset,samplerate, fftsize, low_bin ,test = test)
    buffer = []
    if not test:
        button = Button(17)
        button.when_pressed = sManager.changevisualization


    def callback(indata, frames, time, status):
        global buffer
        if status:
            text = ' ' + str(status) + ' '
            print('\x1b[34;40m', text.center(args.columns, '#'),
                  '\x1b[0m', sep='')
        if any(indata):
            buffer = buffer + list(indata[:, 0])
            if len(buffer) > 4000:
                sManager.visualize(np.asarray(buffer))
                buffer = []
        else:
            print('no input')

    print('stream started')
    with sd.InputStream(device=args.device, channels=1, callback=callback,
                        blocksize=int(samplerate * args.block_duration / 1000),
                        samplerate=samplerate):
        while True:
            pass

except KeyboardInterrupt:
    parser.exit('Interrupted by user')
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))