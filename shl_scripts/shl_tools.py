
#!/usr/bin/env python3
# -*- coding: utf-8 -*
from __future__ import division, print_function, absolute_import
from SLIP import Image
from scipy.stats import kurtosis
import sys
import time
import numpy as np
from shl_scripts.shl_encode import sparse_encode
import math
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import gamma

toolbar_width = 40

def bins_step(mini,maxi,nb_step):
    '''doing a range of non integer number to make histogramm more beautiful'''
    step=(maxi-mini)/nb_step
    out=list()
    a=mini
    for i in range(nb_step+1):
        out.append(a)
        a=a+step
    out.append(a)
    return out


def get_data(height=256, width=256, n_image=200, patch_size=(12,12),
            datapath='database/', name_database='serre07_distractors',
            max_patches=1024, seed=None, patch_norm=True, verbose=0):
    ''' Extract database
    Extract from a given database composed of image of size (height,width) a series a random patch
    '''
    slip = Image({'N_X':height, 'N_Y':width,
                'white_n_learning' : 0,
                'seed': seed,
                'white_N' : .07,
                'white_N_0' : .0, # olshausen = 0.
                'white_f_0' : .4, # olshausen = 0.2
                'white_alpha' : 1.4,
                'white_steepness' : 4.,
                'datapath': datapath,
                'do_mask':True,
                'N_image': n_image})

    if verbose:
        # setup toolbar
        sys.stdout.write('Extracting data...')
        sys.stdout.flush()
        sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['
        t0 = time.time()
    imagelist = slip.make_imagelist(name_database=name_database)#, seed=seed)
    for filename, croparea in imagelist:
        # whitening
        image, filename_, croparea_ = slip.patch(name_database, filename=filename, croparea=croparea, center=False)#, seed=seed)
        image = slip.whitening(image)
        # Extract all reference patches and ravel them
        data_ = slip.extract_patches_2d(image, patch_size, N_patches=int(max_patches))#, seed=seed)
        data_ = data_.reshape(data_.shape[0], -1)
        data_ -= np.mean(data_, axis=0)
        if patch_norm:
            data_ /= np.std(data_, axis=0)
        # collect everything as a matrix
        try:
            data = np.vstack((data, data_))
        except Exception:
            data = data_.copy()
        if verbose:
            # update the bar
            sys.stdout.write(filename + ", ")
            sys.stdout.flush()
    if verbose:
        dt = time.time() - t0
        sys.stdout.write("\n")
        sys.stdout.write("Data is of shape : "+ str(data.shape))
        sys.stdout.write(' - done in %.2fs.' % dt)
        sys.stdout.flush()
    return data

def compute_RMSE(data, dico):
    ''' Compute the Root Mean Square Error between the image and it's encoded representation'''
    a=dico.transform(data)
    residual=data - a@dico.dictionary
    b=np.sum(residual**2,axis=1)/np.sqrt(np.sum(data**2,axis=1))
    rmse=math.sqrt(np.mean(b))
    return rmse

def compute_KL(data, dico):
    '''Compute the Kullback Leibler ratio to compare a distribution to its gaussian equivalent.
    if the KL is close to 1, the studied distribution is closed to a gaussian'''
    sparse_code= dico.transform(data)
    N=dico.dictionary.shape[0]
    P_norm = np.mean(sparse_code**2, axis=0)#/Z
    mom1 = np.sum(P_norm)/dico.dictionary.shape[0]
    mom2 = np.sum((P_norm-mom1)**2)/(dico.dictionary.shape[0]-1)
    KL = 1/N * np.sum( (P_norm-mom1)**2 / mom2**2 )
    return KL

def Compute_kurto(data, dico):
    '''Compute the kurtosis'''
    sparse_code= dico.transform(data)
    P_norm = np.mean(sparse_code**2, axis=0)#/Z
    kurto = kurtosis(P_norm, axis=0)
    return kurto

# To adapt with shl_exp
def show_dico_in_order(shl_exp, data=None, algorithm=None,title=None, fname=None):
    '''Display a the dictionary of filter in order of probability of selection.
    Filter which are selected more often than others are located at the end'''
    subplotpars = matplotlib.figure.SubplotParams(left=0., right=1., bottom=0., top=1., wspace=0.05, hspace=0.05,)
    fig = plt.figure(figsize=(10, 10), subplotpars=subplotpars)

    dico=shl_exp.dico_exp
    if (algorithm is not None) and (data is not None)  :
        sparse_code = shl_encode.sparse_encode(data,dico.dictionary,algorithm=algorithm)
    else :
        sparse_code=shl_exp.coding

    dim_graph=dico.dictionary.shape[0]
    res_lst=np.count_nonzero(sparse_code,axis=0)
    a=res_lst.argsort()
    dim_patch=int(shl_exp.patch_size[0])

    for i in range(dim_graph):
        ax = fig.add_subplot(np.sqrt(dim_graph), np.sqrt(dim_graph), i + 1)
        index_to_consider=a[i]
        dico_to_display=dico.dictionary[index_to_consider]
        cmax = np.max(np.abs(dico_to_display))
        ax.imshow(dico_to_display.reshape((dim_patch,dim_patch)), cmap=plt.cm.gray_r, vmin=-cmax, vmax=+cmax,
                interpolation='nearest')
        ax.set_xticks(())
        ax.set_yticks(())
    if title is not None:
        fig.suptitle(title, fontsize=12, backgroundcolor = 'white', color = 'k')
    if not fname is None: fig.savefig(fname, dpi=200)
    return fig, ax

def show_dico(shl_exp, title=None, fname=None, **kwargs):
    '''
    display the dictionary in a random order
    '''
    dico=shl_exp.dico_exp
    dim_graph = dico.dictionary.shape[0]
    subplotpars = matplotlib.figure.SubplotParams(left=0., right=1., bottom=0., top=1., wspace=0.05, hspace=0.05,)
    fig = plt.figure(figsize=(10, 10), subplotpars=subplotpars)
    dim_patch = int(np.sqrt(dico.dictionary.shape[1]))

    for i, component in enumerate(dico.dictionary):
        ax = fig.add_subplot(np.sqrt(dim_graph), np.sqrt(dim_graph), i + 1)
        cmax = np.max(np.abs(component))
        ax.imshow(component.reshape((dim_patch,dim_patch)), cmap=plt.cm.gray_r, vmin=-cmax, vmax=+cmax,
                interpolation='nearest')
        ax.set_xticks(())
        ax.set_yticks(())
    if title is not None:
        fig.suptitle(title, fontsize=12, backgroundcolor = 'white', color = 'k')
    if not fname is None: fig.savefig(fname, dpi=200)
    return fig, ax

def plot_coeff_distribution(dico, data, title=None,algorithm=None,fname=None):
    '''Plot the coeff distribution of a given dictionary'''

    if algorithm is not None :
        sparse_code = shl_encode.sparse_encode(data,dico.dictionary,algorithm=algorithm)
    else :
        sparse_code= dico.transform(data)
    res_lst=np.count_nonzero(sparse_code,axis=0)
    df=pd.DataFrame(res_lst, columns=['Coeff'])
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    with sns.axes_style("white"):
        ax = sns.distplot(df['Coeff'], kde=False)#, fit=gamma,  fit_kws={'clip':(0., 5.)})
    if title is not None:
        ax.set_title('distribution of coefficients, ' + title)
    else:
        ax.set_title('distribution of coefficients')
    ax.set_ylabel('pdf')
    ax.set_xlim(0)
    if not fname is None: fig.savefig(fname, dpi=200)
    return fig, ax


def plot_dist_max_min(shl_exp, data=None, algorithm=None,fname=None):
    '''plot the coefficient distribution of the filter which is selected the more, and the one which is selected the less'''
    dico=shl_exp.dico_exp
    if (algorithm is not None) and (data is not None)  :
        sparse_code = shl_encode.sparse_encode(data,dico.dictionary,algorithm=algorithm)
    else :
        sparse_code=shl_exp.coding
    nb_filter_selection=np.count_nonzero(sparse_code,axis=0)

    index_max=np.argmax(nb_filter_selection)
    index_min=np.argmin(nb_filter_selection)
    color,label=['r', 'b'], ['most selected filter : {0}'.format(index_max),'less selected filter : {0}'.format(index_min)]
    coeff_max = np.abs(sparse_code[:,index_max])
    coeff_min = np.abs(sparse_code[:,index_min])
    bins_max = bins_step(0.0001,np.max(coeff_max),20)
    bins_min = bins_step(0.0001,np.max(coeff_min),20)
    fig = plt.figure(figsize=(6, 10))
    ax = plt.subplot(2,1,1)
    with sns.axes_style("white"):
        n_max,bins1=np.histogram(coeff_max,bins_max)
        n_min,bins2=np.histogram(coeff_min,bins_min)
        ax.semilogy(bins1[:-1],n_max,label=label[0],color=color[0])
        ax.semilogy(bins2[:-1],n_min,label=label[1],color=color[1])
    ax.set_title('distribution of coeff in the most & less selected filters')
    ax.set_ylabel('number of selection')
    ax.set_xlabel('value of coefficient')
    plt.legend()
    if not fname is None: fig.savefig(fname, dpi=200)
    return fig, ax


def plot_proba_histogram(coding):
    n_dictionary=coding.shape[1]

    p = np.count_nonzero(coding, axis=0)/coding.shape[1]
    p /= p.sum()
    print('Entropy / Entropy_max=', np.sum( -p * np.log(p)) / np.log(n_dictionary) )

    fig = plt.figure(figsize=(16, 4))
    ax = fig.add_subplot(111)
    ax.bar(np.arange(n_dictionary), p*n_dictionary)
    ax.set_title('distribution of the selection probability')
    ax.set_ylabel('pdf')
    ax.set_xlim(0)
    ax.axis('tight')
    return fig, ax

## To adapt with shl_exp
def plot_variance_and_proxy(dico, data, title, algorithm=None, fname=None):
    '''Overlay of 2 histogram, the histogram of the variance of the coefficient, and the corresponding gaussian one'''
    if algorithm is not None :
        sparse_code = shl_encode.sparse_encode(data,dico.dictionary,algorithm=algorithm)
    else :
        sparse_code= dico.transform(data)
    Z = np.mean(sparse_code**2)
    P_norm=np.mean(sparse_code**2, axis=0)/Z
    df = pd.DataFrame(P_norm, columns=['P'])
    mom1= np.mean(P_norm)
    mom2 = (1/(dico.dictionary.shape[0]-1))*np.sum((P_norm-mom1)**2)
    Q=np.random.normal(mom1,mom2,dico.dictionary.shape[0])
    df1=pd.DataFrame(Q, columns=['Q'])
    #code = self.code(data, dico)
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    #bins=[0, 10, 20, 30, 40, 50, 100]
    mini=min(np.min(P_norm),np.min(Q))
    maxi=max(np.max(P_norm),np.max(Q))
    bins=bins_step(mini,maxi,20)
    with sns.axes_style("white"):
        ax = sns.distplot(df['P'],bins=bins,kde=False)
        ax = sns.distplot(df1['Q'],bins=bins, kde=False)
        #ax = sns.distplot(df['P'], bins=frange(0.0,4.0,0.2),kde=False)#, fit=gamma,  fit_kws={'clip':(0., 5.)})
        #ax = sns.distplot(df1['Q'],bins=frange(0.0,4.0,0.2), kde=False)
    if title is not None :
        ax.set_title('distribution of the mean variance of coefficients, ' + title)
    else :
        ax.set_title('distribution of the mean variance of coefficients ')
    ax.set_ylabel('pdf')
    if not fname is None: fig.savefig(fname, dpi=200)
    #print(mom1,mom2)
    return fig, ax

def plot_variance(shl_exp, data=None, algorithm=None, fname=None):
    dico=shl_exp.dico_exp
    if (algorithm is not None) and (data is not None)  :
        sparse_code = shl_encode.sparse_encode(data,dico.dictionary,algorithm=algorithm)
    else :
        sparse_code=shl_exp.coding
    n_dictionary=dico.dictionary.shape[0]
    Z = np.mean(sparse_code**2)
    fig = plt.figure(figsize=(12, 4))
    ax = fig.add_subplot(111)
    ax.bar(np.arange(n_dictionary), np.mean(sparse_code**2, axis=0)/Z)#, yerr=np.std(code**2/Z, axis=0))
    ax.set_title('Variance of coefficients')
    ax.set_ylabel('Variance')
    ax.set_xlabel('#')
    ax.set_xlim(0, n_dictionary)
    if not fname is None: fig.savefig(fname, dpi=200)
    return fig, ax

def plot_variance_histogram(shl_exp, data=None, algorithm=None, fname=None):
    from scipy.stats import gamma
    dico=shl_exp.dico_exp
    if (algorithm is not None) and (data is not None) :
        sparse_code = shl_encode.sparse_encode(data,dico.dictionary,algorithm=algorithm)
    else :
        sparse_code= shl_exp.coding
    Z = np.mean(sparse_code**2)
    df = pd.DataFrame(np.mean(sparse_code**2, axis=0)/Z, columns=['Variance'])
    fig = plt.figure(figsize=(6, 4))
    ax = fig.add_subplot(111)
    with sns.axes_style("white"):
        ax = sns.distplot(df['Variance'], kde=False)#, fit=gamma,  fit_kws={'clip':(0., 5.)})
    ax.set_title('distribution of the mean variance of coefficients')
    ax.set_ylabel('pdf')
    ax.set_xlim(0)
    if not fname is None: fig.savefig(fname, dpi=200)
    return fig, ax

def time_plot(shl_exp, variable='kurt', N_nosample=1, alpha=.3, fname=None):
    dico=shl_exp.dico_exp
    try:
        df_variable = dico.record[variable]
        learning_time = np.array(df_variable.index) #np.arange(0, dico.n_iter, dico.record_each)
        A = np.zeros((len(df_variable.index), dico.n_dictionary))
        for ii, ind in enumerate(df_variable.index):
            A[ii, :] = df_variable[ind]

        #print(learning_time, A[:, :-N_nosample].shape)
        fig = plt.figure(figsize=(12, 4))
        ax = fig.add_subplot(111)
        ax.plot(learning_time, A[:, :-N_nosample], '-', lw=1, alpha=alpha)
        ax.set_ylabel(variable)
        ax.set_xlabel('Learning step')
        ax.set_xlim(0, dico.n_iter)
        if not fname is None: fig.savefig(fname, dpi=200)
        return fig, ax

    except AttributeError:
        fig = plt.figure(figsize=(12, 1))
        ax = fig.add_subplot(111)
        ax.set_title('record not available')
        ax.set_ylabel(variable)
        ax.set_xlabel('Learning step')
        ax.set_xlim(0, dico.n_iter)
        if not fname is None: fig.savefig(fname, dpi=200)
        return fig, ax
