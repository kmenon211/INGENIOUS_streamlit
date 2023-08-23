"""Module of helper methods."""
import math
import numpy as np
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KernelDensity
from sklearn.naive_bayes import GaussianNB
import os
import io

from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.model_selection import GridSearchCV

# st.write('X_train',np.shape(X_train))
# st.write('seaborn version',sns.__version__)
# st.write('pandas version',pd.__version__)
# st.write('streamlit version',st.__version__)
# st.write('numpy version',np.__version__)
# st.write('matplotlib version',sns.__version__)
# import sklearn
# st.write('scikit',sklearn.show_versions()) # sklearn.__version__)


class KDEClassifier(BaseEstimator, ClassifierMixin):
    """Bayesian generative classification based on KDE

    Parameters
    ----------
    bandwidth : float
        the kernel bandwidth within each class
    kernel : str
        the kernel name, passed to KernelDensity
    """
    def __init__(self, bandwidth=1.0, kernel='gaussian'):
        self.bandwidth = bandwidth
        self.kernel = kernel

    def fit(self, X, y):
        self.classes_ = np.sort(np.unique(y))
        training_sets = [X[y == yi] for yi in self.classes_]
        self.models_ = [KernelDensity(bandwidth=self.bandwidth,
                                      kernel=self.kernel).fit(Xi)
                        for Xi in training_sets]
        self.logpriors_ = [np.log(Xi.shape[0] / X.shape[0])
                           for Xi in training_sets]
        #st.write('self.logpriors_',self.logpriors_)
        return self

    def predict_proba(self, X):
        logprobs = np.array([model.score_samples(X)
                             for model in self.models_]).T
        result = np.exp(logprobs + self.logpriors_)
        return result / result.sum(1, keepdims=True)

    def predict(self, X):
        return self.classes_[np.argmax(self.predict_proba(X), 1)]
    

def math_it_up(*args, **kwargs):
    return np.log(*args, **kwargs)

def normpdf(x, mean, sd):
    var = float(sd)**2
    pi = 3.1415926
    denom = (2*pi*var)**.5
    num = math.exp(-(float(x)-float(mean))**2/(2*var))
    return num/denom

def st_file_selector(st_placeholder, path='.', label='Please, select a file/folder...'):
    # get base path (directory)
    base_path = '.' if path == None or path is '' else path
    base_path = base_path if os.path.isdir(
        base_path) else os.path.dirname(base_path)
    base_path = '.' if base_path is None or base_path is '' else base_path
    # list files in base path directory
    files = os.listdir(base_path)
    if base_path is not '.':
        files.insert(0, '..')
    files.insert(0, '.')
    selected_file = st_placeholder.selectbox(
        label=label, options=files, key=base_path)
    selected_path = os.path.normpath(os.path.join(base_path, selected_file))
    if selected_file is '.':
        return selected_path
    if os.path.isdir(selected_path):
        selected_path = st_file_selector(st_placeholder=st_placeholder,
                                         path=selected_path, label=label)
    return selected_path

def make_data():
    return np.random.normal(1, 1, size=100)

def my_kdeplot(dfpair,x_cur,y_cur0,dfpairN=None):
    fig, axes = plt.subplots(figsize=(15,8),ncols=2,nrows=1)

    #### 1 variables ##### sns.histplot(data=penguins, x="flipper_length_mm", kde=True)
    ph0=sns.histplot(data=dfpairN,x=x_cur,kde=True,fill=True,color='r',alpha=0.4,ax=axes[0], 
                    thresh=0.05,common_norm=True) 
    ph0=sns.histplot(data=dfpair,x=x_cur,kde=True,fill=True,color='g',alpha=0.6,ax=axes[0], 
                    thresh=0.05,common_norm=True)
       
    axes[0].set_xlabel(str(x_cur), fontsize=15)                            
    axes[0].set_title(x_cur)

    #### 2 variables ##### 
    ph=sns.kdeplot(data=dfpair,x=x_cur,y=y_cur0,fill=True,cmap='Greens',alpha=0.4,ax=axes[1], 
                    thresh=0.05,common_norm=True, cbar=True)
    
    ph=sns.kdeplot(data=dfpairN,x=x_cur,y=y_cur0,fill=True,cmap='Reds',alpha=0.4,ax=axes[1],
                    thresh=0.05,common_norm=True, cbar=True)
    axes[1].set_xlabel(str(x_cur), fontsize=15)
    axes[1].set_ylabel(str(y_cur0), fontsize=15)

    # st.pyplot(fig)
    # waiting_condition =0
    return #waiting_condition

def make_train_test(dfpair,x_cur,y_cur0,dfpairN):
    X_all = pd.concat((dfpair[x_cur],dfpairN[x_cur]))
    
    # Labels 
    y_g = np.ones((1, dfpair.shape[0]))
    y_all = np.append(y_g,(np.zeros((1, dfpairN.shape[0]))))
    
    X_train, X_test, y_train, y_test = train_test_split(X_all, y_all, test_size=0.33, random_state=42)
    
    return  X_train, X_test, y_train, y_test 

def optimal_bin(X_train, y_train):
    
    x_d = np.linspace(min(X_train), max(X_train), 100)
    
    maxValue = x_d[-1]
    range_div20 = (maxValue - x_d[0])/20.0; #st.write('range_div20 ',range_div20 )
   
    bandwidths = np.linspace(range_div20  , maxValue/3.0, 40) # was max value of attribute. not useful
    
    grid = GridSearchCV(KDEClassifier(), {'bandwidth': bandwidths})

    X_train_np = X_train.values
    #st.write(X_train.iloc[0:5], X_train_np[0:3])
    grid.fit(X_train_np[:,None],y_train) # removed  [:,None],  .to_numpy() doesn't work np.reshape(,(-1,1)), y_train
    scores = grid.cv_results_['mean_test_score']
    #st.write(grid.best_params_)
    #st.write('accuracy =', grid.best_score_)

    return grid.best_params_

def likelihood_KDE(X_train,X_test, y_train, y_test,x_cur,y_cur0, best_parameters):
    #
    #  Original VOI code uses 2d array for likelihood:  models (row) were interpetted where (columns).
    #
    ### bandwidth=1.0 BANDWIDTH can be optimized for RELIABILITY
    #st.write('using this otpimized bandwidth:',best_parameters)
    
    kde_pos = KernelDensity(bandwidth= best_parameters['bandwidth'] , kernel='gaussian') # best_parameters['bandwidth'] bandwidth=0.3
    kde_neg = KernelDensity(bandwidth= best_parameters['bandwidth'], kernel='gaussian')

    # if np.shape(X_train)[1]>2:
    # if train_test only all features
    # two_d = X_train.iloc[:,x_cur] 
    # x_d = np.linspace(min(X_train.iloc[:, x_cur]), max(X_train.iloc[:, x_cur]), 100) 
    # else:
    # if train_test only gets selected x_cur
    forkde_pos = X_train[y_train>0]#.iloc[:,x_cur] #cur_feat
    forkde_neg = X_train[y_train==0]#.iloc[:,x_cur]

    # two_d = X_train #.iloc[:,x_cur] #cur_feat
    forkde_pos_np = forkde_pos.values
    forkde_neg_np = forkde_neg.values
    kde_pos.fit(forkde_pos_np[:,np.newaxis])
    kde_neg.fit(forkde_neg_np[:,np.newaxis])
    
    x_d = np.linspace(min(X_train), max(X_train), 100) 
    Likelihood_logprob_pos = kde_pos.score_samples(x_d[:,np.newaxis]) #.score_samples
    Likelihood_logprob_neg = kde_neg.score_samples(x_d[:,np.newaxis])
    
    #st.write(np.vstack((Likelihood_logprob_pos,Likelihood_logprob_neg)))
    #st.write(np.exp(np.vstack((Likelihood_logprob_pos,Likelihood_logprob_neg))))  

    pos_like_scaled = np.exp(Likelihood_logprob_pos)/np.sum(np.exp(Likelihood_logprob_pos))
    neg_like_scaled = np.exp(Likelihood_logprob_neg)/np.sum(np.exp(Likelihood_logprob_neg))
    # st.write(kde_pos.bandwidth, (X_test.max() - X_test.min()) / kde_pos.bandwidth)
    fig2, ax2 = plt.subplots(figsize=(15,8),ncols=1,nrows=1) # CHANGED to one subplot
    # ax2.hist(X_test,alpha=0.5,color='grey',label='X_test',rwidth=(X_test.max() - X_test.min()) / kde_pos.bandwidth,hatch='/')
    #n_out = ax2.hist([X_test[y_test>0],X_test[y_test==0]], alpha=0.5,facecolor=['g','r'],
    n_out = ax2.hist([X_test[y_test>0]], alpha=0.3,facecolor='g',
                     histtype='barstacked', hatch='O',label='$~Pr(X|\Theta=Positive_{geothermal}$)') #rwidth= kde_pos.bandwidth,
    n_out = ax2.hist(X_test[y_test==0], alpha=0.3,facecolor='r',
                     histtype='barstacked',hatch='/',label='$~Pr(X|\Theta=Negative_{geothermal}$)') #rwidth= kde_pos.bandwidth (X_test.max() - X_test.min()) / 
                     
    ax2.legend(fontsize=18)
    ax2.set_ylabel('Empirical data counts', fontsize=18)
    ax2_ylims = ax2.axes.get_ylim()  

    ax1 = plt.twinx(ax=ax2)
    ax1.fill_between(x_d, pos_like_scaled, alpha=0.3,color='green')
    ax1.plot(x_d,pos_like_scaled,'g.')
    ax1.fill_between(x_d, neg_like_scaled, alpha=0.3,color='red')
    ax1.plot(x_d,neg_like_scaled,'r.')
    ax1.legend(loc=0, fontsize=17)
    ax1.set_ylabel(' Likelihood $~Pr(x | y=Geothermal_{neg/pos}$', fontsize=15)#, rotation=-90)
    ax2.set_xlabel(str(x_cur), fontsize=18)
    ax_ylims = ax1.axes.get_ylim()  
    #print('ax_ylims',ax_ylims)
    #st.write('ax_ylims',ax_ylims)
    ax1.set_ylim(0,ax_ylims[1])
   
    # ax1.set_ylim(0,ax2_ylims[1])
    
    # #.iloc[:,feat4]
    # # n_out = plt.hist([X_test[y_test>0],X_test[y_test==0]], color=['r','g'],histtype='barstacked',rwidth=(X_test.max() - X_test.min()) / kde_pos.bandwidth)
    # #.iloc[:,feat4]
    # n_out = axes[1].hist([X_test[y_test>0],X_test[y_test==0]], color=['g','r'],histtype='barstacked',rwidth=(X_test.max() - X_test.min()) / kde_pos.bandwidth)
    st.pyplot(fig2)
    #st.write('WIDTH of BARS: rwidth=(X_test.max() - X_test.min())',rwidth=(X_test.max() - X_test.min()))    
      
    ### COUNT ARRAY FIGURE # # # # #  #
    #st.write('Staying consistent, rows are *TRUE decision parameter* and columns are *interpretations*.')
    pos_counts = n_out[0][0] 
    neg_counts = n_out[0][1]
    count_ij= np.vstack((n_out[0][0],n_out[0][1]))
    
    fig3,axes=plt.subplots(nrows=1,ncols=1,figsize=(10,8))
    axes.imshow(count_ij,vmin=0,vmax=150,cmap='viridis')
    axes.set_title('Interpretation Counts')

    for (j,i),label in np.ndenumerate(count_ij):
        axes.text(i,j,round(label,2),fontsize=18,color='w',ha='center',va='center')

    xstring = r'''${X}=$'''
    ystring  = r'''${\Theta}=$'''

    labels = [item.get_text() for item in axes.get_xticklabels()]
    empty_string_labels = ['']*len(labels)
    empty_string_labels[1] = xstring+str(n_out[1][0]);
    empty_string_labels[3] = xstring+str(n_out[1][int(len(n_out)/2)]);
    empty_string_labels[5] = xstring+str(n_out[1][-1])
    axes.set_xticklabels(empty_string_labels)
    empty_string_labels = ['']*len(labels)
    empty_string_labels[1] = ystring+'Positive';
    empty_string_labels[3] = ystring+'Negative';
    # empty_string_labels[5] = ystring+str(+2500)
    axes.set_yticklabels(empty_string_labels)

    axes.set_xlabel('Interpretation / Data Attribute ($j$)',fontsize=15)
    axes.set_ylabel('Pos / Neg Label ($i$)', fontsize=15)
    # st.pyplot(fig3)

    ## RECALCULATE counts with smoothed Likelihood ????
        
       
    #return Likelihood_logprob_pos, Likelihood_logprob_neg, x_d, count_ij 
    # NOT LOG LIKELIHOOD
    return pos_like_scaled, neg_like_scaled, x_d, count_ij 

# Not used right now #
# def Prior_probability_continuous(x_sample, X_train, x_cur):
#     st.write('Define your Prior Probability (odds in the geothermal lottery)')  # right now could be used to redefine marginal??
#     X_locations = x_sample # uniformly sampled locations... 
#     X_unif_prior = np.ones(len(X_locations)) /len(X_locations)
#     print('Uniform Probability', X_unif_prior)

#     X_wideNorm_prior = []
#     X_narNorm_prior = []

    
#     st.write('np.min(X_train), np.max(X_train), np.median(X_train), np.round(np.std(X_train),1)')
#     st.write(np.min(X_train), np.max(X_train), np.median(X_train), np.round(np.std(X_train),1),X_train.describe())
    
#     # GaussianVariance =  np.round(np.std(X_train),1)
#     mymin = np.round(np.std(X_train),1)*0.5
#     mymax = np.round(np.std(X_train),1)*2
#     mydefault =  np.round(np.std(X_train),1)
#     mystep = np.round(np.std(X_train)/10,2)
#     st.write(np.round(np.std(X_train),1)*0.5, np.round(np.std(X_train),1)*2, np.round(np.std(X_train),1))
#     st.write(np.dtype(mymin), np.dtype(mymax), np.dtype(mydefault), np.dtype(mystep)) #0.2, 0.8, 0.4, 0.04
    
#     GaussianVariance = st.slider('Choose width of Gaussian Prior', float(mymin),float(mymax), float(mydefault), float(mystep))
#     for x_i in X_locations:    
#         # x, mean, sd
#         prob = normpdf(x_i, np.mean(X_train), GaussianVariance)
#         X_wideNorm_prior = np.append(X_wideNorm_prior, prob)
#         prob = normpdf(x_i, np.mean(X_train) ,0.75*GaussianVariance)
#         X_narNorm_prior = np.append(X_narNorm_prior, prob)

#     Nfactor = 1/float(np.sum(X_narNorm_prior))
#     Wfactor = 1/float(np.sum(X_wideNorm_prior))
#     X_wideNorm_prior = Wfactor*X_wideNorm_prior
#     X_narNorm_prior = Nfactor*X_narNorm_prior
#     fig3 = plt.figure(figsize=(15,8))
#     plt.plot(x_sample,X_unif_prior,'k.', label='Uniform Prior $U()$')
#     plt.plot(x_sample,X_wideNorm_prior,'r--', label='Prior $N(\mu,\sigma)$')
#     plt.plot(x_sample,X_narNorm_prior,'m*-', label='Prior N($\mu$,0.75$\sigma$)')
#     plt.xlabel(str(x_cur), fontsize=15)
#     plt.legend() 
#     st.pyplot(fig3)

#     return X_unif_prior, X_wideNorm_prior, X_narNorm_prior

def Prior_probability_binary(mykey=None): #x_sample, X_train,
    
    # X_locations = x_sample 
    # X_unif_prior = np.ones(len(X_locations)) /len(X_locations)
    
    Pr_POS = st.slider('Choose :blue[prior probability of success (odds in the geothermal lottery)]', float(0.00),float(1.0), float(0.1), float(0.01),key=mykey)

    return Pr_POS 

def Posterior_via_NaiveBayes(Pr_input_POS, X_train, X_test, y_train, y_test, x_sample, x_cur):
    """
    Function to calculate the posterior probability via Naive Bayes 

    Parameters
    PriorWeight: float, prior value from user input (order : NEG / POS) POSITIVE is second column! 
    X_train : 
    X_test : array-like, features in test
    y_train : array-like, labels in train
    y_test : array-like, labels in test
    x_sample : 
    x_cur : parameter

    """
    #   
    # # # # # # 
    model_NVML_input = GaussianNB(priors=[1-Pr_input_POS,Pr_input_POS,])
    #st.write('np.shape(X_train)',np.shape(X_train))
    model_NVML_input.fit(X_train.values[:,np.newaxis], y_train[:,np.newaxis]);

    model_NVML_uniform = GaussianNB(priors=[0.5,0.5])
    model_NVML_uniform.fit(X_train.values[:,np.newaxis], y_train[:,np.newaxis]);

    post_input = model_NVML_input.predict_log_proba(x_sample[:,np.newaxis])# X_test[:,np.newaxis])
    post_uniform = model_NVML_uniform.predict_log_proba(x_sample[:,np.newaxis])# X_test[:,np.newaxis])
    # st.write('post_input[:,0]',post_input[:,0])
    # st.write('post_input[:,1]',post_input[:,1])

    return post_input, post_uniform

def Posterior_Marginal_plot(post_input, post_uniform,marg,x_cur, x_sample):    
    
    fig4, axes = plt.subplots(figsize=(15,8),ncols=1,nrows=1)
    plt.plot(x_sample,post_input[:,1],color='purple', linewidth=6, alpha=0.7)
    plt.plot(x_sample,post_input[:,1],color='lime',linestyle='--', linewidth=3, label='$Pr(Positive|{})$ with Input Prior'.format(x_cur))
    plt.plot(x_sample,post_input[:,0],color='purple', linewidth=6)
    plt.plot(x_sample,post_input[:,0],'r--', linewidth=3,label='$Pr(Negative|{})$ with Input Prior'.format(x_cur))
    plt.plot(x_sample,post_uniform[:,1],'g--', alpha=0.1, linewidth=3,label='$Pr(Postitive|{})$ with Uniform Prior'.format(x_cur))
    plt.plot(x_sample,post_uniform[:,1],color='purple', alpha=0.1)
    plt.ylim([0,1])
    plt.legend(loc=2,fontsize=18,facecolor='w')#,draggable='True') 
    plt.xlabel(str(x_cur), fontsize=20)
    plt.ylabel('Posterior Probability', fontsize=20, color='purple')
    axes.tick_params(axis='x', which='both', labelsize=15)
    axes.tick_params(axis='y', which='both', labelsize=15, colors='purple')

    ax2 = axes.twinx()
    ax2.plot(x_sample,marg,color='orange',linestyle='dashdot', label='Marginal $Pr(X=x_j)$',alpha=0.7)
    ax2.fill_between(x_sample,marg, where=marg>=np.zeros(len(x_sample)), interpolate=True, color='orange',alpha=0.03)
    ax2.tick_params(axis='x', which='both', labelsize=15)
    ax2.tick_params(axis='y', which='both', colors='orange', labelsize=15)
    ax2.set_ylabel('Marginal Probability', color='orange',fontsize=20)
      
    # plt.legend(loc=1,fontsize=18) 
    st.pyplot(fig4)

    title = st.text_input('Filename', 'StreamlitImageDefault_{}.png'.format(x_cur))
    st.write('The current filename is', title)

    # SavePosteriorFig = st.checkbox('Please check if you want to save this figure')
    # if SavePosteriorFig:
    img = io.BytesIO()
    plt.savefig(img, format='png')
        
    btn = st.download_button(
        label="Download image "+title,
        data=img,
        file_name=title,
        mime="image/png"
        )


    return

def Posterior_by_hand(Pr_input_POS,Likelihood_pos, Likelihood_neg,x_sampled):
    # Likelihood from KDE, no longer log-probability, properly normalized
    # data x model

    likelihood = np.transpose(np.vstack((Likelihood_neg, Likelihood_pos)))
    #st.write('np.sum(likelihood,1)',np.shape(likelihood),np.sum(likelihood,1))

    X_input_prior_weight_POS = np.outer(np.ones((np.shape(likelihood)[0],)),Pr_input_POS )
    X_input_prior_weight_NEG = np.outer(np.ones((np.shape(likelihood)[0],)),1.0-Pr_input_POS )
    X_input_prior_weight= np.hstack((X_input_prior_weight_NEG,X_input_prior_weight_POS))

    #st.write('Input Prior Weight array:', np.shape(X_input_prior_weight), X_input_prior_weight[0:10])
    Pr_InputMarg = np.sum(X_input_prior_weight * likelihood,1) # sum across model classes, columns

    X_unif_prior_weight = np.transpose(np.outer(np.ones((np.shape(likelihood)[1],)), 0.5))
    #print('Uniform Prior array:', X_unif_prior_weight)
    Pr_UnifMarg= np.sum(X_unif_prior_weight * likelihood,1)  # sum over model classes, columns
    
    #st.write('Pr_InputMarg',np.shape(Pr_InputMarg), np.sum(Pr_InputMarg))
    #st.write(Pr_InputMarg)
    # st.write('Pr_UnifMarg',Pr_UnifMarg)
  
    # # Plot for looking at marginal(s)
    figM, axes = plt.subplots(figsize=(15,8),ncols=1)
    axes.plot(x_sampled,Pr_InputMarg,'.',color='orange', label='Pr_InputMarg')
    # axes.plot(x_sampled,Pr_InputMarg[0,:],'.r')
    axes.plot(x_sampled,Pr_UnifMarg,'*g',label='marginal with unif prior')
    axes.legend()
    # st.pyplot(figM)

    # POSTERIOR
    InputMarg_weight = np.kron(Pr_InputMarg[:,np.newaxis],np.ones((1,np.shape([1-Pr_input_POS,Pr_input_POS])[0]))) # should be num classes, num of Thetas
    UnifMarg_weight = np.kron(Pr_UnifMarg[:,np.newaxis],np.ones((1,np.shape([0.5,0.5])[0])))
    #st.write('marginals as 2d array InputMarg_weight',InputMarg_weight)

    Prm_d_Uniform = X_unif_prior_weight * likelihood / UnifMarg_weight
    Prm_d_Input = X_input_prior_weight * likelihood / InputMarg_weight
    #st.write('Prm_d_Input',Prm_d_Input)

    return Pr_InputMarg, Pr_UnifMarg, Prm_d_Input, Prm_d_Uniform


def make_value_array(count_ij, profit_drill_pos= 2e6, cost_drill_neg = -1e6):
    
    # make value_array with 
    #  rows= NUMBER OF decision alternatives
    number_a = 2
    # columns equal to subsurface conditions (decision variables) 
    # OLD
    # range_outcomes = np.arange(magnitude,-magnitude,-1000/number_loc)  
    # value_array = np.zeros((np.shape(count_ij)[0],np.shape(count_ij))[0]))
    
    value_array = np.zeros((number_a, np.shape(count_ij)[0]))
    
    value_array[0,:] = [0, 0]
    value_array[1,:] = [cost_drill_neg, profit_drill_pos] 

    index_labels = ['do nothing','drill']
    value_array_df = pd.DataFrame(value_array,index=index_labels,columns=['negative','positive'])
    
    return value_array, value_array_df

def f_VPRIOR(PriorWeight, value_array_mod, *args):  

    """
    Function to calculate the prior value Vprior 

    Parameters
    PriorWeight: array-like [NEG , POS]
    value_array: the value array, contains the value outcomes for each possible 
          NEG/POS (row, was clay cap) and decision alternative (drill/nothing)
    cur_value_drill_DRYHOLE : float, optional, value amount for testing VOI sensitivity

    """
    cur_value_drill_DRYHOLE = None 
    for n in args:
      cur_value_drill_DRYHOLE = n

    if cur_value_drill_DRYHOLE is not None:    
        value_array_mod[1,0] = cur_value_drill_DRYHOLE
        
    #print('modified value_array_mod',value_array_mod)    
    prm = PriorWeight #np.hstack((PriorWeight))

    v_a = []
    # st.write('value_array_mod',value_array_mod)
    # Loop over all alternatives : Eventually be Nx * Ny alternatives
    for na in np.arange(0,np.shape(value_array_mod)[0]): # alternatives here are rows...
        cur_a = np.sum(prm*value_array_mod[na,:])
        # st.write('prm, ROW value_array_mod, SUM cur_a',prm,value_array_mod[na,:],cur_a)
        v_a = np.append(v_a, cur_a)

    
    Vprior = np.max(v_a) ; 
    #print('Vprior=', Vprior)
    
    return Vprior

def Vperfect(input_prior, value_array_mod, *args):
     ## $VOI_{Perfect}$ doesn't need data loop: diagonal of value matrix

    cur_value_drill_DRYHOLE = None 
    for n in args:
      cur_value_drill_DRYHOLE = n

    if cur_value_drill_DRYHOLE is not None:    
        value_array_mod[1,0] = cur_value_drill_DRYHOLE 
     
    VPI = np.sum(input_prior * np.max(value_array_mod,0))

    return VPI

def marginal(Pr_prior_POS, predictedLikelihood_pos, predictedLikelihood_neg, x_sampled):
    """
     How frequent is each data bin?
      in clay cap code: np.sum(X_unif_prior_weight * likelihood,0) where SUM is over model...
      Returns [2 X nbins] marginal
    """
    marg_input_POS = Pr_prior_POS * np.exp(predictedLikelihood_pos)
    marg_input_NEG = (1-Pr_prior_POS) * np.exp(predictedLikelihood_neg)
    marg_w = 1.0 / np.sum(marg_input_POS+marg_input_NEG)
    
    #    likesum = np.exp(predictedLikelihood_pos)+np.exp(predictedLikelihood_neg)
        # scale = 1.0/likesum
    figT, axes = plt.subplots(figsize=(15,8),ncols=1)
    axes.plot(x_sampled,np.exp(predictedLikelihood_pos),'.g')
    axes.plot(x_sampled,np.exp(predictedLikelihood_neg),'.r')
    axes.plot(x_sampled,marg_w*(marg_input_POS+marg_input_NEG),'*c')
    #st.pyplot(figT)
    #st.write('MARG SUM', np.sum(marg_w*(marg_input_POS+marg_input_NEG)))

    #return marg_w*np.vstack((marg_input_NEG, marg_input_POS)) ## what the hell is this?
    st.write('np.shape(Pr_d)',np.shape(marg_w*(marg_input_NEG+marg_input_POS)))
    return marg_w*(marg_input_NEG+marg_input_POS)

def f_VIMPERFECT(Prm_d,value_array,Pr_d,*args):
    """
    Function to calculate the highest decision action/alternative (a) given the 
    
    Parameters
    Prm_d : array_like, posterior. rows=data space, cols= neg, positive
    value_array : the value array, contains the value outcomes for each possible 
            NEG/POS (columns was clay cap) and decision alternative (rows drill/nothing)
    Pr_d : array_like, marginal probability, rows= data, cols= neg/pos
    cur_dryhole_value : float, optional, value amount for testing VOI sensitivity
    """
    cur_value_drill_DRYHOLE = None 
    for n in args:
      cur_value_drill_DRYHOLE = n

    v_aj_array = [] 

    ### If passed, adjust the value array for sensitivity testing. Put new values 
    # in the bottom row, first column and top row, last column
    if cur_value_drill_DRYHOLE is not None: 
        # value_array[-1,0] = cur_value_drill_DRYHOLE
        # value_array[0,-1] = cur_value_drill_DRYHOLE
        value_array[1,0] = cur_value_drill_DRYHOLE 

    v_a = []
    
    # st.write('np.shape(np.exp(Prm_d))',np.shape(np.exp(Prm_d)))
    # st.write('np.exp(Prm_d[0,0]),np.exp(Prm_d[0,-1]',np.exp(Prm_d[0,0]),np.exp(Prm_d[0,-1]))
    # st.write('np.exp(Prm_d[-1,0]),np.exp(Prm_d[-1,-1])',np.exp(Prm_d[-1,0]),np.exp(Prm_d[-1,-1]))
    # st.pyplot(plt.hist(Prm_d))

    ## # Loop through Interpretation bins ~X (columns of Prm_d)
    #for nl in np.arange(0, num_layers):
    v_aj = []
    for j in range(0,np.shape(Prm_d)[0]): #rows=data space, cols= neg, positive
        v_a = []
        ### v_a0 = PrmVul_d[:,j] * x_iVula0  + PrmComp_d[j] * x_iCompa0 
        #print('j: get average',j)
        for a in range(0,np.shape(value_array)[0]):  
            #   [(1 of N) array]  * [1 * M array]
            v_i= sum(Prm_d[j] * value_array[a,:]) # Prm_d: [neg,pos] v_a row: one action at a time
            #if j >90:
            #    print('Prm_d, v_a, (v_i) ', np.exp(Prm_d[j]), value_array[a,:], v_i)
            
            v_a = np.append(v_a, v_i)
        v_aj = np.append(v_aj, np.max(v_a))
    
    v_aj_array = np.append(v_aj_array,v_aj,axis=0)
    # st.write('v_aj_array',np.max(v_aj_array))
    # st.dataframe(Pr_d * v_aj_array)

    # VII:  Value WITH imperfect information
    # print('np.shape(Pr_d) np.sum(Pr_d)',np.shape(Pr_d), np.sum(Pr_d))
    # print(Pr_d[-10:])      
    VII = np.sum(Pr_d * v_aj_array)

    return VII