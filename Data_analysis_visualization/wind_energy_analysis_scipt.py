
# coding: utf-8

import os, re, random, time
from glob import glob
from datetime import date
import pandas as pd
from plotly.offline import plot
import plotly.graph_objs as go
import plotly.tools as tls
import cufflinks as cf
cf.go_offline()

PATHNAME = 'C:/Users/14000322/AppData/Local/Programs/Python/Python36-32/Scripts/job_data_visualize/Data_analysis_visualization'


def get_file(template):
    filenames = glob(template)
    assert len(filenames) == 1
    return filenames[0]


def get_raw_filename(year, month):
    return get_file(PATHNAME + f'./Data/wind_csv/{year}/PL_GEN_WIATR_{year}{month:02}*.csv')


def transformed_filename(year, month):
    return PATHNAME + f'./Data/wind_csv_ready/{year}/{year}{month:02}.csv'


def get_transformed_filename(year, month):
    return get_file(transformed_filename(year, month))


def files_list(year):
    # list of all csv files located in wind_csv_ready folder
    return sorted(glob(PATHNAME + f'./Data/wind_csv_ready/{year}/*.csv')) 


def save_clean_data(year, month_num):
    df = pd.read_csv(get_raw_filename(year, month_num), encoding='iso 8859-1', sep=';').iloc[:,[0, 1, 2]]
    df.columns = ['Date', 'Time', 'Total_Wind_Power(MWh)']
    df['Time'] = df['Time'].astype('str').str.replace('24', '0').str.replace('2A', '2')
    df['Total_Wind_Power(MWh)'] = df['Total_Wind_Power(MWh)'].str.replace(',', '.').astype(float)
    df.to_csv(transformed_filename(year, month_num), index=None, header=True)


def get_clean_data(year, month):
    return pd.read_csv(get_transformed_filename(year, month))


def wind_hourly(year, month_num):
    """
    Input: function takes the year and the number of month in range between 1 and number of months for given year 
    Return: dataframe either for month's wind power generation or for all months - to use for visualization, analysis,
    modelling.
    """
    list_length = len(files_list(year)) 
    # preparing dataframe either for all months in year or for only one month
    if month_num == list_length + 1:
        df_all = [get_clean_data(year, month_num) for month_num in range(1, list_length+1)]
        df = pd.concat(df_all)
    else:
        df = get_clean_data(year, month_num)
    df['Time'] = df['Time'].astype('str')
    df['Date'] = pd.to_datetime(df['Date'].astype('str'))
    return df


def wind_daily(year, month_num):
    """
    Return: dataframe of wind generation where indexing is by day values not by hours
    """
    # resampled data from hours to days
    df_days = wind_hourly(year, month_num).set_index('Date').resample('D').sum()
    df_days.rename(columns={'Total_Wind_Power(MWh)':'Wind_Daily(MWh)'}, inplace=True)
    return df_days


def month_name(month_num):
    """
    Function month_name() returns name of month  to use it in formatting strings for plotting labels. 
    """
    return date(1990, int(month_num), 1).strftime('%B')


def month_names(months):
    return [month_name(month_num) for month_num in range(1, months)]

def years_list():
    return os.listdir(PATHNAME + './Data/wind_csv')[1:]


"""
Names for graphs functions:
      wind_1 - daily wind generation for month
      wind_2 - daily wind generation for year
      wind_3 - monthly wind generation for year
      wind_4 - growth of generation (cumulative) - line or bar - for year
      wind_4a - cumulative growth of generation for each year
      wind_4b - cumulative growth of generation for all years
      wind_5 - average hour generation for year
      wind_6 - hour wind generation for each month
"""

def wind_1(year, month_number=None):
    """
    Input: number of month in range of 1-12 (or number for passed months of present year), by default it is
    random chosen month when function is being called without argument.
    Return: graph presenting daily total wind generation of power in Poland for given or random chosen month. 
    """
    if month_number:
        month_number = month_number
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


def wind_2(year):
    """
    Return: plot presenting wind power generation for each day of given year
    """  
    # dataframe for all year round generation(or all months of present year)
    months = len(files_list(year)) + 1
    wind_y = wind_daily(year, months)/10**3    # to get values in TeraWatt Hours
    y_avg = wind_y['Wind_Daily(MWh)'].mean()
    data = [go.Bar(x=wind_y.index, y=wind_y['Wind_Daily(MWh)'].values, marker={'color':'lightblue'}, name='Wind Power'),
            go.Scatter(x=[wind_y.index[0], wind_y.index[-1]], y=[y_avg]*2,
            mode='lines+text', line={'color':'red', 'width':0.8},
            text=[None, 'Average Power=' + ': ' + str(int(y_avg)) + ' MWh'], textposition='top left', name='Year Average')]
    layout = {'xaxis':{'title':'Days'}, 'yaxis':{'title':'Total Power (GWh)'},
              'title':f'Generation of Wind Power in {year}'}
    plot(go.Figure(data=data, layout=layout))


def wind_3(year):
    """
    Return: plot presenting wind power generation for each month of given year
    """
    
    months = len(files_list(year)) + 1
    m_names = month_names(months)
    
    # dataframe resampled to months with index being months names
    wind_monthly = wind_daily(year, months).resample('M')
    wind_monthly = wind_monthly.sum().iloc[:,[0]]/10**3

    data = [go.Bar(x=m_names, y=wind_monthly.iloc[:,0], marker=dict(color='limegreen'), name='Power by Month')]
    layout = go.Layout(xaxis=dict(title='Months'), yaxis=dict(title='Total Power (GWh)'),
                       title="Monthly Wind Power Generation in {}".format(year),
                       height=400, width=800,
                       # showlegend=True)
                      )
    plot(go.Figure(data=data, layout=layout))
    


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
        return wind_grow.plot(kind='scatter',
                    width=2,
                    annotations=[dict(
                                x=wind_y.index[-1], y=last_day,
                                text='Total=' + str(last_day) + ' GWh', textangle=0,
                                showarror=True, arrowhead=1, ax=0, ay=-20)],
                    xTitle='Days', yTitle='Total Power (GWh)', color='green',
                    title=f"Wind Power Cumulation in {year}", theme='solar', dimensions=(800, 350))
      
    else:
        data = [go.Bar(x=wind_grow.index,
                           y=wind_grow['Wind_Daily(MWh)'].values,
                           name='Total=\n'+str(round(wind_grow.iloc[-1,0], 1)) + ' GWh')]
        layout = go.Layout(xaxis=dict(title='Days'), yaxis=dict(title='Total Power (GWh)'),
                           title="Growth of Wind Power Generation in {}".format(year),
                           height=450, width=900,
                           showlegend=True,
                           legend=dict(x=1.0, y=1.0))
       
        plot(data,layout)


def wind_4a(plot='line'):
    """
    Return: linear or bar graph for cumulative amount of wind energy generated from the beginning of the year
    (some differences in plotting methods - with cufflinks tools and without it).
    Bar chart is returned with any kind of argument put after year number( for example: (2019, 1) or (2018,'bar'))
    """
    for year in years_list():
        months = len(files_list(year)) + 1
        wind_y = wind_daily(year, months)/10**3
        wind_grow = wind_y.cumsum()
        print(wind_grow.index)
        last_day = round(wind_grow.max()[0], 1) # total value for the last day of the plot

        if plot=='line':
            wind_grow.plot(kind='scatter',
                        x=wind_grow.index[0], y=wind_grow[year].values,)
                        #width=2,
                        #annotations=[dict(x=wind_y.index[-1], y=last_day,
                         #               text='Total=' + str(last_day) + ' GWh', textangle=0,
                          #              showarror=True, arrowhead=1, ax=0, ay=-20)],
                        #xTitle='Days', yTitle='Total Power (GWh)', color='green',
                        #title=f"Wind Power Cumulation in {year}",
                        #theme='solar', dimensions =(800, 350))


def wind_4b():
    data = []
    years = years_list()

    for year in years:
        months = len(files_list(year)) + 1
        wind_grow = wind_daily(year, months).cumsum()/10**6
        wind_grow.rename(columns={'Wind_Daily(MWh)': year}, inplace=True)
        wind_grow.index = wind_grow.index.strftime('%d/%m')
        last_day = round(wind_grow.max()[0], 1)
        trace = go.Scatter(x=wind_grow.index, y=wind_grow[year].values,
                           name=f'Total for {year}: {last_day} TWh', mode='lines')
        data.append(trace)

    layout = {'xaxis':{'title':'Days of year'}, 'yaxis':{'title':'Total Power (TWh)'},
             'title':'Wind Power Generation in Years',
             'width':850, 'height':400}
    plot(go.Figure(data=data, layout=layout))


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
            'title':f"Wind Generation per Hour in {year}",
            'width':800, 'height': 400}

    plot(go.Figure(data=data, layout=layout))


def wind_6(year):
    """
    Return: each month subplots for hour wind generation in given year
    """
    months = len(files_list(year))
    cols = 3
    rows = months//cols + 1
    if months % cols == 0: rows = rows - 1

    m_names = month_names(months)
    fig = tls.make_subplots(rows=rows, cols=cols,
                            shared_xaxes=True, shared_yaxes=True,
                            #subplot_titles=month_names,
                            print_grid=False)
    row, col = 1, 0
    for month_num in range(1, months+1):
        month = month_name(month_num)

        # month dataframe with energy values for each hour
        df = wind_hourly(year, month_num)
        h_wind = df.pivot_table(index='Date', columns='Time', values='Total_Wind_Power(MWh)').mean()
        
        # average value of wind energy for all day
        day_avg = h_wind.mean()
        hour_avg = int(h_wind.mean())
        trace_month_num = go.Bar(x=h_wind.index, y=h_wind.values)
        trace_avg = go.Scatter(
            x=[h_wind.index[0], len(h_wind.index)], y=[hour_avg]*2,
            mode='lines+text', line={'width':0.8},
            text=[None, month + ': ' + str(int(hour_avg)) + ' MWh'], textposition='top left')

        if month_num <= (row * cols):
            col += 1
        else:
            row += 1
            col = 1

        fig.append_trace(trace_month_num, row=row, col=col)
        fig.append_trace(trace_avg, row=row, col=col)

    fig.layout.update({'title':'Average Hour Wind Generation in ' + f'{year}',
                       'xaxis':{'title':'Hours'}, 'yaxis':{'title':'Avg Power'},
                       'showlegend':False,
                       'width':900, 'height':800})
    plot(fig);    





# Used one time for given year to make transformed files and save them into wind_csv_ready folder
for year in years_list():
    for month in range(1, len(years_list()) + 1):
        save_clean_data(year, month)

#wind_1(2019)


#wind_2(2017)


#wind_3(2018)
    
for year in years_list(): wind_3(year); time.sleep(5)


#wind_4(2017)


#wind_4a()


#wind_4b()


#wind_5(2019)


#wind_6(2019)
