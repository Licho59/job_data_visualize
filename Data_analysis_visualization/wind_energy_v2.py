# coding: utf-8
import os, re, time, argparse
from glob import glob
import colorlover as cl
from datetime import date
from random import randint, choice, shuffle
import webcolors
import pandas as pd
from plotly.offline import plot
import plotly.graph_objs as go
import plotly.tools as tls

PATHNAME = os.getcwd()

def get_file(template):
    filenames = glob(template)
    if not filenames:
        raise Exception(
            'There are no files for given month or year in /Data/wind_csv_ready/ folder')
    assert len(filenames) == 1
    'There are more than one files for given month in / Data / wind_csv_ready / folder!'
    return filenames[0]


def get_raw_filename(year, month):
    return get_file(PATHNAME + '/Data/wind_csv/{}/PL_GEN_WIATR_{}{:02}*.csv'.format(year, year, month))
    

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
    if not os.path.exists('./Data/wind_csv_ready/{}/'.format(year)):
        os.makedirs('./Data/wind_csv_ready/{}'.format(year))
    return PATHNAME + '/Data/wind_csv_ready/{}/{}{:02}.csv'.format(year, year, month)


def get_transformed_filename(year, month):
    return get_file(transformed_filename(year, month))


def raw_files_list(year):
    raw_files, month_numbers = [], []
    for month_num in range(1, 13):
        try:
            file = get_raw_filename(year, month_num)
            raw_files.append(file)
            month_numbers.append(month_num)
        except:
            continue
    return raw_files, month_numbers


def files_list(year):
    # list of all csv files located in wind_csv_ready folder for given year
    ready_list = sorted(glob(f'./Data/wind_csv_ready/{year}/*.csv'))
    if len(ready_list) == 0:
        raw_files = get_raw_files_list(year)[0]
        if len(raw_files) > 0:
            for month in range(1, 13):
                try:
                    if os.path.exists(get_raw_filename(year, month)):
                        save_clean_data(year, month)
                except AssertionError:
                    continue
            ready_list = sorted(glob(f'./Data/wind_csv_ready/{year}/*.csv'))
        else:
            raise Exception(
                f'There is no data for {year} year. You should try to download it from PSE webpage.')
    return ready_list
    
    
    return sorted(glob(PATHNAME + '/Data/wind_csv_ready/{}/*.csv'.format(year)))


def save_clean_data(year, month_num):
    df = pd.read_csv(get_raw_filename(year, month_num),
                     encoding='iso 8859-1', sep=';').iloc[:, [0, 1, 2]]
    df.columns = ['Date', 'Time', 'Total_Wind_Power(MWh)']
    df['Time'] = df['Time'].astype('str').str.replace(
        '24', '0').str.replace('2A', '2')
    df['Total_Wind_Power(MWh)'] = df['Total_Wind_Power(MWh)'].str.replace(
        ',', '.').astype(float)
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
        df_all = [get_clean_data(year, month_num)
                  for month_num in get_raw_files_list(year)[1]]
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
    df_days = wind_hourly(year, month_num).set_index(
        'Date').resample('D').sum()
    df_days.rename(
        columns={'Total_Wind_Power(MWh)': 'Wind_Daily(MWh)'}, inplace=True)
    return df_days


def month_name(month_num):
    """
    Function month_name() returns name of month  to use it in formatting strings for plotting labels. 
    """
    return date(1990, int(month_num), 1).strftime('%B')


def month_names(months):
    return [month_name(month_num) for month_num in range(1, months)]


def years_list():
    whole_list = os.listdir(PATHNAME + '/Data/wind_csv')
    if '.DS_Store' in whole_list:
        return sorted(whole_list)[1:]
    else:
        return sorted(whole_list)

def get_random_colors():
    colors = webcolors.CSS3_NAMES_TO_HEX
    palette = [colors[key] for key in colors]
    shuffle(palette)
    return [palette[i] for i in range(12)]
   

def wind_1(year, month_number=None):
    """
    Input: number of month in range of 1-12 (or number for passed months of present year), by default it is
    random chosen month when function is being called without argument.
    Return: graph presenting daily total wind generation of power in Poland for given or random chosen month. 
    """
    if month_number:
        month_number = month_number
    else:
        month_number = randint(1, len(files_list(year)))
    
    wind_m = wind_daily(year, month_number) / 10**3
    month = month_name(month_number)
    m_avg = wind_m.iloc[:, 0].mean()

    data = [go.Bar(x=wind_m.index, y=wind_m['Wind_Daily(MWh)'].values, marker={
                   'color': 'orange'})]
    layout = {'xaxis': {'title': 'Days'}, 'yaxis': {'title': 'Total Power (GWh)'},
              'shapes': [{'type': 'line', 'x0': wind_m.index[0], 'x1':wind_m.index[-1], 'y0':m_avg, 'y1':m_avg,
                          'line':{'color': 'green', 'width': 2, 'dash': 'longdash'}}],
              'annotations': [{'x': wind_m.index[-3], 'y': m_avg,
                               'text': 'Avg Power=' + str(round(m_avg, 1)) + ' GWh',
                               'showarrow':True, 'arrowhead':1, 'ax':0, 'ay':-30}],
              'autosize': True,
              'title': f'Generation of Wind Power in {month} of {year}'}
    plot(go.Figure(data=data, layout=layout))


def wind_2(year):
    """
    Return: plot presenting wind power generation for each day of given year
    """
    # dataframe for all year round generation(or all months of present year)
    months = len(files_list(year)) + 1
    # to get values in TeraWatt Hours
    wind_y = wind_daily(year, months) / 10**3
    y_avg = wind_y['Wind_Daily(MWh)'].mean()
    data = [go.Bar(x=wind_y.index, y=wind_y['Wind_Daily(MWh)'].values, marker={'color': 'lightblue'}, name='Wind Power'),
            go.Scatter(x=[wind_y.index[0], wind_y.index[-1]], y=[y_avg] * 2,
                       mode='lines+text', line={'color': 'red', 'width': 0.8},
                       text=[None, 'Average Power=' + ': ' + str(int(y_avg)) + ' MWh'], textposition='top left', name='Year Average')]
    layout = {'xaxis': {'title': 'Days'}, 'yaxis': {'title': 'Total Power (GWh)'},
              'title': f'Generation of Wind Power in {year}'}
    plot(go.Figure(data=data, layout=layout))


def wind_3(year):
    """
    Return: plot presenting wind power generation for each month of given year
    """
    months = len(files_list(year)) + 1
    m_names = month_names(months)

    # dataframe resampled to months with index being months names
    wind_monthly = wind_daily(year, months).resample('M')
    wind_monthly = wind_monthly.sum().iloc[:, [0]] / 10**3

    data = [go.Bar(x=m_names, y=wind_monthly.iloc[:, 0],
                   marker=dict(color=choice(get_random_colors()),
                   autocolorscale=True))]
    layout = go.Layout(xaxis=dict(title='Months'), yaxis=dict(title='Total Power (GWh)'),
                       title="Monthly Wind Power Generation in {}".format(
                           year),
                       # showlegend=True)
                       )
    plot(go.Figure(data=data, layout=layout))


def wind_4(year, graph=None):
    """
    Return: linear or bar graph for cumulative amount of wind energy generated from the beginning of the year
    (some differences in plotting methods - with cufflinks tools and without it).
    Bar chart is returned with any kind of argument put after year number( for example: (2019, 1) or (2018,'bar'))
    """
    months = len(files_list(year)) + 1
    wind_y = wind_daily(year, months) / 10**3
    wind_grow = wind_y.cumsum()
    # total value for the last day of the plot
    last_day = round(wind_grow.max()[0], 1)
    if graph == 'line':
        data = [go.Scatter(x=wind_grow.index,
                           y=wind_grow['Wind_Daily(MWh)'].values,
                           name='Total=\n' + str(round(wind_grow.iloc[-1, 0], 1)) + ' GWh')]
    else:
        data = [go.Bar(x=wind_grow.index,
                       y=wind_grow['Wind_Daily(MWh)'].values,
                       name='Total=\n' + str(round(wind_grow.iloc[-1, 0], 1)) + ' GWh')]
    layout = go.Layout(xaxis=dict(title='Days'),
                       yaxis=dict(title='Total Power (GWh)'),
                       title="Growth of Wind Power Generation in {}".format(
                           year),
                       showlegend=True,
                       legend=dict(x=1.0, y=1.0))

    plot(go.Figure(data=data, layout=layout))


def wind_4a():
    """
    Return: Separate linear graphs for each year in data folder with cumulative amount of wind energy generated.
    """
    for year in years_list():
        months = len(files_list(year)) + 1
        wind_grow = (wind_daily(year, months) / 10**3).cumsum()
        # total value for the last day of the plot
        last_day = round(wind_grow.max()[0], 1)

        data = [go.Scatter(x=wind_grow.index, y=wind_grow['Wind_Daily(MWh)'].values, marker={
                           'color': 'orange'})]
        annotations = [{'x': wind_grow.index[-1], 'y':last_day,
                        'text':'Total=' + str(last_day) + ' GWh',
                        'textangle':0, 'showarrow':True, 'arrowhead':1, 'ax':0, 'ay':-20}]
        layout = {'xaxis': {'title': 'Days'},
                  'yaxis': {'title': 'Total Power(GWh)'},
                  'title': f'Wind Power Cumulation in {year}',
                  'annotations': annotations}
        plot(go.Figure(data=data, layout=layout))
        time.sleep(5)


def wind_4b():
    """
    Return: A single graph of number of plots for every year of wind generation's cumulative value
    """
    data = []
    years = years_list()
    
    # the 2012 year moved to the end of list to make plotting in that sequence,because data for 2012 begins in May and indexing would have been disturbed
    years.append(years[0])
    years.remove(years[0])
    
    for year in years:
        months = len(files_list(year)) + 1
        wind_grow = wind_daily(year, months)
        # code to work only when leap years occur(February with 29 days)
        if wind_grow.shape[0] == 366:
            df_days = wind_daily(year, months)
            df_days.iloc[58] = df_days.iloc[58, 0] + df_days.iloc[59, 0]
            df_days.drop(df_days.index[59], inplace=True)
            wind_grow = df_days.cumsum() / 10**6
        else:
            wind_grow = wind_grow.cumsum() / 10**6
        
        wind_grow.rename(columns={'Wind_Daily(MWh)': year}, inplace=True)
        wind_grow.index = wind_grow.index.strftime('%d/%m')
        last_day = round(wind_grow.max()[0], 1)
        trace = go.Scatter(x=wind_grow.index, y=wind_grow[year].values,
                           name=f'Total for {year}: {last_day} TWh', mode='lines')
        data.append(trace)
    layout = {'xaxis': {'title': 'Days of year'}, 'yaxis': {'title': 'Total Power (TWh)'},
              'title': 'Wind Power Generation in Years'}
    plot(go.Figure(data=data, layout=layout))

    
def wind_4c():
    """
    Return: Total yearly production of wind energy in GWh.
    """
    years = years_list()
    data = []
    for year in years:
        months = len(files_list(year)) + 1
        wind_grow = (wind_daily(year, months) / 10**3).resample('Y').sum()
        trace = go.Bar(x=wind_grow.index.strftime('%Y...'),
                       y=wind_grow['Wind_Daily(MWh)'], name=year)
        data.append(trace)
    layout = {'xaxis': {'title': 'Years'}, 'yaxis': {'title': 'Total Generation (GWh)'},
              'title': 'Wind Power Generation in Years'}
    plot(go.Figure(data=data, layout=layout))


def wind_5(year):
    """
    Return: A plot showing an average hour wind generation for a given year
    """
    months = len(files_list(year)) + 1
    df = wind_hourly(year, months)

    h_wind = df.pivot_table(index='Date', columns='Time',
                            values='Total_Wind_Power(MWh)').mean()
    hour_avg = h_wind.mean()

    data = [go.Bar(x=h_wind.index, y=h_wind.values)]
    layout = {'shapes': [{'type': 'line',
                          'x0': h_wind.index[0], 'y0': hour_avg, 'x1': len(h_wind.index), 'y1': hour_avg,
                          'line': {'color': 'red', 'width': 2, 'dash': 'longdash'}}],
              'showlegend': False,
              'annotations': [{'x': h_wind.index[-10], 'y': hour_avg,
                               'text': 'Avg Power=' + str(round(hour_avg, 1)) + ' MWh',
                               'showarrow':True, 'arrowhead':1, 'ax':0, 'ay':-30}],
              'xaxis': {'title': 'Hours'},
              'yaxis': {'title': 'Generation by Hour (MWh)'},
              'title': f"Wind Generation per Hour in {year}"}

    plot(go.Figure(data=data, layout=layout))


def wind_6(year):
    """
    Return: each month subplots for hour wind generation in given year
    """
    months = len(files_list(year))
    cols = 3
    rows = months // cols + 1
    if months % cols == 0:
        rows = rows - 1

    m_names = month_names(months)
    fig = tls.make_subplots(rows=rows, cols=cols,
                            shared_xaxes=True, shared_yaxes=True,
                            #subplot_titles=m_names,
                            print_grid=False)
    row, col = 1, 0
    for month_num in range(1, months + 1):
        month = month_name(month_num)

        # month dataframe with energy values for each hour
        df = wind_hourly(year, month_num)
        h_wind = df.pivot_table(
            index='Date', columns='Time', values='Total_Wind_Power(MWh)').mean()
        # average value of wind energy for all day
        day_avg = h_wind.mean()
        hour_avg = int(h_wind.mean())
        trace_month_num = go.Bar(x=h_wind.index, y=h_wind.values)
        trace_avg = go.Scatter(
            x=[h_wind.index[0], len(h_wind.index)], y=[hour_avg] * 2,
            mode='lines+text', line={'width': 0.8},
            text=[None, month + ': ' + str(int(hour_avg)) + ' MWh'], textposition='top left')

        if month_num <= (row * cols): col += 1
        else: row += 1; col = 1

        fig.append_trace(trace_month_num, row=row, col=col)
        fig.append_trace(trace_avg, row=row, col=col)

    fig.layout.update({'title': 'Average Hour Wind Generation in ' + f'{year}',
                       'xaxis': {'title': 'Hours'}, 'yaxis': {'title': 'Avg Power'},
                       'showlegend': False})
    plot(fig)


plot_description = "Plotting graphs coming from wind energy analyses.\n Numbers for graph functions:\n1 - wind_1(year, month_number=None) - daily wind generation for month; \n2 - wind_2(year) - daily wind generation for year; \n3 - wind_3(year) - monthly wind generation for year; \n4 - wind_4(year, graph='line') - growth of generation for a given year; \n4a - wind_4a() - separate plots for growth of generation for each year in data; \n4b - wind_4b() - joint plot for growth of generation for all years; \n4c - wind_4c() - total yearly generation for all years; \n5 - wind_5(year) - average hour generation for year; \n5a - wind_5(year) - separate hour average generation for each month in given year; \n6 - wind_6(year) - hour wind generation for each month."

def parse_arguments():
    years = sorted(years_list())
    graph = ['1', '2', '3', '3a', '4', '4a', '4b', '4c', '5', '5a', '6']
    
    parser = argparse.ArgumentParser(description= plot_description)
    
    parser.add_argument('graph_number', type=str, nargs='?',
        choices=['1', '2', '3', '3a', '4', '4a', '4b', '4c', '5', '5a', '6'])
    parser.add_argument('-y','--year', choices=years, default=years[0],
                        help='Provide a year number as an integer')
    parser.add_argument('-m', '--month', type=int, choices=list(range(1, 13)), default=list(range(1,13))[0],
                        help='Provide a number of month for expected plot')
    parser.add_argument('-i', '--info', action='store_true',
                        help='get description for argparse')
    parser.add_argument('-b', default='line',
                        action='store_true', help='get bar plot if invoked')
    parser.add_argument('-s', '--sleep', type=int,
                        default=5, help='get wait in action')
    args = parser.parse_args()
    

    if args.info:
        print(parser.description)
    
    if args.graph_number == '1':
        wind_1(args.year, args.month)
    elif args.graph_number == '2':
        wind_2(args.year)
    elif args.graph_number == '3':
        wind_3(args.year)
    elif args.graph_number == '3a':
        for year in years:
            wind_3(year)
            time.sleep(args.sleep)
    elif args.graph_number == '4':
        wind_4(args.year, args.b)
    elif args.graph_number == '4a':
        wind_4a()
    elif args.graph_number == '4b':
        wind_4b()
    elif args.graph_number == '4c':
        wind_4c()
    elif args.graph_number == '5':
        wind_5(args.year)
    elif args.graph_number == '5a':
        for year in years:
            wind_5(year)
            time.sleep(args.sleep)
    elif args.graph_number == '6':
        wind_6(args.year)
    elif args.graph_number not in graph:
        print(
            '\n\t!WRONG number! Use [-h] or [-i] option to get more info on module working.\n')


if __name__ == "__main__":
    parse_arguments()