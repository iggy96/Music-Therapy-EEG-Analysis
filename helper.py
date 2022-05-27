from libs import*

def create_db_connection(host_name, user_name, user_password, database_name):
    # used to establish created database connection
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=database_name
        )
        print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return connection


def df_to_table_query(connection, query):
    # converts all sql queries user writes in python strings 
    # and passes it to cursor.execute() method to execute them
    # on the MYSQL server 
    cursor = connection.cursor()
    try:
        df = pd.read_sql(query, con=connection)
        print("Query successful")
    except Error as err:
        print(f"Error: '{err}'")
    return df


def sqlTableToDataframe(host_name,user_name,user_password,database_name,query):
    dbConnection = create_db_connection(host_name,user_name,user_password,database_name)
    sql_query = pd.read_sql_query (query,dbConnection)
    df = pd.DataFrame(sql_query)
    return df

def allSQLTableNames(hostName,userName,userPassword,databaseName):
    # Input: hostName,userName,userPassword,databaseName
    # Output: list of all table names in database
    db_connection = create_db_connection(hostName,userName,userPassword,databaseName)
    cursor = db_connection.cursor()
    cursor.execute("Show tables;")
    result = cursor.fetchall()
    result = [x[0] for x in result]
    return result


def multiSQLTablesToDataframes(hostName,userName,userPassword,databaseName,table_name):
    # Input: hostName,userName,userPassword,databaseName,table_name
    #        table_name is a list of all table names in database
    # Output: 2D array holding four channel tables
    def tableToDF(host_name,user_name,user_password,database_name,table_name):
        query = ("% s % s"%('SELECT * FROM', table_name))
        dbConnection = create_db_connection(host_name,user_name,user_password,database_name)
        sql_query = pd.read_sql_query (query,dbConnection)
        df = pd.DataFrame(sql_query)
        return df
    tables_ = []
    for i in range(len(table_name)):
        tables_.append(tableToDF(hostName,userName,userPassword,databaseName,table_name[i]))
    #tables_ = np.array(tables_,dtype=object)
    return tables_


def singleTransformToRawEEG(data,fs,collection_time,fs_setting):
    #   Inputs  :   data    - one dataframe of unfiltered EEG data
    #   upsampling is common for muse eeg if the custom setting is utilized
    #   fs = desired sampling frequency
    #   'constant':eeg signals generated at this rate is perfect
    data = data.dropna()
    rawEEG = data
    t_len = len(rawEEG)
    period = (1.0/fs)
    time_s = np.arange(0, t_len * period, period)
    if fs_setting == 'resample':
        rawEEG = signal.resample(rawEEG,fs*collection_time)
        t_len = len(rawEEG)
        period = (1.0/fs)
        time_s = np.arange(0, t_len * period, period)
    elif fs_setting == 'constant':
        pass
    return rawEEG,time_s


def multiTransformTableToRawEEG(data,fs,collection_time,fs_setting):
    #   Inputs  :   data    -multiple dataframes of unfiltered EEG data
    #   upsampling is common for muse eeg if the custom setting is utilized
    #   fs = desired sampling frequency
    #   'constant':eeg signals generated at this rate is perfect
    #   Outputs  :   rawEEG  - multiple 2D arrays of raw EEG data collapsed in a 3D array
    newRawEEG = []
    for i in range(len(data)):
        newRawEEG.append((singleTransformToRawEEG(data[i],fs,collection_time,fs_setting))[0])
    newRawEEG = np.dstack(newRawEEG)
    newRawEEG = newRawEEG.reshape(newRawEEG.shape[2],newRawEEG.shape[0],newRawEEG.shape[1])
    return newRawEEG

def meanComparisonPlots(tp1,tp2,chanName,groups,plot_title):
    groupA_T1 = np.mean(tp1[0],axis=0)
    groupA_T2 = np.mean(tp2[0],axis=0)
    groupB_T1 = np.mean(tp1[1],axis=0)
    groupB_T2 = np.mean(tp2[1],axis=0)
    grpA_std_T1 = np.std(tp1[0],axis=0)
    grpA_std_T2 = np.std(tp2[0],axis=0)
    grpB_std_T1 = np.std(tp1[1],axis=0)
    grpB_std_T2 = np.std(tp2[1],axis=0)
    length = len(groupA_T1)
    x_labels = chanName
    # Set plot parameters
    fig, ax = plt.subplots()
    width = 0.2 # width of bar
    x = np.arange(length)

    ax.bar(x,groupA_T1, width, color='#90EE90', label=groups[0], yerr=grpA_std_T1)
    ax.bar(x + width,groupA_T2, width, color='#013220', label=groups[1], yerr=grpA_std_T2)
    ax.bar(x + (2 * width),groupB_T1, width, color='#C4A484', label=groups[2], yerr=grpB_std_T1)
    ax.bar(x + (3 * width),groupB_T2, width, color='#654321', label=groups[3], yerr=grpB_std_T2)
    ax.set_ylabel('Average Band Power')
    #ylim = np.amax()
    #ax.set_ylim(0,1000)
    ax.set_xticks(x + width + width/2)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel('Channels')
    ax.set_title(plot_title)
    ax.legend()
    plt.grid(True, 'major', 'y', ls='--', lw=.5, c='k', alpha=.3)
    fig.tight_layout()
    plt.show()
    pass


def plots(x,y,titles,figsize,pltclr):
    x_lim = [x[0],x[-1]]
    if len(y.T) % 2 != 0:
        nrows,ncols=1,int(len(y.T))
    elif len(y.T) % 2 == 0:
        nrows,ncols=2,int(len(y.T)/2)
    fig, axs = plt.subplots(nrows,ncols,sharex=True,sharey=True,figsize=(figsize[0],figsize[1]))
    for i, axs in enumerate(axs.flatten()):
        axs.plot(x, y[:,i], color=pltclr[i])
        axs.set_title(titles[i])
        axs.set_ylim([np.max(y[:,i])+1000,np.min(y[:,i])-1000])
        axs.set_xlim([x_lim[0],x_lim[1]])
        axs.set(xlabel='Time (s)', ylabel='Amplitude (uV)')
        axs.label_outer()


class filters:
    # filters for EEG data
    # filtering order: adaptive filter -> notch filter -> bandpass filter (or lowpass filter, highpass filter)
    def notch(self,data,line,fs,Q):
        #   Inputs  :   data    - 2D numpy array (d0 = samples, d1 = channels) of unfiltered EEG data
        #               cut     - frequency to be notched (defaults to config)
        #               fs      - sampling rate of hardware (defaults to config)
        #               Q       - Quality Factor (defaults to 30) that characterizes notch filter -3 dB bandwidth bw relative to its center frequency, Q = w0/bw.   
        #   Output  :   y     - 2D numpy array (d0 = samples, d1 = channels) of notch-filtered EEG data
        #   NOTES   :   
        #   Todo    : report testing filter characteristics
        cut = line
        w0 = cut/(fs/2)
        b, a = signal.iirnotch(w0, Q)
        y = signal.filtfilt(b, a, data, axis=0)
        return y

    def butterBandPass(self,data,lowcut,highcut,fs,order):
        #   Inputs  :   data    - 2D numpy array (d0 = samples, d1 = channels) of unfiltered EEG data
        #               low     - lower limit in Hz for the bandpass filter (defaults to config)
        #               high    - upper limit in Hz for the bandpass filter (defaults to config)
        #               fs      - sampling rate of hardware (defaults to config)
        #               order   - the order of the filter (defaults to 4)  
        #   Output  :   y     - 2D numpy array (d0 = samples, d1 = channels) of notch-filtered EEG data
        #   NOTES   :   
        #   Todo    : report testing filter characteristics
        # data: eeg data (samples, channels)
        # some channels might be eog channels
        low_n = lowcut
        high_n = highcut
        sos = butter(order, [low_n, high_n], btype="bandpass", analog=False, output="sos",fs=fs)
        y = sosfiltfilt(sos, data, axis=0)
        return y

def rollingWindow(array,window_size,freq):
    #   Inputs  :   array    - 2D numpy array (d0 = samples, d1 = channels) of filtered EEG data
    #               window_size - size of window to be used for sliding
    #               freq   - step size for sliding window 
    #   Output  :   3D array (columns of array,no of windows,window size)
    def rolling_window(array, window_size,freq):
        shape = (array.shape[0] - window_size + 1, window_size)
        strides = (array.strides[0],) + array.strides
        rolled = np.lib.stride_tricks.as_strided(array, shape=shape, strides=strides)
        return rolled[np.arange(0,shape[0],freq)]
    out_final = []
    for i in range(len(array.T)):
        out_final.append(rolling_window(array[:,i],window_size,freq))
    out_final = np.asarray(out_final).T
    out_final = out_final.transpose()
    return out_final

def customICA(input,tuneVal):
    # algorithm uses ICA to split the eeg into components to allow for easy extraction of ocular artefacts
    # Using the idea of the ASR algorithm, the tuneVal is the number of STD above the mean
    # eeg elements that fall into the class above the mean are artefactsa and replaced with 
    # the mean value of non-artefact elements
    val = tuneVal
    ica = FastICA(len(input.T),max_iter=200,tol=0.0001,random_state=0)
    components = ica.fit_transform(input)  

    def fixICAcomps(datae,val):
        mean = np.mean(datae, axis=0)
        sd = np.std(datae, axis=0)
        final_list = [x for x in datae if (x > mean - val * sd)]
        final_list = [x for x in final_list if (x < mean + val * sd)]
        final_list = np.asarray(final_list)

        def returnNotMatches(a, b):
            a = set(a)
            b = set(b)
            return [list(b - a), list(a - b)]

        rejected = np.asarray(returnNotMatches(datae,final_list)[1])
        rejected = rejected.reshape(len(rejected),1)
        idx = np.where(datae==rejected)[1]
        idx = idx.tolist()
        #idx = idx.reshape(len(idx),1)
        #datae = datae.reshape(len(datae),1)
        replace_vals = [np.mean(final_list)] * len(idx)
        fixedComps = [replace_vals[idx.index(i)] if i in idx else datae[i] for i in range(len(datae))]
        return fixedComps

    out_final = []
    for i in range(len(components.T)):
        out_init = fixICAcomps(components[:,i],val)
        out_final.append(out_init)
    out_final = np.asarray(out_final).T
    x_restored = ica.inverse_transform(out_final)
    return x_restored

def averageBandPower(data,arrayType,fs,low,high,win):
    #  Inputs  :   data    - 2D numpy array (d0 = samples, d1 = channels) of filtered EEG data
    #              or data - 3D numpy array (d0 = channels, d1 = no of windows, d2 = length of windows) of unfiltered EEG data
    #              arrayType - '2D' or '3D'
    #              fs      - sampling rate of hardware (defaults to config)
    #              low     - lower limit in Hz for the brain wave
    #              high    - upper limit in Hz for the brain wave
    #              win     - size of window to be used for sliding
    #   Output  :   3D array (columns of array,no of windows,window size)
    def absPower(data,fs,low,high,win):                                                 
        freqs, psd = signal.welch(data,fs,nperseg=win)
        idx_freqBands = np.logical_and(freqs >= low, freqs <= high) 
        freq_res = freqs[1] - freqs[0]                                  
        freqBand_power = round(simps(psd[idx_freqBands],dx=freq_res),3)      
        return freqBand_power
    if arrayType=='2D':
        avgBandPower = []
        for i in range(len(data.T)):
            avgBandPower.append(absPower(data[:,i],fs,low,high,win))
        avgBandPower= np.array(avgBandPower).T
    elif arrayType=='3D':
        avgBandPower = []
        for i in range(len(data)):
            x = data[i,:,:]
            for i in range(len(x)):
                avgBandPower.append(absPower(x[i,:],fs,low,high,win))
        avgBandPower= np.array(avgBandPower)
        avgBandPower = avgBandPower.reshape(len(x),len(data))
    return avgBandPower


def spectogramPlot(data,fs,nfft,nOverlap,figsize,titles):
    #   Inputs  :   data    - 2D numpy array (d0 = samples, d1 = channels) of filtered EEG data
    #               fs      - sampling rate of hardware (defaults to config)
    #               nfft    - number of points to use in each block (defaults to config)
    #               nOverlap- number of points to overlap between blocks (defaults to config)
    #               figsize - size of figure (defaults to config)
    #               titles  - titles for each channel (defaults to config)
    y = data
    if len(y.T) % 2 != 0:
        nrows,ncols=1,int(len(y.T))
    elif len(y.T) % 2 == 0:
        nrows,ncols=2,int(len(y.T)/2)
    fig, axs = plt.subplots(nrows,ncols,sharex=True,sharey=True,figsize=(figsize[0],figsize[1]))
    fig.suptitle('Spectogram')
    label= ["Power/Frequency"]
    for i, axs in enumerate(axs.flatten()):
        d, f, t, im = axs.specgram(data[:,i],NFFT=nfft,Fs=fs,noverlap=nOverlap)
        axs.set_title(titles[i])
        axs.set_ylim(0,50)
        axs.set(xlabel='Time (s)', ylabel='Frequency (Hz)')
        axs.label_outer()
        axs
    fig.colorbar(im, ax=axs, shrink=0.9, aspect=10)


def normalityTest(data):
    #   Inputs  :   difference between data from two timepoints 
    #   Output  :   result of normality test (p-value test)
    #           :   choice of technique for significance testing

    print ("Executing Shapiro Wilks Test...")

    if shapiro(data)[1] > 0.05:
        pVal = shapiro(data)[1]
        print ("Shapiro Wilks Test: data is normally distributed, P-Value=", pVal)
        print("Confirm Shapiro Wilks Test normality result with D’Agostino’s K^2 test")
        print ("Executing D’Agostino’s K^2 Test...")
        if stats.normaltest(data)[1] > 0.05:
            pVal = stats.normaltest(data)[1]
            print ("D’Agostino’s K^2 Test: data is normally distributed, P-Value=", pVal)
            print("Confirm D’Agostino’s K^2 Test normality result with Anderson-Darling Test")
            print ("Executing Anderson-Darling Test...")
            result = anderson(data)
            print('Statistic: %.3f' % result.statistic)
            p = 0
            for i in range(len(result.critical_values)):
                sl, cv = result.significance_level[i], result.critical_values[i]
                if result.statistic < result.critical_values[i]:
                    print('%.3f: %.3f, Anderson-Darling Test: data is normally distributed' % (sl, cv))
        print ("Utilize Paired T-test to evaluate significance of data")        

    if shapiro(data)[1] <= 0.05:
        pVal = shapiro(data)[1]
        print ("Shapiro Wilks Test: data is not normally distributed, P-Value=", pVal)
        print("Confirm Shapiro Wilks Test non-normality result with D’Agostino’s K^2 test")
        print ("Executing D’Agostino’s K^2 Test...")
        if stats.normaltest(data)[1] < 0.05:
            pVal = stats.normaltest(data)[1]
            print ("D’Agostino’s K^2 Test: data is not normally distributed, P-Value=", pVal)
            print("Confirm D’Agostino’s K^2 Test non-normality result with Anderson-Darling Test")
            print ("Executing Anderson-Darling Test...")
            result = anderson(data)
            print('Statistic: %.3f' % result.statistic)
            p = 0
            for i in range(len(result.critical_values)):
                sl, cv = result.significance_level[i], result.critical_values[i]
                if result.statistic > result.critical_values[i]:
                    print('%.3f: %.3f, Anderson-Darling Test: data is not normally distributed' % (sl, cv))
        print ("Utilize non parametric methods e.g., Wilcoxon Signed Test etc., to evaluate significance of data")
    pass


def wilcoxonTest(data_1,data_2,show_output,variableName,channelName,alpha=0.05):
    #   Inputs  :       data_1   - 2D numpy array (d0 = samples, d1 = channels) of filtered EEG data
    #                   data_2   - 2D numpy array (d0 = samples, d1 = channels) of filtered EEG data
    #   Output  :       2D array (d0 = samples, d1 = channels) of paired t-test results
    #   wilcoxon Test:  P < 0.05 : significance difference exists
    #                   P > 0.05 : no significance difference exists
    #   SD           :  Signficant difference between the two groups

    def initializeTest(data_1,data_2,variableName,channelName):
        stat_test_1 = (wilcoxon(data_1,data_2))[1]
        if show_output==True:
            if stat_test_1 < alpha:
                if np.mean(data_1)-np.mean(data_2)<0:
                    print("{}: SD (increase) exists at {}, P-value = {}".format(variableName,channelName,round(stat_test_1,5)))
                elif np.mean(data_1)-np.mean(data_2)>0:
                    print("{}: SD (decrease) exists at {}, P-value = {}".format(variableName,channelName,round(stat_test_1,5)))
            else:
                print("{}: SD does not exists at {}, P-value = {}".format(variableName,channelName,round(stat_test_1,5)))
        else:
            return stat_test_1
        return stat_test_1

    stat_test_3 = []
    for i in range(len(data_1.T)):
        stat_test_2 = initializeTest(data_1[:,i],data_2[:,i],variableName,channelName[i])
        stat_test_3.append(stat_test_2)
    stat_test_3 = np.array(stat_test_3).T

    return stat_test_3


