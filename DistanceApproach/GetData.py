from copy import deepcopy
from future.utils import iteritems
from datetime import date, datetime
import pandas as pd
import numpy as np
import bt

def make_data( n_assets=100, n_periods=2000, start_date=date(2021,1,1), phi=0.5, corr=1.0, seed=1234 ):
    ''' Randomly generate a data set consisting of non-stationary prices,
        but where the difference between the prices of any two securities is. '''
    np.random.seed(seed)
    dts = pd.date_range( start_date, periods=n_periods)
    T = dts.values.astype('datetime64[D]').astype(float).reshape(-1,1)
    N = n_assets
    columns = ['s%i' %i for i in range(N)]
    cov = corr * np.ones( (N,N) ) + (1-corr) * np.eye(N)
    noise = pd.DataFrame( np.random.multivariate_normal( np.zeros(N), cov, len(dts)), index = dts, columns = columns )
    # Generate an AR(1) process with parameter phi
    eps = pd.DataFrame( np.random.multivariate_normal( np.zeros(N), np.eye(N), len(dts)), index = dts, columns=columns)
    alpha = 1 - phi
    eps.values[1:] = eps.values[1:] / alpha # To cancel out the weighting that ewm puts on the noise term after x0
    ar1 = eps.ewm(alpha=alpha, adjust=False).mean()
    ar1 *= np.sqrt(1.-phi**2) # Re-scale to unit variance, since the standard AR(1) process has variance sigma_eps/(1-phi^2)
    data = 100. + noise.cumsum()*np.sqrt(0.5) + ar1*np.sqrt(0.5)
    # With the current setup, the difference between any two series should follow a mean reverting process with std=1
    return data