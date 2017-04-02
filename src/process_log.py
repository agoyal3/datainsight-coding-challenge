import re
import pandas as pd
import collections
from config import log_file_path

regex = re.compile(r"([^\s]+).*?\[(.*)?\s(.*)?\][\s]+\"(.*)?\"[\s]+([^\s]+)[\s]+([^\s]+)")

log_file = open(log_file_path)


def parse_log_file(input_file = None, regular_exp = None):

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

    print 'Number of valid records in file : {}'.format(len(valid_records))
    print 'Number of invalid records in file : {}'.format(len(invalid_records))

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

    return zip(host_visit_counts.index[0:n], host_visit_counts[0:n])


parsed_records, bad_records = parse_log_file(input_file=log_file, regular_exp=regex)

column_headers = ['host_name', 'timestamp', 'timezone', 'http_request', 'http_status_code',
                  'bytes_transferred', 'log_entry']

df_log_data = get_data_frame(input_records=parsed_records, column_names=column_headers)

top_active_hosts = get_top_n_active_hosts(n=10, input_data_frame=df_log_data)

print top_active_hosts