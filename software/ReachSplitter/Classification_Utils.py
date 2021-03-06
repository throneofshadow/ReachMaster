"""
    Written by Brett Nelson, UC Berkeley/ Lawrence Berkeley National Labs, NSDS Lab 12/8/2020

    This code is intended to create and implement structure supervised classification of coarsely
    segmented trial behavior from the ReachMaster experimental system.
    Functions are designed to work with a classifier of your choice.

    Edited: 12/8/2020
"""

import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn import decomposition
from sklearn import preprocessing
import pandas as pd
import pdb
from sklearn.pipeline import make_pipeline
from yellowbrick.model_selection import CVScores
from yellowbrick.features import Rank2D
from Classification_Visualization import visualize_model, print_preds, plot_decision_tree
from yellowbrick.classifier import ClassificationReport
import DataStream_Vis_Utils as utils

def make_vectorized_labels(blist):
    """

    :param blist: list of labels, for more robust description please see github
    :return:
            new_list : vectorized list of labels
            ind_total : vectorized array of reaching indices
    """
    ll = len(blist)
    new_list = np.empty((ll, 9))
    ind_total = []
    for ix, l in enumerate(blist):
        # l has index of [int trial_num, int start, int stop, int trial_type, int num_reaches, str which_hand_reach, str tug_noTug, int hand_switch, int num_frames]
        # we want to vectorize this list for use in ML-standard format (0,1 etc)

        # transform non-numerics into numeric template
        # arm type
        # 'lr': 2 , 'l' : 1, 'bi' : 3 , 'lbi' : 4, 'r': 0, 'tug': 1
        if 'l' in str(l[5]):
            if 'lr' in str(l[5]):
                blist[ix][5] = 2
            else:
                blist[ix][5] = 1
        elif 'bi' in str(l[5]):
            if 'lbi' in str(l[5]):
                blist[ix][5] = 4
            else:
                blist[ix][5] = 3
        if 'r' in str(l[5]):
            blist[ix][5] = 0
        if l[5] == 0:
            blist[ix][5] = 5  # null trial
        try:
            if 'no' in str(l[6]):
                blist[ix][6] = 0
            else:
                blist[ix][6] = 1
        except:
            continue
        # code to split off any trial indices
        try:
            if len(l) > 9:  # are there indices?
                ind_total.append([l[9], l[10]])
            if len(l) > 11:  # second indices?
                ind_total.append([l[11], l[12]])
            if len(l) > 13:
                ind_total.append([l[13], l[14]])
            if len(l) > 15:
                ind_total.append([l[15], l[16]])
            if len(l) > 17:
                ind_total.append([l[17], l[18]])
            if len(l) > 19:
                ind_total.append([l[19], l[20]])
        except:
            print(ix)
        new_list[ix, :] = blist[ix][0:9]
    return new_list, np.array(ind_total)


def xform_array(k_m, eit, cl):
    k = np.asarray(k_m)
    # rv=np.dot(k.reshape(k.shape[2],27,3),eit)+cl # good Xform value, then use this value
    return k_m


def transpose_kin_array(kc,et,el):
    # kc is dtype pandas dataframe
    # we want numpy data format
    # kc['colname'].to_numpy()
    for items in kc.items():
        pdb.set_trace()
        if 'X' in items[0][1]:
            kc[items[0]] = xform_array(kc[items[0]], et, el)
        if 'Y' in items[0][1]:
            kc[items[0]] = xform_array(kc[items[0]], et, el)
        if 'Z' in items[0][1]:
            kc[items[0]] = xform_array(kc[items[0]], et, el)
    return kc


def filter_obvious_outliers(x, k):
    # Code for median filtering function taken from https://gist.github.com/bhawkins/3535131.
    assert k % 2 == 1, "Median filter length must be odd."
    assert x.ndim == 1, "Input must be one-dimensional."
    k2 = (k - 1) // 2
    y = np.ones((len(x), k), dtype=x.dtype)
    y[:, k2] = x
    for i in range(k2):
        j = k2 - i
        y[j:, i] = x[:-j]
        y[:j, i] = x[0]
        y[:-j, -(i + 1)] = x[j:]
        y[-j:, -(i + 1)] = x[-1]
    return np.median(y, axis=1)


def block_pos_extract(kin_df, et, el, wv):
    x_arr_ = []
    y_arr_ = []
    z_arr_ = []
    feat_name = []
    for (columnName, columnData) in kin_df.iteritems():
        feat_name.append(columnName[0])
        try:
            if columnName[1] == 'X':
                x_arr_.append(filter_obvious_outliers(columnData.values, wv))
            if columnName[1] == 'Y':
                y_arr_.append(filter_obvious_outliers(columnData.values, wv))
            if columnName[1] == 'Z':
                azir = filter_obvious_outliers(columnData.values, wv)
                z_arr_.append(azir)
                #print(np.where(azir == 0))
        except:
            print('No filtering..')
            pdb.set_trace()
    # transform the coordinates in each block
    try:
        block = xform_array([x_arr_, y_arr_, z_arr_], et, el)
    except:
        print('o')
    # print(np.where(block==0))
    return block, feat_name


def reshape_posture_trials(a):
    pdb.set_trace()
    for ix, array in enumerate(a):
        #yarr = ykin[ix]
        #zarr = zkin[ix]
        if ix == 0:
            arx = a

        else:
            ar = np.vstack((a))
            pdb.set_trace()
            arx = np.concatenate((arx, ar))
    return arx


def split_trial(posture_array, _start, window_length, pre):
    # posture array is timexfeatx 3 x coords np array
    # ML format is time x feat x coords
    #
    posture_array = np.asarray(posture_array)
    trials_list = np.empty((len(_start), posture_array.shape[0], posture_array.shape[1], window_length + pre))
    for i, jx in enumerate(_start):
        try:
            c = posture_array[:, :, jx - pre:jx + window_length]  # get time-series segment
            trials_list[i, :, :, :] = c
        except:
            print('no Kinematic Data imported')
            return 0

    return trials_list


def onehot(r_df):
    try:
        m = len(r_df['r_start'].values[0])
    except:
        print('onehot vector error')
        # pdb.set_trace()
    sf = r_df['SF'].values[0]
    hot_vec = np.zeros(m, dtype=int)
    hot_vec[sf] = 1
    return np.asarray(hot_vec)


def unwind_list(strial_list):
    for ix, trial in enumerate(strial_list):
        if ix == 0:
            tsx = trial
        if ix != 0:
            try:
                tsx = np.concatenate((tsx, trial), axis=0)
            except:
                print('concat error in unwind_list')
                # pdb.set_trace()
    return tsx


def reshape_list(strial_list):
    # pdb.set_trace()
    try:
        length, width, height = np.array(strial_list[0]).shape
        num_trials = len(strial_list)
        # make empty array
        emp = np.empty((num_trials, length, width, height))
        # loop over len num_trials
        for iterz, trials in enumerate(strial_list):
            ts = np.array(trials)
            try:
                emp[iterz, :, :, :] = ts
            except:
                emp[iterz, :, :, :] = np.zeros((length, width, height))
    except:
        # pdb.set_trace()
        print('Problem with reshaping the list..')
    return emp


def forward_xform_coords(x, y, z):
    Axx = 168
    Ly = 64
    Ayy = 100
    Lz = 47
    Azz = 117
    X0 = 1024
    Y0 = 608
    Z0 = 531
    Ax_est = (x - X0) / (1024 * 50) + Axx
    Ay_est = (y - Y0) / (1024 * 50) + Ayy
    Az_est = (z - Z0) / (1024 * 50) + Azz
    c1 = np.asarray((0, 0, 0))
    c2 = np.asarray((Ly, Ayy, 0))
    c3 = np.asarray((Lz, 0, Azz))
    u = np.asarray((Ly, Ayy, 0)) / np.sqrt(Ly ** 2 + Ayy ** 2)
    v = c3 - np.dot(c3, u) * u
    v = v / np.sqrt(np.dot(v, v))
    w = np.cross(u, v)
    y1 = np.asarray((0, 1, 0))
    z1 = np.asarray((0, 0, 1))
    U2 = np.sqrt(np.sum((c2 - c1) ** 2))
    U3 = np.dot(c3, u)
    V3 = np.dot(c3, v)
    sd = np.dot(c3, c3)
    cos_top = (Az_est ** 2 + Lz ** 2 - sd)
    cos_bot = (2 * Az_est * Lz)
    r3 = np.sqrt(
        Az_est ** 2 + (Ly - Lz) ** 2 - (2 * Az_est * (Ly - Lz) * np.cos(np.pi - np.arccos((Az_est ** 2 + Lz ** 2 - sd)
                                                                                          / (2 * Az_est * Lz)))))
    Pu = (Ly ** 2 - Ay_est ** 2 + U2 ** 2) / (2 * U2)
    Pv = (U3 ** 2 + V3 ** 2 - 2 * U3 * Pu + Ly ** 2 - r3 ** 2) / (2 * V3)
    Pw = np.sqrt(-Pu ** 2 - Pv ** 2 + Ly ** 2)
    Py = Pu * np.dot(u, y1) + Pv * np.dot(v, y1) + Pw * np.dot(w, y1)
    Pz = Pu * np.dot(u, z1) + Pv * np.dot(v, z1) + Pw * np.dot(w, z1)
    gammay_est = np.arcsin(Py / (Ly * np.cos(np.arcsin(Pz / Ly))))
    gammaz_est = np.arcsin(Pz / Ly)
    r = np.sqrt(Axx ** 2 + Ax_est ** 2 - (2 * Axx * Ax_est * np.cos(gammay_est) * np.cos(gammaz_est)))
    dz = np.sin(-gammaz_est)
    dy = np.sin(-gammay_est)
    theta = np.arcsin(dz * Ax_est / r)
    phi = np.arcsin(Ax_est * dy * np.cos(-gammaz_est) / r / np.cos(theta))
    x = r * np.cos(theta) * np.cos(phi)
    y = r * np.sin(theta) * np.cos(phi)
    z = r * np.sin(phi)
    return r, theta, phi, x, y, z


def calculate_robot_features(xpot, ypot, zpot, mstart_, mstop_):
    sample_rate = 30000  # sample rate from analog
    # split into sample
    start__ = int(mstart_ * sample_rate)
    stop__ = int(mstop_ * sample_rate)
    xp = xpot[start__:stop__]
    yp = ypot[start__:stop__]
    zp = zpot[start__:stop__]
    r1, theta1, phi1, x1, y1, z1 = forward_xform_coords(xp, yp, zp)  # units of meters
    # vta = np.diff(vt)
    try:
        vx = np.diff(x1) / 30000  # units of seconds
        vy = np.diff(y1) / 30000  # units of seconds
        vz = np.diff(z1) / 30000  # units of seconds
    except:
        print('bad potentiometer derivatives')
        pdb.set_trace()
    # ve=np.absolute(np.gradient(np.asarray([x1,y1,z1]),axis=0))/30000
    # ae = np.gradient(ve)/30000
    return vx, vy, vz, x1, y1, z1


def import_experiment_features(exp_array, starts, window_length, pre, m_start, m_stop):
    # features to extract from experiment array : pot_x, pot_y, pot_z, lick_array, rew_zone robot features
    wlength = (starts[0] + window_length) - (
                starts[0] - pre)  # get length of exposures we are using for trial classification
    exp_feat_array = np.empty((len(starts), 11, wlength))  # create empty np array Ntrials X Features X Length
    for ixs, vals in enumerate(starts):  # loop over each trial
        # get experimental feature values
        try:
            time_ = exp_array['time'].to_numpy()[0]
            rz = exp_array['RW'].to_numpy()[0]
        except:
            print('f1')
            pdb.set_trace()
        try:
            rz = rz[vals - pre:vals + window_length]
            lick = exp_array['lick'].to_numpy()[0]
            exp_time = np.asarray(time_, dtype=float) - time_[0]
            lmi = np.searchsorted(exp_time, lick)
            # get lick times, subtract time[0] from lick times (this normalizes them to cam data), then make your vector
            lick_mask_array = np.zeros(exp_time.shape[0] + 1, dtype=int)
            lick_mask_array[lmi] = 1
            np.delete(lick_mask_array, [-1])
        except:
            print('f2')
            pdb.set_trace()
        try:
            vcx, vcy, vcz, xp1, yp1, zp1 = calculate_robot_features(exp_array['x_pot'].to_numpy()[0],
                                                                    exp_array['y_pot'].to_numpy()[0],
                                                                    exp_array['z_pot'].to_numpy()[0],
                                                                    m_start[ixs], m_stop[ixs])
        except:
            print('bad pot data')
            pdb.set_trace()
        # fill in array
        # decimate potentiometer from s to exposure !~ in frames (we dont have exact a-d-c)
        try:
            xp1 = xp1[::213]
            yp1 = yp1[::213]
            zp1 = zp1[::213]
            vcx = vcx[::213]
            vcy = vcy[::213]
            vcz = vcz[::213]
        except:
            print('bad downsample')
            pdb.set_trace()
        # downsample potentiometer readings to match camera exposures
        # each exposure is ~ 213hz
        # make same length as other features, to avoid problems with ML (this means we will lose ~5 data points at end of experiment)
        try:
            xp1 = xp1[0:wlength]
            yp1 = yp1[0:wlength]
            zp1 = zp1[0:wlength]
            vcx = vcz[0:wlength]
            vcy = vcy[0:wlength]
            vcz = vcz[0:wlength]
        except:
            print('bad decimate')
            pdb.set_trace()
        try:
            exp_feat_array[ixs, 0:3, :] = [vcx, vcy, vcz]
        except:
            print(exp_feat_array[ixs, 0:3, :])
            continue
        try:
            exp_feat_array[ixs, 6, :] = rz
            exp_feat_array[ixs, 7, :] = xp1
            exp_feat_array[ixs, 8, :] = yp1
            exp_feat_array[ixs, 9, :] = zp1
            exp_feat_array[ixs, 10, :] = lick_mask_array[vals - pre:vals + window_length]
        except:
            print('bad robot data fit')
    print('Finished experimental feature generation')
    return exp_feat_array


def make_s_f_trial_arrays_from_block(kin_array_, robot_array_, et, el, rat, date, kdate, session, wv=5, window_length=800,
                                     pre=100):
    try:
        kim_df = kin_array_[kin_array_.index.get_level_values('rat') == rat][
            kin_array_.index.get_level_values('date') == kdate]
        kc = kim_df[kim_df.index.get_level_values('session') == session]
        _a, _feat_labels = block_pos_extract(kc, et, el, wv)
    except:
        print('Not in kinematic array : Trial ' + rat + date + session)
        return 0, 0, 0
    r_df = utils.get_single_trial(robot_array_, date, session, rat)
    start = r_df['r_start'].values[0]
    m_start = r_df['m_start'].values[0]
    m_stop = r_df['m_stop'].values[0]
    try:
        exp_features = import_experiment_features(r_df, start, window_length, pre, m_start, m_stop)
    except:
        print('bad robot feature extraction')
        exp_features = 0
        pdb.set_trace()
    _tt1 = split_trial(_a, start, window_length, pre)
    print('Finished trial splitting')
    _hot_vector = onehot(r_df)
    return _hot_vector, _tt1, _feat_labels, exp_features


def match_stamps(kinematic_array_, label_array, exp_array_):
  # Create trial arrays
    len_array = len(label_array)
    try:
        mk_array = np.empty((len_array, kinematic_array_[0].shape[0], kinematic_array_[0].shape[1],
                             kinematic_array_[0].shape[2]))
    except:
        print('No Kinematic Data to Match')
        pdb.set_trace()
    try:
        ez_array = np.empty((len_array, exp_array_.shape[1], exp_array_.shape[2]))
    except:
        print('Bad Robot Data Pass')
        pdb.set_trace()
  # From label array, first column states the trial # of the row
    for dr, tval in enumerate(label_array):
        # iterate over the index and value of each trial element
        ixd=int(label_array[dr][0]) # get trial #
        #pdb.set_trace()
        try:
            mk_array[ixd, :, :, :] = kinematic_array_[ixd, :, :, :]
            ez_array[ixd, :, :] = exp_array_[ixd, :, :]
        except:
            print('Cant set kinematic and robot arrays in place')
    return mk_array, ez_array


def create_ML_array(matched_kinematics_array,matched_exp_array):
    mid_amt = matched_kinematics_array.shape[1]*matched_kinematics_array.shape[2]
    l=matched_kinematics_array.shape[3]
    tl=matched_kinematics_array.shape[0]
    ctc = np.concatenate((matched_kinematics_array.reshape(tl,mid_amt,l), matched_exp_array),axis=1)
    return ctc


def stack_ML_arrays(list_of_k, list_of_f):
    for idd, valz in enumerate(list_of_k):
        if idd == 0:
            ogk = valz
            ogf = list_of_f[idd]
        else:
            ogk = np.vstack((ogk, valz))
            ogf = np.vstack((ogf, list_of_f[idd]))

    return ogk, ogf


def norm_and_zscore_ML_array(ML_array, robust=False, decomp=False, gauss=False):
    """
    default preprocessing is simple MinMax L1 norm
    input
    ML_array : array shape : (Cut Trials, Features, Frames)   where Cut Trials refers to either the number of Trials
    inside the testing data or training data (Don't call this function for just the total ML data, split beforehand..)
    robust: boolean flag, use sci-kit learn robust scaling to normalize our data
    decomp : boolean flag, post-processing step used to return first whitened 20 PCA components to remove linear dependence
    gauss : boolean flag, use sci-kit learn gaussian distribution scaling to normalize our data
    """
    # ML_array
    if robust:
        pt = preprocessing.robust_scale()
    elif gauss:
        pt = preprocessing.PowerTransformer(method='box-cox', standardize=False)
    else:
        pt = preprocessing.MinMaxScaler()

    r_ML_array = pt.fit_transform(ML_array.reshape(ML_array.shape[0], ML_array.shape[1] * ML_array.shape[2]))
    # apply normalization to feature axis
    if decomp:  # used to decomp linear correlations, if they exist.
        pca = decomposition.PCA(n=20, whiten=True)
        r_ML_array = pca.fit(r_ML_array)

    return r_ML_array


def split_ML_array(Ml_array, labels_array, t=0.2):
    X_train, X_test, y_train, y_test = train_test_split(Ml_array, labels_array, test_size=t, random_state=0)
    return X_train, X_test, y_train, y_test


def onehot_nulls(type_labels_):
    # kwargs: n_f_fr_s_st: Trial type (null, failed, failed_rew,s ,succ_tug), label key [0, 1, 2, 3, 4]
    null_labels = np.zeros((type_labels_.shape[0]))
    null_labels[np.where(type_labels_ == 0)] = 1  # 1 if null, 0 if real trial
    return null_labels


def onehot_num_reaches(num_labels_):
    num_r_labels = np.zeros((num_labels_.shape[0]))  # 0 vector
    num_r_labels[np.where(num_labels_ > 1)] = 1  # 0 if <1, 1 if > 1 reaches
    return num_r_labels


def hand_type_onehot(hand_labels_, simple=True):
    # 'lr': 2 , 'l' : 1, 'bi' : 3 , 'lbi' : 4, 'r': 0,
    hand_type_label = np.zeros((hand_labels_.shape[0]))
    if simple:
        hand_type_label[np.where(hand_labels_ > 1)] = 1  # classify all non r,l reaches as 0 vector
    else:
        hand_type_label[np.where(hand_labels_ > 2)] = 1  # classify 0 as r, l + 'rl'
    return hand_type_label


def get_ML_labels(fv):
    # #[int trial_num, int start, int stop,
    # int trial_type, int num_reaches, str which_hand_reach, str tug_noTug, int hand_switch, int num_frames]
    # shape (Trials, 9 ^)
    fv = fv[:, 3:-1]  # take label catagories necessary for trial classification
    type_labels = onehot_nulls(fv[:, 0])  # labels for trial type
    num_labels = onehot_num_reaches(fv[:, 1])  # labels for num reaches in trial
    hand_labels = hand_type_onehot(fv[:, 2])  # labels for which hand
    tug_labels = fv[:, 3]  # labels for tug/no tug, tug = 1
    switch_labels = fv[:, 4]  # labels for hand switching (y/n), 1 is switch
    return [type_labels, num_labels, hand_labels, tug_labels, switch_labels]


def run_classifier(_model, _X_train, _X_test, input_labels):
    """
    Function for manually running a given model, intended for hard-code/troubleshooting.
    """
    _model.fit(_X_train, input_labels)
    type_pred = _model.predict(_X_test)
    type_feature_imp = pd.Series(_model.feature_importances_).sort_values(ascending=True)
    return [type_pred, type_feature_imp]


def classification_structure(ml, feature, model_,kFold=False,LOO=False,PCA_data=False,constant_split=False,structured=True,
                             plot_correlation_matrix=False,pred=False,disc=True,bal=True,conf=True): # add kFold argument
    """
    ml : ML-ready feature vector containing experimental and kinematic data
    feature : labels for each class (vectorized using blist and get_ML_labels)
    model : classifier (sk-Learn compatible)
    kFold : int, number of folds if using kFold cross-validation from sk-Learn
    LOO : boolean flag, set True if using LOO cross-validation from sk-Learn
    PCA : boolean flag, set True if using PCA to reduce dimensions of feature vectors
    constant_split : boolean flag, set True if comparing results between classifiers

    """
    # split before norming to prevent bias in test data
    classifier_pipeline = make_pipeline(preprocessing.StandardScaler(), model_)
    if constant_split:
        cs=[]
        X_train, X_test, y_train, y_test = split_ML_array(ml, feature, t=0.2)
        train_labels = get_ML_labels(y_train)
        X_train = norm_and_zscore_ML_array(X_train, robust=False, decomp=False, gauss=False)
        X_test = norm_and_zscore_ML_array(X_test, robust=False, decomp=False, gauss=False)
        for i, vals in enumerate(train_labels):
            cs.append(run_classifier(model_,X_train, X_test, vals, 0))
            # need to add cross_val_score for X_train,X_test splits

        return cs, model_

    # Create Classifier Pipeline Object in SciKit Learn
    if PCA_data:
        classifier_pipeline = make_pipeline(preprocessing.StandardScaler(),
                                            decomposition.PCA(n_components=int(PCA_data)), model_)
    else:
        classifier_pipeline = make_pipeline(preprocessing.StandardScaler(), model_)
    # For simple Classifier:
    X_train, X_test, y_train, y_test = split_ML_array(ml, feature, t=0.2)
    # generate correct labels for test/train labels
    train_labels = get_ML_labels(y_train)
    # norm and z-score test/train features
    X_train = norm_and_zscore_ML_array(X_train, robust=False, decomp=False, gauss=False)
    X_test = norm_and_zscore_ML_array(X_test, robust=False, decomp=False, gauss=False)
    # Feature Work
    if PCA_data:
        pcs = decomposition.PCA()
        X_train = pcs.fit(X_train)
        X_test = pcs.fit(X_test)
        for ii,mi in enumerate(pcs.explained_variance_ratio_[:].sum()):
            if mi > .99:
                n_comps=ii
        X_train = X_train[0:ii,:]
        X_test = X_test[0:ii,:]

    if plot_correlation_matrix:
        pearson_features(X_train)

    preds = []
    if structured:
        for idx, vals in enumerate(train_labels):
            # check for important class, then train inputs
            if idx == 0: # Reach vs Null
                # Save ML predictions, models
                preds.append(cross_val_score(classifier_pipeline,
                                            ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]),
                                            get_ML_labels(feature)[idx], cv=kFold))
                # Plot in Yellowbrick
                visualizer = CVScores(classifier_pipeline, cv=kFold, scoring='f1_weighted')
                visualizer.fit(ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]), get_ML_labels(feature)[idx])
                visualizer.show()
                visualize_model(ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]), get_ML_labels(feature)[idx]
                                , classifier_pipeline,pred=pred,disc=disc, conf=conf, bal=bal)
            if idx == 1: # num reaches, 1 vs >1
                # Save ML predictions, models
                preds.append(cross_val_score(classifier_pipeline,
                                             ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]),
                                             get_ML_labels(feature)[idx], cv=kFold))
                # Plot in Yellowbrick
                visualizer = CVScores(classifier_pipeline, cv=kFold, scoring='f1_weighted')
                visualizer.fit(ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]), get_ML_labels(feature)[idx])
                visualizer.show()
                visualize_model(ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]), get_ML_labels(feature)[idx]
                                , classifier_pipeline,pred=pred,disc=disc, conf=conf, bal=bal)
            if idx ==3: # l/r vs lra,bi,rla
                # Save ML predictions, models
                preds.append(cross_val_score(classifier_pipeline,
                                             ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]),
                                             get_ML_labels(feature)[idx], cv=kFold))
                # Plot in YellowBrick
                visualizer = CVScores(classifier_pipeline, cv=kFold, scoring='f1_weighted')
                visualizer.fit(ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]), get_ML_labels(feature)[idx])
                visualizer.show()
                visualize_model(ml.reshape(ml.shape[0], ml.shape[1] * ml.shape[2]), get_ML_labels(feature)[idx]
                                , classifier_pipeline,pred=pred,disc=disc, conf=conf, bal=bal)
    else:
        for i, vals in enumerate(train_labels):  # loop over each layer of classifier, this just does classification
            try:
                if KFold:
                    preds.append(cross_val_score(classifier_pipeline,
                                    ml.reshape(ml.shape[0], ml.shape[1]*ml.shape[2]), get_ML_labels(feature)[i], cv=kFold))
                elif LOO:
                    preds.append(cross_val_score(classifier_pipeline, ml.reshape(ml.shape[0], ml.shape[1]*ml.shape[2]),
                                                 get_ML_labels(feature)[i], cv=ml.shape[0]-10))
                else:# simple classification
                    preds.append(run_classifier(model_, X_train, X_test, vals, 0))
                    continue
            except:
                print('Bad Classifier Entry (Line 500)')
                pdb.set_trace()
        try:
            print_preds(preds,train_labels)
        except:
            print('')
    return preds, model_


def pearson_features(ml_array_):
    feat_visualizer = Rank2D(algorithm="pearson")
    feat_visualizer.fit_transform(ml_array_)
    feat_visualizer.show()


def is_tug_no_tug():
    """
    Function to classify trials with post-reaching behavior from well-behaved handle release.
    """
    # ask if there is robot velocity after a trial ends (for around a second)
    tug_preds=[]
    return tug_preds


def is_reach_rewarded(lick_data,start,stop):
    """
    Function to simply classify trials as rewarded with water or not using sensor data from ReachMaster (lick detector).

    """
    reward_vector=[]
    return reward_vector