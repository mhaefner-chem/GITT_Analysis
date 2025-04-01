# -*- coding: utf-8 -*-
'''
Created on Sat Feb  8 15:51:35 2025

@author: mhaefner-chem
'''

# INPUT

'''
function reads in the GITT data from a given file
Format: 
    dictionary 'data', keys from list ['time','volt','cap','spec_cap']
    time (continuous measurement time) and volt (measured voltage) are required
    either cap (capacity) or spec_cap (special capacity) are requied
    
    datapoints are stored in lists:
    data[key] = []
'''
def get_GITT_data(file):
    
    data = {}    
    labels = []    
    splitter = ' '
    
    with open(file,mode='r') as f:
        lines = f.readlines()
        if ',' in lines[0]:
            splitter = ','
        elif '\t' in lines[0]:
            splitter = '\t'
        else:
            splitter = ' '
            
        required = ['time','volt','cap','spec_cap']
            
        for line_index, line in enumerate(lines):
            if line_index == 0:
                for item in line.split(splitter):
                    item = item.split('\n')[0]
                    label = item
                    if item in ['Test Time (s)','time/s','Time (s)']:
                        label = 'time'
                    elif item in ['Voltage (V)','Ewe/V']:
                        label = 'volt'
                    elif item in ['Capacity (mAh)','Capacity/mA.h','Capacity/mAh']:
                        label = 'cap'
                    elif item in ['Specific Capacity (mAh/g)','SpecificCapacity/mA.h/g']:
                        label = 'spec_cap'
                        
                    data[label] = []
                    labels.append(label)
            else:
                for item_index, item in enumerate(line.split(splitter)):
                    if labels[item_index] in required:
                        try:
                            float(item)
                        except:
                            messagebox.showerror('Faulty GITT data', 'GITT data contains non-numerical values. Please check the input file.')
                            return 0
                        else:
                            data[labels[item_index]].append(float(item))
                                
                    
    for label in ['time','volt']:
        if not label in data.keys():
            messagebox.showerror('GITT data incomplete', 'The GITT data needs to contain at least a column labeled \'time/s\' and a column labeled \'Ewe/V\'.')
            return 0

    return data

# OUTPUT

'''
This function writes the GITT settings to an .info-file in plain text format associated to the 
filename of the input raw data file. That allows the program to keep the settings between closing
and reopening.
'''
def write_GITT_settings(settings_file, settings):
    
    number_settings = ['theocap','m_AM/A','M_AM','rho','c0','A','scale','limiter']
    with open(settings_file, mode='w') as f:
        for item in number_settings:                      
            value = settings[item].entry.get()
            f.write('{} {}\n'.format(item,value))
            
'''
This function writes an example file with mock GITT data.
'''
def write_GITT_example():
    import numpy as np
    
    volt_init = 2
    
    t_all = list(np.linspace(0,540,10))
    volt_all = [2]*10
    cap_all = [0]*10
    
    def jump(t_in,volt_in,cap_in,charge):
        t_out = np.linspace(0,8100,136)
        volt_out = []
        cap_out = []
        
        for t in t_out:
            if t < 900:
                volt_out.append((np.sqrt(t)/300 + 0.1)*charge + volt_in)
                cap_out.append(cap_in + t/4500)
            else:
                volt_out.append((np.exp(-(t-900)/900)/20 + 0.05)*charge + volt_in)
                cap_out.append(cap_out[-1])
                
        for i in range(len(t_out)):
            t_out[i] = t_out[i] + t_in
        return t_out, volt_out, cap_out
    
    t_jump, volt_jump, cap_jump = jump(t_all[-1], volt_init, cap_all[-1], 1)
    for i, t in enumerate(t_jump):
        t_all.append(t)
        volt_all.append(volt_jump[i])
        cap_all.append(cap_jump[i])
    
    for i in range(12):
        t_jump, volt_jump, cap_jump = jump(t_all[-1], volt_all[-1], cap_all[-1], 1)
        for i, t in enumerate(t_jump):
            t_all.append(t)
            volt_all.append(volt_jump[i])
            cap_all.append(cap_jump[i])
        
    cap_all[-1] = 0
            
    for i in range(12):
        t_jump, volt_jump, cap_jump = jump(t_all[-1], volt_all[-1], cap_all[-1], -1)
        for i, t in enumerate(t_jump):
            t_all.append(t)
            volt_all.append(volt_jump[i])
            cap_all.append(cap_jump[i])
    
    Files = [('TXT File', '*.txt'),
        ('All Files', '*.*')]
    savefile = fd.asksaveasfile(filetypes = Files, defaultextension = Files)
    
    with savefile as fw:
        fw.write('time/s\tEwe/V\tCapacity/mA.h\n')
        for i, t in enumerate(t_all):
            fw.write('{:.8E}\t{:.8E}\t{:.8E}\n'.format(t,volt_all[i],cap_all[i]))

'''
this function saves the raw and processed GITT data into a OriginLab workbook,
carrying over the name of the original file as label
'''
def write_GITT_2_origin(data_raw,data_out,settings):
    import originpro as op
    book = op.new_book(lname=settings['name'])
    
    # worksheet for raw data
    wks_raw = book.add_sheet(name='raw_data')
    wks_raw.cols = 3
    
    wks_raw.from_list(0,data_raw['time'],lname='Time',units='s')
    wks_raw.from_list(1,data_raw['volt'],lname='Voltage',units='V')
    if settings['cap']:
        wks_raw.from_list(2,data_raw['cap'],lname='Capacity',units='mAh')
    elif settings['spec_cap']:
        wks_raw.from_list(2,data_raw['spec_cap'],lname='Specific Capacity',units='mAh/g')
    
    # worksheet for processed data
    wks_diff = book.add_sheet(name='diffusion_data')
    if settings['cap'] or settings['spec_cap']:
        wks_diff.cols = 6
    else:
        wks_diff.cols = 3
        
    wks_diff.from_list(0,data_out['time'],lname='Time',units='s')
    wks_diff.from_list(1,data_out['volt'],lname='Voltage',units='V')
    wks_diff.from_list(2,data_out['diff'],lname='Diffusion Coefficient',units='cm²/s')
    if settings['cap'] or settings['spec_cap']:
        wks_diff.from_list(3,data_out['spec_cap'],lname='Specific Capacity',units='mAh/g')
        wks_diff.from_list(4,data_out['ion'],lname='Content Conducting Ion',units='')
        
        half_cycle_label = []
        for value in data_out['cycle']:
            half_cycle_label.append(value + 1)
        
        wks_diff.from_list(5,half_cycle_label,lname='Half Cycle',units='',
                           comments='odd cycles: charge, even cycles: discharge')

'''
function outputs diffusion data
Format: 
    dictionary 'data_out', keys from list ['time','volt','spec_cap','cycle','diff']
    'time' is measurement time and 'volt' is measured voltage associated with diffusion rate 'diff'
    
    if capacity data is supplied, output also contains
    'spec_cap' (special capacity)
    'cycle' (current cycle, usually 0 is first charge, 1 is first discharge, 2 is second charge, etc.)
    
    datapoints are stored in lists:
    data_out[key] = []
'''
def write_GITT_data(savefile,data_out,settings):
    
    with savefile as f:
        if settings['cap'] or settings['spec_cap']:            
            f.write('{:16},{:16},{:16},{:16},{:16},{:16}\n'.format('time/s','volt/V','x_ion','SpecCap/mAh/g','D/cm^2/s','Cycle'))
            for i,value in enumerate(data_out['diff']):
                f.write('{:16.10e},{:16.10e},{:16.10e},{:16.10e},{:16.10e},{:4}\n'.format(data_out['time'][i],data_out['volt'][i],data_out['ion'][i],data_out['spec_cap'][i],data_out['diff'][i],data_out['cycle'][i]))
        else:
            f.write('{:16},{:16},{:16}\n'.format('time/s','volt/V','D/cm^2/s'))
            for i,value in enumerate(data_out['diff']):
                f.write('{:16.10e},{:16.10e},{:16.10e}\n'.format(data_out['time'][i],data_out['volt'][i],data_out['diff'][i]))


# METHODS
'''
function produces a numerical derivative of a given pair of x and y-values
slope at x determined with formula f(x+delta)-f(x-delta)/(2*delta)
'''
def get_numerical_derivative(x,y):
    
    derivative = []

    for i, value in enumerate(x):
        if i == 0:
            m = (y[i+1]-y[i])/(x[i+1]-x[i])
        elif i == len(x)-1:
            m = (y[i]-y[i-1])/(x[i]-x[i-1])
        else:
            m = (y[i+1]-y[i-1])/(x[i+1]-x[i-1])
        derivative.append(m)
        
    return derivative

'''
This function processes the raw GITT data
'''
def process_GITT(GITT_data,settings):
    import numpy as np
    from scipy.stats import linregress
    
    # initial data transformation, time as x-axis, voltage as y-axis
    x = GITT_data['time']
    y = GITT_data['volt']
    
    try:
        A = float(settings['A'].entry.get())
        m_AM = float(settings['m_AM/A'].entry.get())*A
        M = float(settings['M_AM'].entry.get())
        theocap = float(settings['theocap'].entry.get())
        c0 = float(settings['c0'].entry.get())
        scale = float(settings['scale'].entry.get())
        limiter = float(settings['limiter'].entry.get())
        rho = float(settings['rho'].entry.get())
    except:
        messagebox.error('Faulty Settings','The settings contain non-numerical data. Please check all settings and correct.')
        return 0,0
    
    # assigns capacity if it was provided
    # prefers special capacity over pure capacity, if both are provided
    settings['spec_cap'] = False
    settings['cap'] = False

    if 'spec_cap' in GITT_data:
        raw_spec_cap = GITT_data['spec_cap']
        settings['spec_cap'] = True
    elif 'cap' in GITT_data:
        x_cap = GITT_data['cap']
        settings['cap'] = True  
    
    # calculate specific capacity, current cycle, and ion content at every given time
    charge = True
    current_cycle = 0 # charge-discharge cycle number
    ref_cap = 0
    max_cap = 0
    x_ion = []
    x_spec_cap = []
    y_cycle = []    
    
    # this logic works with regular output from a BioLogic cycler
    # i.e., capacity is reset to 0 for every new charge or discharge cycle
    # capacity only ever rises and never decreases
    if settings['cap']:
        for i, cap in enumerate(x_cap):    
            y_cycle.append(current_cycle)
            if i > 1 and x_cap[i]-x_cap[i-1] < 0:
                current_cycle += 1
                if charge:
                    charge = False
                    ref_cap = ref_cap+x_cap[i-1]
                else:
                    charge = True
                    ref_cap = ref_cap-x_cap[i-1]
            if charge == True:
                spec_cap = (ref_cap+cap)/m_AM
            else:
                spec_cap = (ref_cap-cap)/m_AM
            x_spec_cap.append(spec_cap)
            x_ion.append(-spec_cap/theocap + c0)
            
    elif settings['spec_cap']:
        charge = True

        for i in range(len(raw_spec_cap)):
            y_cycle.append(current_cycle)
            if i > 1:
                if raw_spec_cap[i] > max_cap:
                    max_cap = raw_spec_cap[i]
                    
                if raw_spec_cap[i] > 1E-4 and raw_spec_cap[i] < 1E-4*max_cap:
                    current_cycle += 1
                    if charge:
                        charge = False
                        ref_cap = ref_cap+max_cap  
                    else:
                        charge = True
                        ref_cap = ref_cap-max_cap
                    max_cap = 0
                    
                if charge == True:
                    spec_cap = (ref_cap+raw_spec_cap[i])
                else:
                    spec_cap = (ref_cap-raw_spec_cap[i])
                    
                x_spec_cap.append(spec_cap)
                x_ion.append(-spec_cap/theocap + c0)

    # get numerical derivative of voltage
    # cutoff determines minimum jump in derivative required for it to be counted
    y_deriv = get_numerical_derivative(x, y)
    y_deriv_cutoff = limiter*np.mean(list(map(abs, y_deriv)))

    # this part detects when the current is applied and removed
    # makes this less dependent on format of GITT data
    current_on = []
    current_off = []
    on_times = []
    off_times = []
    load = False
    bad_fit = 0
    for i, value in enumerate(y_deriv):
        # detects positive derivative jump
        if y_deriv[i] > abs(scale*y_deriv[i-1]) and y_deriv[i] > y_deriv_cutoff and load == False:
            # switches meaning of jump depending of whether the cell is currently being charged or discharged
            if len(current_on) == 0 or y[current_on[-1]] < y[i]:
                current_on.append(i)
                on_times.append(x[i])
            else:
               current_off.append(i)
               off_times.append(x[i])
            load = True
        # detects negative derivative jump, same logic as for positive derivative jump but flipped
        elif y_deriv[i] < -abs(scale*y_deriv[i-1]) and y_deriv[i] < -y_deriv_cutoff and load == True:
            if len(current_on) == 0 or y[current_on[-1]] < y[i]:
                current_off.append(i)
                off_times.append(x[i])
            else:
               current_on.append(i)
               on_times.append(x[i])
            load = False
    
    # evaluate E1-E4, charging time tau
    D_out = {
        'ion':      [],
        'spec_cap': [],
        'cycle':    [],
        'time':     [],
        'volt':     [],
        'diff':     []
        }
    GITT_refined = []
    
    V_mol = M/rho
    off = 0
    for i, on in enumerate(current_on):    
        # determines the next point after on at which current is turned off
        for off in current_off:
            if off > on:
                break
        
        # determination of E1, E3, and tau
        E1 = y[on]
        E3 = y[off]
        tau = x[off]-x[on]
        
        # E4 requires logic to properly treat final titration
        if i < len(current_on)-1:
            E4 = y[current_on[i+1]]
        else:
            E4 = y[-1]
            
        # E2 requires linear regression for sqrt-behavior while current is applied
        interval_x = []
        interval_y = []
        for j in range(on+int((on-off)/2),off):
            interval_x.append(np.sqrt(x[j]))
            interval_y.append(y[j])
        try:
            regress_param = linregress(interval_x,interval_y)
        except:
            continue
        m = [regress_param.slope,regress_param.stderr]
        b = [regress_param.intercept,regress_param.intercept_stderr]
        
        E2 = m[0]*np.sqrt(x[on]) + b[0]
        
        if regress_param.rvalue**2 < 0.4:
            bad_fit += 1
        
        GITT_refined.append((E1,E2,E3,E4,tau,x[on],x[on],x[off],regress_param.rvalue**2)) # required for plotting
        
        # collect data for output
        if settings['cap'] or settings['spec_cap']:
            # the +1 is a fix to properly process Arbin data
            D_out['ion'].append(x_ion[current_on[i]+1])
            D_out['spec_cap'].append(x_spec_cap[current_on[i]+1])
            D_out['cycle'].append(y_cycle[current_on[i]+1])   
        D_out['time'].append(x[current_on[i]])
        D_out['volt'].append(y[current_on[i]])
        
        # calculation of the diffusion constants
        dE_s = E4-E1
        dE_t = E3-E2
        D = 4/(np.pi*tau) * (m_AM * V_mol/(M*A))**2 * ((dE_s)/(dE_t))**2
        D_out['diff'].append(D) 
    
    # check whether there is issues with the titration lengths
    def evaluate_tau(taus):
        
        buckets = [0,0,0]
        tot_length = [0,0,0]
        n_taus = len(taus)
        median = np.median(taus)
        
        for tau in taus:
            if tau > 0.95*median and tau < 1.05*median:
                buckets[1] += 1
                tot_length[1] += tau
            elif tau > 1.05*median:   
                buckets[2] += 1
                tot_length[2] += tau
            elif tau < 0.95*median:
                buckets[0] += 1
                tot_length[0] += tau
        
        if tot_length[2] > tot_length[1] or buckets[2] > 0.01*buckets[1]:
            messagebox.showwarning('Check Results','A significant number of abnormally long titration cycles was obtained, indicating that the program failed to correctly identify all titration cycles. Please reduce the settings \'scale\' and \'limiter\'.')

    evaluate_tau(list(zip(*GITT_refined))[4])
    
    if bad_fit > 0:
        messagebox.showinfo('Check Results','The regression for determining the onset energy yielded a bad fit {} times. Please check the results for errors and outliers.'.format(bad_fit))

    return D_out, GITT_refined

# GUI

'''
Function for plotting results from analyzed GITT data
messy code, refactoring not yet planned
'''
class plot_window:
    # initializes the window and default plotting data
    def __init__(self,GITT_data,GITT_refined,D_out,settings):
        
        self.root = create_window('1000x700+120+120', 'V-t and D-t plot')
    
        self.data = GITT_data
        self.refined = GITT_refined
        self.D = D_out
        self.settings = settings
        self.dpi_default = 100
        self.dpi_set = str(self.dpi_default)
        self.draw_window()
        
    # populates the window with widgets
    def draw_window(self):
        self.plot_form_factors()
    
    # creates the plot with matplotlib
    def plot_form_factors(self): 
        
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,  
        NavigationToolbar2Tk)
        
        fs = 16
        
        fig = plt.figure(figsize=(3,3), dpi=80)
        ax = fig.add_subplot()
        
        colors = ['green','blue','red']
        alphas = [1.0,1.0,1.0]
        labels = ['E1','E2','E3']
        props = dict(boxstyle='round', facecolor='white', alpha=0.5)
        for i in range(3):
            tmp = [[],[]]
            for result in self.refined:
                tmp[0].append(result[i+5])
                tmp[1].append(result[i])
                if i == 1:
                    ax.text(result[i+5],result[i],'R²:{:.3f}'.format(result[-1]),bbox=props)
                    
            ax.scatter(tmp[0],tmp[1],marker='x',color=colors[i],zorder=50,label=labels[i],alpha=alphas[i])
            
        ax.plot(self.data['time'],self.data['volt'],linestyle='-',label='E',marker='x')
        plt.xticks(fontsize=fs)
        plt.yticks(fontsize=fs)
        
        ax2 = ax.twinx()
        ax2.scatter(self.D['time'],self.D['diff'],color='black',marker='+',label='D')
        
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax2.legend(h1+h2, l1+l2,loc=1,fontsize=fs)
        
        ax2.set_yscale('log')
        ylim2_max = max(self.D['diff'])*5
        ylim2_min = min(self.D['diff'])/5
        ax2.set_ylim(ylim2_min,ylim2_max)
        plt.yticks(fontsize=fs)
        
        ax.grid(zorder=-50,linestyle='--',alpha=0.66)
        ax.set_xlabel('Time t ($10^6$ s)',fontsize=fs) 
        ax.set_ylabel('Voltage E (V)',fontsize=fs)  
        ax2.set_ylabel('Diffusion rate D ($10^{-9}$ cm²/s)',fontsize=fs) 
        ax.set_title('GITT Plot\nDiffusion and Voltage against Time',fontsize=fs+4)
    
        # creates and places Tkinter canvas for the matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master = self.root)   
        canvas.draw() 
        canvas.get_tk_widget().pack(side=tk.TOP,fill='both',expand=False)
        
        # creates the matplotlib default toolbar 
        toolbar = NavigationToolbar2Tk(canvas, self.root) 
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP,fill='both',expand=True) 
      
'''
Function to streamline the creation of the labeled entries
'''
class labeled_entry:
     
     def __init__(self, parent_frame, pos, label, init_value):
         
         self._frame = tk.Frame(parent_frame)
         self._frame.grid(row=pos,column=0)
         
         self._label = ttk.Label(self._frame,width=8)
         self._label['text'] = label[0]
         self._label.grid(row=0,column=0)
         
         self._altlabel = ttk.Label(self._frame,width=8)
         self._altlabel['text'] = ' '+label[1]
         self._altlabel.grid(row=0,column=2)
         
         self.value = tk.StringVar()
         self.entry = ttk.Entry(
             self._frame,
             textvariable=self.value,
             width=12,
             justify='right'
         )
         self.entry.insert(0, init_value)

         self.entry.grid(row=0,column=1) 

'''
Creates the main window for loading and saving data
'''
class main_window:
    
    # initializes the base window
    def __init__(self):
        
        self.version = '0.7.1'
        self.icon = ''
        
        self.raw_file = None
        self.raw_filename = ''
        self.GITT_data = 0
        self.D_data = 0
                
        self.settings = {}
        
        self.root = create_window('400x500+120+120','GITT Analysis')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.frame_buttons()
        self.frame_entry_fields()
        
        self.root.mainloop()
  
    '''
    This frame contains all entry fields for the settings
    '''
    def frame_entry_fields(self):
        
        self.frame_entry_fields = tk.Frame(self.root)
        self.frame_entry_fields.grid(row=1,column=0)
        self.frame_entry_fields.columnconfigure(0, weight=1)
        
        self.entries_title = tk.Label(self.frame_entry_fields,
                                      text = 'Properties Active Material (AM)'
                                      )
        self.entries_title.grid(row=0,column=0)
        
        self.settings['m_AM/A'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 1, 
            label = ['m/A','g/cm²'], 
            init_value = 1)
        
        self.settings['M_AM'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 2, 
            label = ['M','g/mol'], 
            init_value = 13)
        
        self.settings['rho'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 3, 
            label = ['ρ','g/cm³'], 
            init_value = 55)
        
        self.settings['theocap'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 4, 
            label = ['ref cap.','mAh/g'], 
            init_value = 100)
        
        self.settings['c0'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 5, 
            label = ['c_0 (ion)',''], 
            init_value = 1.0)
        
        self.entries_title = tk.Label(self.frame_entry_fields,
                                      text = 'Properties Measurement')
        self.entries_title.grid(row=6,column=0)
        
        self.settings['A'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 7, 
            label = ['A_cont','cm²'], 
            init_value = 1.25)
        
        self.entries_title = tk.Label(self.frame_entry_fields,
                                      text = 'Settings Analysis')
        self.entries_title.grid(row=8,column=0)
        
        self.settings['scale'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 9, 
            label = ['scale',''], 
            init_value = 1)
        
        self.settings['limiter'] = labeled_entry(
            self.frame_entry_fields, 
            pos = 10, 
            label = ['limiter',''], 
            init_value = 0.01)
        
    '''
    This frame handles all relevant buttons.
    '''
    def frame_buttons(self):

        '''
        This is the top row of buttons.
        '''
        def top_buttons(self):
            columns = 3
            
            self.frame_top_buttons = tk.Frame(self.root)
            self.frame_top_buttons.grid(row=0,column=0,sticky='NSEW')
            for i in range(columns):
                self.frame_top_buttons.columnconfigure(i, weight=1)
            
            sep_top = ttk.Separator(self.frame_top_buttons,orient='horizontal')
            sep_top.grid(row=0,column=0,columnspan=columns,sticky='EW')
            
            _button_get_GITT_raw = ttk.Button(self.frame_top_buttons,
                                              text = 'Open File',
                                              command = lambda : get_GITT_raw())
            _button_get_GITT_raw.grid(row=1,column=0,sticky='NS')
            
            _button_process_GITT = ttk.Button(self.frame_top_buttons,
                                              text = 'Run Analysis',
                                              command = lambda : try_process_GITT())
            _button_process_GITT.grid(row=1,column=1,sticky='NS')
            
            _button_save_GITT = ttk.Button(self.frame_top_buttons,
                                           text = 'Save File',
                                           command = lambda : save_GITT())
            _button_save_GITT.grid(row=1,column=2,sticky='NS')
            
            sep_top2 = ttk.Separator(self.frame_top_buttons,orient='horizontal')
            sep_top2.grid(row=3,column=0,columnspan=columns,sticky='EW')
            
            label_GITT_file = tk.Text(self.frame_top_buttons,
                                          height=3)
            if self.GITT_data == 0:
                label_GITT_file.insert(tk.END,'No raw GITT data loaded.')
            else:
                label_GITT_file.insert(tk.END,self.raw_filename)
            if self.D_data != 0:
                label_GITT_file.insert(tk.END,'\nData processed!')
            
            label_GITT_file.grid(row=2,column=0,columnspan=3,pady=10)
        
        '''
        This is the bottom row of buttons.
        '''
        def bottom_buttons(self):
        
            columns = 2
            self.frame_bottom_buttons = tk.Frame(self.root)
            self.frame_bottom_buttons.grid(row=2,column=0,sticky='EW')
            for i in range(columns):
                self.frame_bottom_buttons.columnconfigure(i, weight=1)
            
            sep_bottom = ttk.Separator(self.frame_bottom_buttons,orient='horizontal')
            sep_bottom.grid(row=1,column=0,columnspan=columns,sticky='EW')
    
            _button_help = ttk.Button(self.frame_bottom_buttons,
                                      text = 'Help',
                                      command = lambda : getting_help())
            _button_help.grid(row=2,column=0,sticky='S')
            
            _button_about = ttk.Button(self.frame_bottom_buttons,
                                       text = 'About',
                                       command = lambda : about())
            _button_about.grid(row=2,column=1,sticky='S') 
        
        '''
        This function retrieves the settings from an existing file.
        '''
        def fetch_GITT_settings():
            
            number_settings = ['theocap','m_AM/A','M_AM','rho','c0','A','scale','limiter']
            settings_file = self.raw_file.split('.')[0]+'.info'
            if os.path.isfile(settings_file):
                with open(settings_file, mode='r') as f:
                    for line in f.readlines():
                        for item in number_settings:
                            if line.split()[0] == item:
                                self.settings[item].entry.delete(0,tk.END)
                                self.settings[item].entry.insert(0, float(line.split()[1]))
        
        '''
        This function imports raw GITT data.
        '''
        def get_GITT_raw():
            filetypes = (
                ('data files', '*.csv;*.txt;*.dat'),
                ('All files', '*.*'))
            
            self.raw_file = fd.askopenfilename(
                title='Open GITT raw data file',
                initialdir='./',
                filetypes=filetypes)
            
            if os.path.isfile(self.raw_file) == True:
                self.GITT_data = get_GITT_data(self.raw_file)
                if self.GITT_data != 0:
                    self.raw_filename = 'GITT raw data loaded: '+self.raw_file
                    self.frame_top_buttons.destroy()
                    top_buttons(self)
                    fetch_GITT_settings()
                    self.settings['name'] = os.path.basename(self.raw_file.split('.')[0])                
            elif not self.raw_file == '':
                messagebox.showerror('No input file!', 'Input file could not be found!')
        
        '''
        This function processes raw GITT data. Depending on whether launched in an OriginLab
        environment or not, it either writes the results to an OriginLab workbook or
        plots the D-t and V-t diagram for checking the sensibility of the results
        '''
        def try_process_GITT():
            if self.GITT_data == 0:
                messagebox.showerror('No GITT data', 'No GITT data loaded!')
            else:
                self.D_data, GITT_extra = process_GITT(self.GITT_data,self.settings)
                self.frame_top_buttons.destroy()
                top_buttons(self)
                file = self.raw_file.split('.')[0]+'.info'
                write_GITT_settings(file, self.settings)
                try:
                    import originpro as op
                    op.org_ver()
                    write_GITT_2_origin(self.GITT_data,self.D_data,self.settings)
                except:
                    plot_window(self.GITT_data,GITT_extra,self.D_data,self.settings)
        
        '''
        This function handles GUI side of saving the processed GITT data.
        '''
        def save_GITT():
            if self.GITT_data == 0:
                messagebox.showerror('No GITT data', 'No GITT data loaded!')
                return
            elif self.D_data == 0:
                self.D_data, GITT_extra = process_GITT(self.GITT_data,self.settings)
                self.frame_top_buttons.destroy()
                top_buttons(self)
            
            Files = [('CSV File', '*.csv'),
                ('All Files', '*.*')]
            savefile = fd.asksaveasfile(filetypes = Files, defaultextension = Files)
            write_GITT_data(savefile,self.D_data,self.settings)
        
        '''
        This function handles the window containing an overview about the formatting of the raw GITT data input file and the meaning of the different required settings for processing.
        '''
        def getting_help():
            help_frame = create_window('850x550+120+120', 'Quick Tips',self.icon)
            help_frame.config(bg='#FFFFFF')
            message ='''Format raw data:
Natively works with standard output format from BioLogic cyclers. An example raw data file in that format can be generated with the button below. As alternative to tab stops, commas (regular CSV file formatting) or spaces can be used in the input file, e.g.,
0.0E+00 1.0E+00 1.5E+00
0.0E+00,1.0E+00,1.5E+00

Format capacity data:
If capacity should be considered in the analysis, it needs to be formatted such that every half cycle (charge and discharge) are treated separately, each beginning at capacity 0. Examplary behavior for a full cycle (charge and discharge) is simulated in an idealized fashion in the example raw data file.
Regular capacity is indicated by 'Capacity/mA.h' in the input file header,
specific capacity is indicated by 'SpecialCapacity/mA.h/g' in the input file header, e.g.,
Time/s,Ewe/V,Capacity/mA.h,SpecificCapacity/mA.h/g
0.0E+00,1.0E+00,1.5E+00,1.5E+01

Capacity data is not required for analysis. Only time and voltage are required.

Settings for analysis:
m/A
    area-normed mass of the active material in g/cm²
M
    molar mass of the active material in g/mol
ρ
    densitiy of the active material in g/cm³
A_cont
    contact area for measurement in cm²
    
With capacity data:
ref cap.
    specific capacity at ion content 1, e.g., Li1NiO2 or Na1CoO2
c_0
    actual starting ion content

Settings for pattern recognition:
scale (regular range: 1-3)
    decrease if not all titrations are detected
limiter (regular range: 0.02-0.05)
    decrease after scale until all titrations are detected
    adjust until the smoothest curve for diffusion coefficients is obtained
    
Processed data is saved in CSV format.
If program is run in OriginLab either via
    run -pyf GITT_analysis.py
or via the OPX file, the results are automatically filled into a new workbook upon analysis.
If program is run as standalone, results are automatically plotted upon analysis.
'''

            text_box = tk.Text(help_frame, wrap = 'word')
            text_box.pack(expand=False,fill=tk.X)
            text_box.insert('end', message)
            text_box.config(state='disabled')
            
            button_example = ttk.Button(help_frame,
                                        text = 'Make Example Input',
                                        command = lambda : write_GITT_example())
            button_example.pack(side=tk.BOTTOM,expand=False,fill=tk.X) 
        
        '''
        This function handles the window containing a short description, version, and license of the program.
        '''
        def about():
            about_frame = create_window('850x600+120+120', 'About BondFinder',self.icon)
            about_frame.config(bg='#FFFFFF')
            message ='''GITT_analysis, version {}
            
GITT_analysis analyzes raw GITT data to extract the diffusion coefficients of the conducting ion based on the mini-review 'Principle and Applications of Galvanostatic Intermittent Titration Technique for Lithium-ion Batteries' by Jaeyoung Kim, Sangbin Park, Sunhyun Hwang, and Won-Sub Yoon. (DOI: https://doi.org/10.33961/jecst.2021.00836) and equation 16, in particular.

MIT License
Copyright (c) 2025 mhaefner-chem
Contact: michael.haefner@uni-bayreuth.de

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''.format(self.version)

            text_box = tk.Text(about_frame, wrap = 'word', height=50)
            text_box.pack(expand=True,fill=tk.X)
            text_box.insert('end', message)
            text_box.config(state='disabled')
    
        top_buttons(self)
        bottom_buttons(self)

'''
function that creates a new window
'''
def create_window(dimensions='500x350+100+100', title = 'You should not be reading this', icon = ''):
   
    w = int(dimensions.split('x')[0])
    h = dimensions.split('x')[1]
    h = int(h.split('+')[0])
    
    offset_x = int(dimensions.split('+')[1])
    offset_y = int(dimensions.split('+')[2])
    
    # initializes the Tk root window
    window = tk.Tk()
    
    # gets screen properties and centers in upper third
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    offset_x = int(screen_width/3 - w / 3)
    offset_y = int(screen_height/3 - h / 3)
    
    # makes sure the window stays within bounds
    actual_wxh, actual_offsets = window_size_limiter([screen_width,screen_height],[w,h], [offset_x,offset_y])
    
    # set a title
    window.title(title)
    
    # specify geometry and max and min measurements
    window.geometry(f'{actual_wxh[0]}x{actual_wxh[1]}+{actual_offsets[0]}+{actual_offsets[1]}')
    window.minsize(10,10)
    window.maxsize(screen_width,screen_height)
    if icon != '':
        window.iconbitmap(icon)
    
    return window

'''
function that ensures that the created windows do not become bigger than the screen
'''
def window_size_limiter(avail_wxh,req_wxh,req_offset_xy):

    actual_wxh = [0,0]
    actual_offsets = [0,0]
    
    # check whether window fits on the current screen with and without offsets
    for i in range(len(avail_wxh)):
        if req_wxh[i] > avail_wxh[i]:
            actual_wxh[i] = avail_wxh[i]
        elif req_wxh[i] + req_offset_xy[i] > avail_wxh[i]:
            actual_wxh[i] = req_wxh[i]
            actual_offsets[i] = avail_wxh[i] - req_wxh[i]
        else:
            actual_wxh[i] = req_wxh[i]
            actual_offsets[i] = req_offset_xy[i]
    
    return actual_wxh,actual_offsets

if __name__ == '__main__':
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog as fd
    from tkinter import messagebox
    import os
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    
    plt.close('all')
    mpl.use('pgf')
    mpl.use('pdf')
    mpl.use('ps')
    mpl.use('svg')
    
    main = main_window()