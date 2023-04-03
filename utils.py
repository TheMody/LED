import numpy as np
#import matplotlib.pyplot as plt
#from scipy.signal import find_peaks

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
def find_peaks(x,prominence = 0.0,distance = 0, n_size = 5):
    peaks = []
    # def smooth(x):
    #     return np.convolve(x, np.ones(5)/5, mode='same')
    # x_smooth = smooth(x)
    # x = x-x_smooth
    # x = x/max(x)
    # x[x<0] = 0
    for i in range(1,len(x)-1):
        x_selected = x[max(0,i-n_size):min(len(x),i+n_size)]
        if x[i] == np.max(x_selected) and x[i] > np.mean(x_selected) * (1.5):
            if len(peaks) == 0:
                peaks.append(i)
            else:
                if i-peaks[-1] > distance:
                    peaks.append(i)
                else:
                    if x[i] > x[peaks[-1]]:
                        peaks[-1] = i
                      #  peaks.append(i)
    if len(peaks) == 0:
        return np.array([])
    max_peak = np.max(x[peaks])
    peaks = np.array(peaks)
    peaks = peaks[x[peaks] > max_peak * prominence]
    return peaks


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

    X_energy_log = np.concatenate([[np.mean(X_energy_log)],X_energy_log])    

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

    peaks = find_peaks(X_energy_novelty_rectified,prominence=prominence,distance=distance)  
   

    if(len(peaks)==0):
    #    print("No peaks found!")
        return np.array([]), np.array([])
    
    size_of_peaks = X_energy_novelty_rectified[peaks]
    # if(displayAll):
    #     plt.figure(figsize=(12,4))
    #     plt.title("Picking Peaks")
    #     plt.plot(peaks, X_energy_novelty_rectified[peaks], "or")
    #     plt.plot(X_energy_novelty_rectified)
    #     plt.show()
    
    # peaks are beginning of window, more accurate to make the onsets in the middle
    # of the window, reduces potential error by 1/2y
    
    onsets = peaks*skip + window_size//2
    # if(displayAll):
    #     plt.figure(figsize=(12,4))
    #     plt.title("Signal with Onsets")
    #     plt.plot(X)
    #     for k in range(len(onsets)):
    #         plt.plot([onsets[k],onsets[k]],[-1,1],color='r')    
    #     plt.show()

    return onsets, size_of_peaks