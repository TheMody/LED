import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def energy(x):
    return (x @ x) / len(x)

# Half-wave rectification

def rectify(x):
    if(isinstance(x,np.ndarray)):
        return np.maximum(x,np.zeros(len(x)))
    elif(isinstance(x,list)):
        return list(np.maximum(x,np.zeros(len(x))))
    else:
        return max(x,0)



def AmplitudeBasedOnsets(X,window_size=512,overlap=0.5,scale=10,
                         height=None,
                         prominence=None,
                         distance=None,
                         displayAll=False):
    
    N = len(X)
    
    X = X / max(X)       # normalize amplitude

    skip = int((1-overlap)*window_size)
    
   # print("skip:",skip)

    num_windows = (N // skip) - 1

  #  print("num_windows:",num_windows)

    window_locations = skip * np.arange(num_windows)

  #  print("window_locations:",window_locations)

    X_energy = np.array( [ energy( X[ w : (w+window_size)] ) for w in window_locations ])

    X_energy = np.array(X_energy)

    if(scale == None):
        X_energy_log = X_energy
    else:
        X_energy_log = np.log(1 + scale*X_energy)

    # if(displayAll):
    #     plt.figure(figsize=(12,4))
    #     plt.title("Log X Energy Signal with scale factor "+str(scale))
    #     plt.plot(X_energy_log)
    #     plt.show()

    X_energy_log = np.concatenate([[0],X_energy_log])    

    # Take the discrete differential; watch out, diff transforms array in place

    X_energy_novelty = np.diff(list(X_energy_log)) 
    
    # standardize novelty
    
    X_energy_novelty = X_energy_novelty / max(X_energy_novelty)
    
    # if(displayAll):
    #     plt.figure(figsize=(12,4))
    #     plt.title("X Energy Novelty")
    #     plt.plot(X_energy_novelty)
    #     plt.show()

    X_energy_novelty_rectified = rectify(X_energy_novelty)      
    
    # if(displayAll):
    #     plt.figure(figsize=(12,4))
    #     plt.title("Rectified X Energy Novelty")
    #     plt.plot(X_energy_novelty_rectified)
    #     plt.show()

    # peak picking

    peaks,_ = find_peaks(X_energy_novelty_rectified,
                         height=height,prominence=prominence,distance=distance)  
    
    if(len(peaks)==0):
    #    print("No peaks found!")
        return np.array([])
    # if(displayAll):
    #     plt.figure(figsize=(12,4))
    #     plt.title("Picking Peaks")
    #     plt.plot(peaks, X_energy_novelty_rectified[peaks], "or")
    #     plt.plot(X_energy_novelty_rectified)
    #     plt.show()
    
    # peaks are beginning of window, more accurate to make the onsets in the middle
    # of the window, reduces potential error by 1/2y
    
    onsets = peaks*skip + window_size//2
    if(displayAll):
        plt.figure(figsize=(12,4))
        plt.title("Signal with Onsets")
        plt.plot(X)
        for k in range(len(onsets)):
            plt.plot([onsets[k],onsets[k]],[-1,1],color='r')    
        plt.show()

    return onsets



# Apply a moving average smoothing filter to X, starting at index n//2 and ending
# at len(X)-n//2-1, returning a new smoothed array;
    
def movingAverageFilter(X,n=3):    
    Y = np.copy(X)
    for i in range(n//2,len(X)-n//2):
        Y[i] = np.mean(X[i-n//2:i+n//2+1])
    return Y

    
# Replace each X[i] by its difference from the mean of the surrounding
# n points

def subtractMAFilter(X,n=3):
    Y = np.copy(X)
    return Y - movingAverageFilter(X,n)

# Apply a median smoothing filter to X, starting at index n/2 and ending
# at len(X)-n/2-1, returning a new smoothed array;
    
def medianFilter(X,n=3):    
    Y = np.copy(X)
    for i in range(n//2,len(X)-n//2):
        Y[i] = np.median(X[i-n//2:i+n//2+1])
    return Y

# To emphasize peaks, subtract the smoothed curve from the original
    
def subtractMedianFilter(X,n=3):
    Y = np.copy(X)
    return Y - medianFilter(X,n)

# Onset detection using various distance measure, including
# spectral flux from Lerch, p.163
def realFFT(X):
    return 2*abs(np.fft.rfft(X))/len(X) 

def normalize(x):
    return x / np.max(x)
# S is previous spectrum, Sn is next one
from scipy.signal import windows
def spectral_distance(S,Sn,kind='SF2'):      # default will be Lerch, p.163
    if(kind == 'L1'):
        return np.sum(np.abs(Sn-S))
    elif(kind == 'L2'):
        return (np.sum((Sn-S)**2))**0.5
    elif(kind == 'CD'):                     # Correlation Distance:  1 - correlation
        s = np.std(S)                       # must account for spectra with all 0's
        sn = np.std(Sn)
        if(np.isclose(s,0) or np.isclose(sn,0)):
            return 0.0
        else:
            return 1.0 + (((S - np.mean(S)) @ (Sn - np.mean(Sn))) / (len(S) * s * sn))
    elif(kind == 'RL1'):
        return np.sum(np.abs(rectify(Sn-S)))
    elif(kind == 'RL2'):
        return (np.sum((Sn-S)**2))**0.5
    elif(kind == 'SF1'):     # use Lerch, p.163 with L1 norm, following Dixon
        return (np.sum( [ (max(Sn[k]-S[k],0)) for k in range(len(S)) ] )) / len(S)
    elif(kind == 'SF2'):     # use Lerch, p.163 with L2 norm
        return np.sqrt(np.sum( [ (max(Sn[k]-S[k],0)**2) for k in range(len(S)) ] )) / len(S)                
    else:
        return None
    
def SpectralBasedOnsets(X,window_size=512,overlap=0.5,
                        kind = None,     # distance function used, L1, L2, CD, SF1, SF2
                        filtr = None,    # filter applied before peak picking, if any
                        size = 3,        # size of kernel used in filter
                        win = "tri",      # apply windowing function to window
                        scale=10,      # scale factor for log, None = no log
                        height=None,     # these 3 parameters are for pick_peak,
                        prominence=0.1, #    any not equal to None will be applied
                        distance=None,
                        displayAll=False):
    
    N = len(X)
    
    X = X / max(X)       # normalize amplitude

    skip = int((1-overlap)*window_size)

    num_windows = (N // skip) - 1

    window_locations = skip * np.arange(num_windows)
    
    if(win == 'hann'):
        W = windows.hann(window_size)
    elif(win == "tri"):
        W = windows.triang(window_size)
    else:
        W = windows.boxcar(window_size)
        
    X_spectrogram = np.array( [ realFFT( W * X[ w : w + window_size ] ) for w in window_locations ])   

    # take the log with scaling factor; if no log transformation, set to None
    
    if(scale == None):
        X_spectrogram_log = X_spectrogram
    else:
        X_spectrogram_log = np.log(1 + scale*X_spectrogram)

    # Difference = Novelty Function

    X_spectral_novelty = np.zeros(num_windows)
    
    for k in range(1,num_windows):           #first value will be 0, length unchanged
       # print(X_spectrogram_log[k-1])
      #  print(X_spectrogram_log[k])
        X_spectral_novelty[k] = spectral_distance(X_spectrogram_log[k-1],X_spectrogram_log[k])
    
   # print(X_spectral_novelty)
    
    # normalize spectral novelty function
    if(displayAll):
        plt.figure(figsize=(12,4))
        plt.title("X Spectral Novelty unnomarlized")
        plt.plot(X_spectral_novelty)
        plt.show()
    X_spectral_novelty = normalize(X_spectral_novelty)
    
    if(displayAll):
        plt.figure(figsize=(12,4))
        plt.title("X Spectral Novelty")
        plt.plot(X_spectral_novelty)
        plt.show()


#     Distance functions are always >= 0
#     X_spectral_novelty_rectified = rectify(X_spectral_novelty)      
    
#     if(displayAll):
#         plt.figure(figsize=(12,4))
#         plt.title("Rectified X Spectral Novelty")
#         plt.plot(X_spectral_novelty_rectified)
#         plt.show()
        
    if(filtr != None):
        X_spectral_novelty = filtr(X_spectral_novelty,size)
        if(displayAll):
            plt.figure(figsize=(12,4))
            plt.title("Filtered X Spectral Novelty")
            plt.plot(X_spectral_novelty)
            plt.show()
            
    # peak picking

    peaks,_ = find_peaks(X_spectral_novelty,height=height,prominence=prominence,distance=distance)   # this works pretty well

    if(len(peaks)==0):
        print("No peaks found!")
        return np.array([])
    if(displayAll):
        plt.figure(figsize=(12,4))
        plt.title("Picking Peaks")
        plt.plot(peaks, X_spectral_novelty[peaks], "or")
        plt.plot(X_spectral_novelty)
        plt.show()

    # fft_novelty = realFFT(X_spectral_novelty)
    # plt.title("fft_novelty")
    # plt.plot(X_spectral_novelty)
    # plt.plot(fft_novelty)
    # plt.show()

    # peaks are beginning of window, more accurate to make the onsets in the middle
    # of the window, reduces potential error by 1/2
    
    onsets = peaks*skip + window_size//2
    if(displayAll):
        plt.figure(figsize=(12,4))
        plt.title("Signal with Onsets")
        plt.plot(X)
        for k in range(len(onsets)):
            plt.plot([onsets[k],onsets[k]],[-1,1],color='r')    
        plt.show()
    return onsets
if __name__ == '__main__':
    x = np.asarray([np.sin(i/10) for i in range(22000)])
    y = np.asarray([np.sin(i/1000) for i in range(22000)])
    c = np.asarray([np.sin(0.5+i/100000) for i in range(22000)])
    c2= np.asarray([ ((3000-int(i%3000) ) / 3000)   for i in range(22000)])
    x = x*y*c*c2
    plt.plot(x)
    plt.show()

    #AmplitudeBasedOnsets(x)
    SpectralBasedOnsets(x)

