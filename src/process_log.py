import re
import pandas as pd
from config import log_file_path, number_of_active_hosts, number_of_top_resources, number_of_busiest_periods, busy_period_window_in_min

regex = re.compile(r"([^\s]+).*?\[(.*)?\s(.*)?\][\s]+\"(.*)?\"[\s]+([^\s]+)[\s]+([^\s]+)")

log_file = open(log_file_path)


def parse_log_file(input_file=None, regular_exp=None):

    print "\nStarted parsing the log file..."

    if input_file is None or regular_exp is None:
        return

    valid_records = list()
    invalid_records = list()

    for line in input_file.readlines():

        line = line.strip('\n')

        match_object = re.match(regular_exp, line)

        if match_object:
            valid_records.append(match_object.groups() + (line,))
        else:
            invalid_records.append(line)

    print "Log file parsing completed!!"

    print 'Total records : {} | Valid records  : {} | Invalid records : {}'\
        .format((len(valid_records)+len(invalid_records)),
                len(valid_records), len(invalid_records))

    return valid_records, invalid_records


def get_data_frame(input_records=None, column_names=None):

    df_data = pd.DataFrame(input_records, columns=column_names)

    # updating the '-' bytes transferred to 0 and changing column type to float
    df_data['bytes_transferred'].replace('-', '0', inplace=True)
    df_data['bytes_transferred'] = df_data['bytes_transferred'].astype('float64')

    # change the timestamp to datetime format
    df_data['timestamp'] = pd.to_datetime(df_data['timestamp'], format='%d/%b/%Y:%H:%M:%S')

    # create http method and uri columns from the http request column
    df_data['http_method'] = [x.split()[0] if len(x.split()) > 1 else '' for x in df_data['http_request']]
    df_data['uri'] = [x.split()[1] if len(x.split()) > 1 else x.split()[0] for x in df_data['http_request']]

    return df_data


def get_top_n_active_hosts(n=0, input_data_frame=None):

    if n == 0 or input_data_frame is None:
        return

    host_visit_counts = input_data_frame['host_name'].value_counts(dropna=True)

    top_n_active_hosts = [str(host_visit_counts.index[i]) + ',' + str(host_visit_counts[i]) for i in range(n)]

    return top_n_active_hosts


def get_top_n_resources_max_bandwidth(n=0, input_data_frame=None):

    if n == 0 or input_data_frame is None:
        return

    grouped_object = input_data_frame.groupby(['uri'], as_index=True)['bytes_transferred'].sum()

    df_resources_bandwidth = pd.DataFrame({'uri': grouped_object.index,
                                           'bandwidth_used': grouped_object.values}).sort_values(['bandwidth_used'],
                                                                                                 ascending=False)

    return df_resources_bandwidth['uri'][0:n]


def get_top_n_busiest_periods(n=0, period_in_minutes=0, input_data_frame=None):

    if n == 0 or period_in_minutes == 0 or input_data_frame is None:
        return

    df_timestamp_visit_count = input_data_frame['timestamp'].value_counts().to_frame(name='num_visits')

    min_timestamp_value = df_timestamp_visit_count.index.min(axis=0)
    max_timestamp_value = df_timestamp_visit_count.index.max(axis=0)

    new_index_range = pd.date_range(start=min_timestamp_value, end=max_timestamp_value, freq='S')

    df_timestamp_visit_count = df_timestamp_visit_count.reindex(new_index_range, fill_value=0)

    sliding_window_size = period_in_minutes * 60

    df_timestamp_visit_count['num_visits_in_window'] = df_timestamp_visit_count.rolling(
        window=sliding_window_size).sum().shift(-(sliding_window_size - 1))

    total_records = len(df_timestamp_visit_count)

    for i in range(1, sliding_window_size):
        df_timestamp_visit_count.set_value(df_timestamp_visit_count.index[total_records + i - sliding_window_size],
                                           'num_visits_in_window',
                                           sum(df_timestamp_visit_count['num_visits'][i - sliding_window_size:]))

    df_timestamp_visit_count['num_visits_in_window'] = df_timestamp_visit_count['num_visits_in_window'].astype('int64')

    timezone = list(set(input_data_frame['timezone']))[0]

    df_timestamp_visit_count.sort_values('num_visits_in_window', ascending=False, inplace=True)

    busiest_periods = [str(pd.to_datetime(df_timestamp_visit_count.index[i])) + ' ' + str(timezone) + ',' + str(
        df_timestamp_visit_count['num_visits_in_window'][i]) for i in range(n)]

    return busiest_periods

parsed_records, bad_records = parse_log_file(input_file=log_file, regular_exp=regex)

column_headers = ['host_name', 'timestamp', 'timezone', 'http_request', 'http_status_code',
                  'bytes_transferred', 'log_entry']

df_log_data = get_data_frame(input_records=parsed_records, column_names=column_headers)

top_active_hosts = get_top_n_active_hosts(n=number_of_active_hosts, input_data_frame=df_log_data)

print ("\nTop " + str(number_of_active_hosts) + " active hosts (host_name, #visits): ")
print("\n".join(top_active_hosts))

top_resources = get_top_n_resources_max_bandwidth(n=number_of_top_resources, input_data_frame=df_log_data)

print ("\nTop " + str(number_of_top_resources) + " resources (URI): ")
print("\n".join(top_resources))

top_busy_periods = get_top_n_busiest_periods(n=number_of_busiest_periods, period_in_minutes=busy_period_window_in_min,
                                             input_data_frame=df_log_data)

print ("\nBusiest " + str(number_of_busiest_periods) + " periods (period_start_time, #visits): ")
print ("\n".join(top_busy_periods))
