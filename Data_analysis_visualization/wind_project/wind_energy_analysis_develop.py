
# coding: utf-8

# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"></ul></div>

# In[27]:


import os, re, csv, os
import random
from glob import glob
from datetime import date, datetime, timedelta
import webcolors
import numpy as np
import pandas as pd
from plotly.offline import iplot, plot
import plotly.graph_objs as go
import plotly.tools as tls
import cufflinks as cf
cf.go_offline()


# In[28]:


def get_file(template):
    # glob function creates a list of files appropriate with template
    filenames = glob(template)
    if not filenames:
        raise Exception(f'There are no files for given month or year in /Data/wind_ready/ folder')
    assert len(filenames) == 1
    f'There are more than one files for given month in /Data/wind_ready/ folder!'
    return filenames[0]

def get_raw_filename(year, month):
    return get_file(f'./Data/wind_csv/{year}/PL_GEN_WIATR_{year}{month:02}*.csv')

def get_raw_files_list(year):
    """
    Return: 2 lists: first one for downloaded from PSE webpage files, second one for numbers of months appropriate
    files. When there are no files downloaded or duplicates - error messages are generated.
    """
    raw_files = []
    month_numbers = []
    for month_num in range(1, 13):
        try:
            file = get_raw_filename(year, month_num)
            raw_files.append(file)
            month_numbers.append(month_num)
        except:
            continue
    return raw_files, month_numbers

def transformed_filename(year, month):
    if not os.path.exists(f'./Data/wind_ready/{year}/'):
        os.makedirs(f'./Data/wind_ready/{year}')   
    return f'./Data/wind_ready/{year}/{year}{month:02}.csv'


def get_transformed_filename(year, month):
    return get_file(transformed_filename(year, month))


def files_list(year):
    """
    Return: List of transformed 'csv' files for given year or error message on the lacking(or duplicated) data
    """
    ready_list = sorted(glob(f'./Data/wind_ready/{year}/*.csv'))
    if  len(ready_list) == 0:
        raw_files = get_raw_files_list(year)[0]
        if len(raw_files) > 0:
            for month in range(1, 13):
                try:
                    if os.path.exists(get_raw_filename(year, month)):
                        save_clean_data(year, month)
                except AssertionError:
                    continue
            ready_list = sorted(glob(f'./Data/wind_ready/{year}/*.csv'))
        else:
            raise Exception(f'There is no data for {year} year. You should try to download it from PSE webpage.')
    return ready_list                


# In[29]:


def save_clean_data(year, month_num):
    df = pd.read_csv(get_raw_filename(year, month_num),
                     encoding='iso 8859-1',
                     sep=';',
                     skiprows=[0],
                     usecols=[0, 1, 2],
                     names=['Date', 'Time', 'Total_Wind_Power(MWh)'],
                     index_col='Date',
                    converters={1: lambda x:x.replace('24', '0').replace('2A', '2'),
                               2: lambda x:x.replace(',', '.')})
    #df['Time'].astype('str', inplace=True)
    df.to_csv(transformed_filename(year, month_num), header=True)
    
def get_clean_data(year, month):
    if not os.path.exists(f'./Data/wind_ready/{year}/{year}{month}.csv'):
        save_clean_data(year, month)
    return pd.read_csv(get_transformed_filename(year, month))


# In[30]:


def wind_hourly(year, month_num):
    """
    Input: function takes the year and the number of month in range between 1 and number of months for given year 
    Return: dataframe either for month's wind power generation or for all months - to use for visualization, analysis,
    modelling.
    """
    raw_files_list = get_raw_files_list(year)[1]
    # preparing dataframe either for all months in year or for only one month
    if month_num > len(raw_files_list):
        df_all = [get_clean_data(year, month_num) for month_num in raw_files_list]
        df = pd.concat(df_all)
    else:
        df = get_clean_data(year, month_num)
    
    df['Date'] = pd.to_datetime(df['Date'].astype('str'))
    df.set_index('Date', inplace=True)
    return df


# In[31]:


def wind_daily(year, month_num):
    """
    Return: dataframe of wind generation where indexing is by day values not by hours
    """
    # resampled data from hours to days
    df_days = wind_hourly(year, month_num).resample('D').sum().iloc[:,[1]]
    df_days.rename(columns={'Total_Wind_Power(MWh)':'Wind_Daily(MWh)'}, inplace=True)
    
    return df_days


# In[32]:


def month_name(month_num):
    """
    Function month_name() returns name of month  to use it in formatting strings for plotting labels. 
    """
    return date(1990, int(month_num), 1).strftime('%B')

def month_names(months):
    return [month_name(month_num) for month_num in range(1, months)]

def years_list():
    y_list = os.listdir('./Data/wind_csv')
    if y_list[0] == 'ipynb':
        return y_list[1:]
    else:
        return y_list
    


# In[33]:


def get_random_colors():
    colors = webcolors.CSS3_HEX_TO_NAMES
    aborted_colors = ['white','mintcream','snow','lightyellow','whitesmoke','linen','beige','seashell',
                     'floralwhite','oldlace','lavenderblush','ivory','ghostwhite','mediumslateblue',
                     'aliceblue','lightgoldenrodyellow','honeydew','azure','cornsilk','black']
    palette = [colors[key] for key in colors]
    random.shuffle(palette)
    chosen_palette = [palette[i] for i in range(16) if palette[i] not in aborted_colors]
    return chosen_palette


# In[34]:


def leap_years(year, months):
    """
    Return: cumulative data for year with 366 days where 29th of February value is summed
    wiht the value of 28th and next the row for 29th is dropped from the dataframe.
    """
    df_days = wind_hourly(year, months).resample('D').sum().iloc[:,[1]]
    df_days.rename(columns={'Total_Wind_Power(MWh)':'Wind_Daily(MWh)'}, inplace=True)
    df_days.iloc[58] = df_days.iloc[58,0] + df_days.iloc[59,0]
    df_days.drop(df_days.index[59], inplace=True)
    return df_days.cumsum()/10**6


# In[35]:


def current_year(year, months):
    """
    Return: cumulative data for all passed months of the year but for 0 values for days of future
    months - it plots the data only for passed months.
    """
    wind_grow_ = wind_daily(year, months)
    last_date = wind_grow_.index[-1]
    last_day_of_year = datetime(int(year), 12, 31)
    no_data_days = (last_day_of_year - last_date).days
    no_data_range = pd.date_range(last_date+timedelta(days=1), last_date + timedelta(no_data_days), freq='D')
    data_vals = np.array([0]*no_data_days)
    df = pd.DataFrame({'Date': no_data_range, 'Wind_Daily(MWh)': data_vals})
    df.set_index('Date', inplace=True)
    frames = [wind_grow_, df]
    return wind_grow_.append(df)

Graphs presented below use 2 methods of plotting available in Plotly library - the main reason is a learning aspect.
"""
Names for graphs functions:
      wind_1 - daily wind generation for month
      wind_1a - daily generation for month plotted in deafult web browser
      wind_2 - daily wind generation for year
      wind_3 - monthly wind generation for year
      wind_4 - growth of generation (cumulative) - line or bar - for given year
      wind_4a - cumulative growth of generation for given year
      wind_4b - cumulative growth of generation for all years
      wind_4c - total yearly power generation
      wind_5 - average hour generation for year
      wind_6 - hour wind generation for each month
"""
Colors of graphs both for months and years are randomly chosen due to get_random_colors() (possible change)
# In[36]:


def wind_1(year, month_number=None):
    """
    Input: number of month in range of 1-12 (or number for passed months of present year), by default it is
    random chosen month when function is being called without argument.
    Return: graph presenting daily total wind generation in Poland for given or random chosen month. 
    """
    try:
        if str(year) not in years_list():
            raise Exception
    except Exception:
        print(f"No data for given {year} year.")
        return
    
    if month_number:
        month_number = month_number
    else:
        month_number = random.randint(1, len(files_list(year)))
    
    wind_m = wind_daily(year, month_number)/10**3
    if month_number > len(files_list(year)):
        month = 'until last month part'
    else:
        month = month_name(month_number)
    w_avg = wind_m.iloc[:, 0].mean()
    # preparing plots with plotly + cufflinks
    wind_m.iplot(kind='bar',
                dimensions=[900,450],
                annotations=[dict(
                                x=wind_m.index[-5],
                                y=w_avg,
                                text='Average Power=' + str(round(w_avg, 1)) + ' GWh',
                                textangle=0,
                                showarror=True,
                                arrowhead=17,
                                ax=0,
                                ay=-40)],
                hline=dict(y=wind_m.iloc[:, 0].mean(), color='red', dash='dash'),
                xTitle='Days',
                yTitle='Total Power (GWh)',
                colors=random.choice(get_random_colors()),
                title='Generation of Wind Power for {} of {}'.format(month, year))


# In[37]:


def wind_1a(year, month_number=None):
    """
    Input: number of month in range of 1-12 (or number for passed months of present year), by default it is
    random chosen month when function is being called without argument.
    Return: graph plotted in web browser, presenting daily wind generation in Poland for given or random chosen month. 
    """
    if month_number:
        month_number = month_number
    elif year == 2012:
        month_number = random.choice(get_raw_files_list(year)[1])
    else:
        month_number = random.randint(1, len(files_list(year)))
    
    wind_m = wind_daily(year, month_number)/10**3
    month = month_name(month_number)
    m_avg = wind_m.iloc[:,0].mean()
    
    data = [go.Bar(x=wind_m.index, y=wind_m['Wind_Daily(MWh)'].values, marker={'color':'orange'})]      
    layout = {'xaxis':{'title':'Days'}, 'yaxis':{'title':'Total Power (GWh)'},
             'shapes':[{'type':'line', 'x0':wind_m.index[0], 'x1':wind_m.index[-1], 'y0':m_avg, 'y1':m_avg,
                       'line':{'color':'green', 'width':2, 'dash':'longdash'}}],
              'annotations': [{'x': wind_m.index[-3], 'y': m_avg,
                        'text': 'Avg Power=' + str(round(m_avg, 1)) + ' MWh',
                             'showarrow':True, 'arrowhead':1, 'ax':0, 'ay':-30}],
              'autosize':True,
              'title':f'Generation of Wind Power in {month} of {year}'}
    plot(go.Figure(data=data, layout=layout))


# In[38]:


def wind_2(year):
    """
    Return: plot presenting wind power generation for each day of given year
    """
    # dataframe for full year generation(or all months of present year)
    months = len(files_list(year)) + 1
    wind_y = wind_daily(year, months)/10**3    # to get values in TeraWatt Hours
    # cufflinks style plot - because of interactivity no need to show all dates in x axis
    wind_y.iplot(kind='bar',
                 annotations = [dict(x=wind_y.index[-2],y=wind_y['Wind_Daily(MWh)'].mean(),
                                text='Average Power=' + str(round(wind_y.iloc[:,0].mean(), 1)) + ' GWh',
                               textangle=0, showarrow=True, arrowhead=17, ax=0, ay=-40)],
                 hline=dict(y=wind_y['Wind_Daily(MWh)'].mean(), color='red', dash='dash'),
                 legend='Wind_Daily(GWh)',
                 showlegend=False,
                 xTitle='Days', yTitle='Total Power(GWh)', colors='blue',
                 title="Generation of Wind Power in " + '{}'.format(year), theme='white',
                dimensions=[1000,500])


# In[39]:


def wind_3(year):
    """
    Return: plot presenting wind power generation for each month of given year
    """
    m_names = [month_name(month_num) for month_num in get_raw_files_list(year)[1]]
    months =len(m_names) + 1
    
    # dataframe resampled to months with index being months names
    wind_monthly = wind_daily(year, months).resample('M')
    wind_monthly = wind_monthly.sum().iloc[:,[0]]/10**3
    colors = random.choice(get_random_colors())
    data = [go.Bar(x=m_names, y=wind_monthly.iloc[:,0], marker=dict(color=colors), name='Power by Month')]
    layout = go.Layout(xaxis=dict(title='Months'), yaxis=dict(title='Total Power (GWh)'),
                       title="Monthly Wind Power Generation in {}".format(year),
                       height=400, width=800,
                       # showlegend=True)
                      )
    iplot(go.Figure(data=data, layout=layout));


# In[40]:


def wind_4(year,plot='line'):
    """
    Return: linear or bar graph for cumulative amount of wind energy generated from the beginning of the year
    (some differences in plotting methods - with cufflinks tools and without it).
    Bar chart is returned with any kind of argument put after year number( for example: (2019, 1) or (2018,'bar'))
    """
    months = len(files_list(year)) + 1
    wind_y = wind_daily(year, months)/10**3
    wind_grow = wind_y.cumsum()
    last_day = round(wind_grow.max()[0], 1) # total value for the last day of the plot
    if plot=='line':
        return wind_grow.iplot(kind='scatter',
                    width=2,
                    annotations=[dict(
                                x=wind_y.index[-1],
                                y=last_day,
                                text='Total=' + str(last_day) + ' GWh',
                                textangle=0,
                                showarror=True,
                                arrowhead=1,
                                ax=0,
                                ay=-20)],
                    xTitle='Days', yTitle='Total Power (GWh)', colors='green',
                    title=f"Wind Power Cumulation in {year}", theme='solar', dimensions=(800, 350))
    
        
    else:
        data = [go.Bar(x=wind_grow.index,
                           y=wind_grow['Wind_Daily(MWh)'],
                           name='Total=\n'+str(round(wind_grow.iloc[-1,0], 1)) + ' GWh')]
        layout = go.Layout(xaxis=dict(title='Days'), yaxis=dict(title='Total Power (GWh)'),
                           title="Growth of Wind Power Generation in {}".format(year),
                           height=450, width=900,
                           showlegend=True,
                           legend=dict(x=1.0, y=1.0))
        iplot(go.Figure(data=data, layout=layout))


# In[41]:


def wind_4a():
    """
    Return: Separate linear graphs for each year in data folder with cumulative amount of wind energy generated).
    """
    years = years_list()
    for year in years:
        months = len(files_list(year)) + 1
        wind_y = wind_daily(year, months)/10**3
        wind_grow = wind_y.cumsum()
        last_day = round(wind_grow.max()[0], 1) # total value for the last day of the plot
        
        wind_grow.iplot(kind='scatter',
                        width=2,
                        annotations=[dict(
                                    x=wind_y.index[-1],
                                    y=last_day,
                                    text='Total=' + str(last_day) + ' GWh',
                                    textangle=0,
                                    showarror=True,
                                    arrowhead=1,
                                    ax=0,
                                    ay=-20)],
                        xTitle='Days', yTitle='Total Power (GWh)', colors='green',
                        title=f"Wind Power Cumulation in {year}",
                        theme='solar', dimensions =(800, 350))


# In[42]:


def wind_4b():
    """
    Return: A single graph of number of plots for every year of wind generation's cumulative value
    """
    data = []
    years = years_list()
    cur_year = years[-1]
    # 2012 year moved to the end of list to facilitate plotting disturbed by the lack of data
    years.append(years.pop(0)) 
    for year in years:
        months = len(files_list(year)) + 1
        # preparing data for current year to facilitate correct plotting
        if year==cur_year and months != 13:
            wind_grow = current_year(year, months)
        else:
            wind_grow = wind_daily(year, months)            
        # code used for leap years(February with 29 days)
        if wind_grow.shape[0] == 366:
            wind_grow = leap_years(year, months)
        else:
            wind_grow = wind_grow.cumsum()/10**6
       
        wind_grow.rename(columns={'Wind_Daily(MWh)': year}, inplace=True)
        wind_grow.index = wind_grow.index.strftime('%d/%m')
        last_day = round(wind_grow.max()[0], 1)
        trace = go.Scatter(x=wind_grow.index, y=wind_grow[year].values,
                           name=f'Total for {year}: {last_day} TWh')
        data.append(trace)
        
    layout = {'xaxis':{'title':'Days of year'}, 'yaxis':{'title':'Total Power (TWh)'},
             'title':'Cumulative Wind Power Generation in Years',
             'width':900, 'height':550}
    iplot(go.Figure(data=data, layout=layout))


# In[43]:


def wind_4c():
    """
    Return: Total yearly production of wind energy in GWh.
    """
    years = years_list()
    data = []
    for year in years:
        months = len(files_list(year)) + 1
        wind_grow = (wind_daily(year, months)/10**6).resample('Y').sum()
        trace = go.Bar(x=wind_grow.index.strftime('%Y'), y=wind_grow['Wind_Daily(MWh)'], name=year)
        data.append(trace)
    layout = {'xaxis':{'title':'Years'}, 'yaxis':{'title':'Total Generation (TWh)'},
             'title':'Total Wind Power Generation in Years'}
    iplot(go.Figure(data=data, layout=layout))
    


# In[44]:


def wind_5(year):
    """
    Return: plot showing an average hour wind generation for given year
    """
    months = len(files_list(year)) + 1
    df = wind_hourly(year, months)
    
    h_wind = df.pivot_table(index='Date', columns='Time', values='Total_Wind_Power(MWh)').mean()
    hour_avg = h_wind.mean()
    
    data = [go.Bar(x=h_wind.index, y=h_wind.values)]
    layout = {'shapes': [{'type': 'line',
                        'x0': h_wind.index[0], 'y0': hour_avg, 'x1': len(h_wind.index), 'y1': hour_avg,
                        'line': {'color': 'red', 'width': 2, 'dash': 'longdash'}}],
            'showlegend':False,
            'annotations': [{'x': h_wind.index[-10], 'y': hour_avg,
                            'text': 'Avg Power=' + str(round(hour_avg, 1)) + ' MWh',
                             'showarrow':True, 'arrowhead':1, 'ax':0, 'ay':-30}],
            'xaxis': {'title': 'Hours'},
            'yaxis': {'title': 'Generation by Hour (MWh)'},
            'title':f"Averge Wind Generation per Hour in {year}",
            'width':800, 'height': 400}

    iplot(go.Figure(data=data, layout=layout))


# In[45]:


def wind_6(year):
    """
    Return: each month subplots for hour wind generation in given year
    """
    months = len(files_list(year))
    rows, cols = (4, 3)

    m_names = [month_name(m_num) for m_num in range(1, 13)]
    fig = tls.make_subplots(rows=rows, cols=cols,
                            shared_xaxes=True, shared_yaxes=True,
                            subplot_titles=m_names,
                            print_grid=False)
    row, col = 1, 0
    for month_num in get_raw_files_list(year)[1]:
        # month dataframe with energy values for each hour
        df = wind_hourly(year, month_num)
        h_wind = df.pivot_table(index='Date', columns='Time', values='Total_Wind_Power(MWh)').mean()
        # average value of wind energy for all day
        day_avg = h_wind.mean()
        m_name = month_name(month_num)
        trace_month_num = go.Bar(x=h_wind.index, y=h_wind.values)
        trace_avg = go.Scatter(
            x=[h_wind.index[0], len(h_wind.index)],
            y=[day_avg]*2,
            mode='lines+text',
            line={'width':0.8},
            text=[None, 'avg=' + str(int(day_avg)) + ' MWh'],
            textposition='middle left')
        if year != 2012:
            if month_num <= (row * cols): col += 1
            else: row += 1; col = 1
        else:
            if month_num <= (row * cols): col += 1
            else: row += 1; col = month_num % cols
        
        fig.append_trace(trace_month_num, row=row, col=col)
        fig.append_trace(trace_avg, row=row, col=col)

    fig.layout.update({'title':'Average Hour Wind Generation in ' + f'{year}',
                       'xaxis':{'title':'Hours'},
                       'yaxis':{'title':'Avg Power'},
                       'showlegend':False,
                       'width':800,
                       'height':700
                       },
                      autosize=True,
                    )
    iplot(fig);    


# In[46]:


# returns daily wind generation for given month, if second argument not given month number is taken randomly
wind_1(2020)


# In[47]:


# returns graph with wind power generation for given month of year but plotted in web browser
wind_1a(2013)


# In[48]:


# returns daily wind generation for given year
wind_2(2012)


# In[49]:


# returns separate bar graphs wiht monthly wind power generation for each year
for i in years_list():
    wind_3(i)


# In[50]:


# without optional second argument(any kind) linear graph is returned, in other cases function returns bar plot
wind_4(2015, 'akuku')


# In[51]:


wind_4(2015)


# In[52]:


# returns separate linear graphs with wind power cumulation for each year
wind_4a()


# In[53]:


# returns cumulative growth of wind generation for all years
wind_4b()


# In[54]:


# returns total wind power generation for all years
wind_4c()


# In[55]:


# returns bar plot with average (during 24 hours) wind power generation for given year
wind_5(2015)


# In[56]:


# returns average hour wind generation for each month of given year
wind_6(2019)

Notebook seems to be complete without errors - ready to use that code and prepare the form of python package and run from the command line(..to be continue) 