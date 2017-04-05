import re
import os
import sys
import time
import pandas as pd


def parse_log_file(input_file=None, regular_exp=None):

    """Parses the NASA web server log file.

    Parses the input file line by line using the regular expression passed as an
    argument. All the lines which match the regular expression are considered valid
    and remaining are considered as invalid. Both valid and invalid records are stored
    in separate lists and returned by the function.

    Args:
        input_file: NASA web server log file.
        regular_exp: the regular expression to extract the relevant groups from every
         line in the log file.

    Returns:
        None if any one of the arguments are missing else returns a tuple of two lists
        with valid and invalid records. If the line is parsed successfully then it will
        be added to valid list else invalid list.

    Raises:
        IOError: if the log file is missing at the given location or there is some problem
        opening the log file.

    """

    print "\nParsing the log file..."

    # checks for the missing arguments
    if input_file is None or regular_exp is None:
        return None

    valid_records = list()
    invalid_records = list()

    try:
        # open the log file in read mode
        log_file = open(input_file, 'r')

        # reading log file line by line
        for line in log_file.readlines():

            # removing the new line character from each line
            line = line.strip('\n')

            # creating a match object for each line using the regular expression
            match_object = re.match(regular_exp, line)

            # If match is found, then adding to valid list else invalid list
            if match_object:
                # adding the found groups along with the log entry in the matched groups tuple
                valid_records.append(match_object.groups() + (line,))
            else:
                invalid_records.append(line)

    except IOError as e:

        # print the error message if issues in accessing log file and terminate the program.
        print "Error opening the log file!!"
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        sys.exit()

    else:
        # close the log file after parsing is completed.
        log_file.close()

        print "Log file parsing completed!!"

        # printing the total number of records parsed, valid and invalid
        print 'Total records : {} | Valid records  : {} | Invalid records : {}' \
            .format((len(valid_records) + len(invalid_records)),
                    len(valid_records), len(invalid_records))

        # returning the two lists
        return valid_records, invalid_records


def get_data_frame(input_records=None):

    """Creates a pandas data frame from the input records list.

    Returns the pandas data frame for the list of successfully parsed log records.
    Assigns the column headers, updates the missing values, assign data types to
    columns and formats the column values. It also generates additional columns from
    existing columns which will be required for analysis.

    Args:
        input_records: a list of all the successfully parsed log records from the NASA web
        server log file.

    Returns:
        A pandas data frame with all the required columns from the parsed log records.

    Raises:
        ValueError : if the column data type conversion is not a valid operation
        AssertionError : if the number of columns passed is different than the number of columns
        in the log data
        Exception : Any other exception raised while creating the data frame like unsupported input type.

    """

    # define the column headers for pandas data frame
    column_headers = ['host_name', 'timestamp', 'timezone', 'http_request', 'http_status_code',
                      'bytes_transferred', 'log_entry']
    try:

        # create the data frame from the input records with assigned column headers
        df_data = pd.DataFrame(input_records, columns=column_headers)

        # updating the '-' bytes transferred to 0 and changing column type to float
        df_data['bytes_transferred'].replace('-', '0', inplace=True)
        df_data['bytes_transferred'] = df_data['bytes_transferred'].astype('float64')

        # change the timestamp to datetime format
        df_data['timestamp'] = pd.to_datetime(df_data['timestamp'], format='%d/%b/%Y:%H:%M:%S')

        # create http method and uri columns from the http request column
        df_data['http_method'] = [x.split()[0] if len(x.split()) > 1 else '' for x in df_data['http_request']]
        df_data['uri'] = [x.split()[1] if len(x.split()) > 1 else x.split()[0] for x in df_data['http_request']]

    except ValueError as v:
        # print error message if the column data type conversion is invalid and exit the program
        print "Error while converting data types of pandas data frame columns"
        print "Value error({0}): {1}".format(v.errno, v.strerror)
        sys.exit()

    except AssertionError as a:
        # print error message if the invalid number of columns passed and exit the program
        print "Invalid number of columns passed for data frame creation"
        print "Assertion error({0}): {1}".format(a.errno, a.strerror)
        sys.exit()

    except Exception as e:
        print "Error while creating pandas data frame from the parsed records"
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        sys.exit()

    else:
        # return the created data frame
        return df_data


def get_top_n_active_hosts(n=0, input_data_frame=None):

    """Fetches the top n active hosts/IP Addresses.

    Fetches the top n most active hosts/IP addresses in descending order and how many times they
    have accessed any part of the site.

    Args:
        n: number of top active hosts required.
        input_data_frame: the data frame with the server log data

    Returns:
        A list with the top n active hosts along with the visit counts
        separated by a comma. Example:

            example.host.com,1000000
            another.example.net,800000
            31.41.59.26,600000

    """

    # check if input parameters are valid
    if n == 0 or input_data_frame is None:
        return None

    # get the data frame with host name as index and value counts i.e. group by host names and get frequency count
    host_visit_counts = input_data_frame['host_name'].value_counts(dropna=True)

    # if the number of distinct hosts available is less than given n then
    # update n to the number of distinct hosts
    if len(host_visit_counts) < n:
        n = len(host_visit_counts)

    # iterate through the top n entries of the data frame to get top n active hosts and append
    # results to a list.
    top_n_active_hosts = [str(host_visit_counts.index[i]) + ',' + str(host_visit_counts[i]) for i in range(n)]

    # return the list with top n active hosts
    return top_n_active_hosts


def get_top_n_resources_max_bandwidth(n=0, input_data_frame=None):

    """Fetches the top n resources based on bandwidth consumed

    Fetches the top n resources from the log records data frame based on the
    bandwidth consumption. Bandwidth consumption is extrapolated from bytes sent
    over the network and the frequency by which they were accessed.

    Args:
        n: number of top resources based on bandwidth consumed.
        input_data_frame: the data frame with the server log data

    Returns:
        A list with the top n bandwidth-intensive resources,
        sorted in descending order and separated by a new line. Example:

            /images/USA-logosmall.gif
            /shuttle/resources/orbiters/discovery.html
            /shuttle/countdown/count.html

    """

    # check if input parameters are valid
    if n == 0 or input_data_frame is None:
        return

    # create a grouped object based on uri as key and summing over the values in the bytes transferred column to get
    # the total bandwidth consumed.
    grouped_object = input_data_frame.groupby(['uri'], as_index=True)['bytes_transferred'].sum()

    # get the data frame with uri and total bandwidth consumed as columns sorted in descending order by bandwidth
    df_resources_bandwidth = pd.DataFrame({'uri': grouped_object.index,
                                           'bandwidth_used': grouped_object.values}).sort_values(['bandwidth_used'],
                                                                                                 ascending=False)

    # return the top n rows of the uri column of the data frame
    return df_resources_bandwidth['uri'][0:n]


def get_top_n_busiest_periods(n=0, period_in_minutes=0, input_data_frame=None):

    """Fetches the n busiest minute periods for given period window.

    Fetches the top n busiest (i.e. most frequently visited) from the log records data frame.
    The period window starts from any time and not when an event occurs.

    Used pandas dataframe, rolling window sum function to get the number of visits during that window.
    Shift function allows to move the rolling sum to start of the window instead of end (by default). The shift function
    moves up all the records by the sliding window size resulting in NaN values for the last records outside the
    sliding window size. Updated all the resulting NaN values with their respective sums in a separate loop.

    Args:
        n: number of top busiest periods required.
        period_in_minutes: the period window for which the busiest period is to be computed
        input_data_frame: the data frame with the server log data

    Returns:
        A list with the top n busiest periods with the start of each period window
        followed by the number of times the site was accessed during that time period.
        The results are listed in descending order with the busiest period window shown first.
        Example:

            01/Jul/1995:00:00:01 -0400,100
            02/Jul/1995:13:00:00 -0400,22
            05/Jul/1995:09:05:02 -0400,10
            01/Jul/1995:12:30:05 -0400,8

    """

    # check if input parameters are valid
    if n == 0 or period_in_minutes == 0 or input_data_frame is None:
        return

    # get the data frame with host names and value counts i.e. group by host names and get frequency count
    df_timestamp_visit_count = input_data_frame['timestamp'].value_counts().to_frame(name='num_visits')

    # get the minimum timestamp and maximum timestamp of the log entries and generate a index range to reindex the data
    # frame to get the window start times other than the event occurrences and make it continuous.
    min_timestamp_value = df_timestamp_visit_count.index.min(axis=0)
    max_timestamp_value = df_timestamp_visit_count.index.max(axis=0)

    new_index_range = pd.date_range(start=min_timestamp_value, end=max_timestamp_value, freq='S')

    # reindex the dataframe based on new index range and fill the default number of visits value for missing
    # timestamps as zero.
    df_timestamp_visit_count = df_timestamp_visit_count.reindex(new_index_range, fill_value=0)

    # get the sliding window size in seconds
    sliding_window_size = period_in_minutes * 60

    # if the range of timestamps is greater than sliding window then update the sliding window size to
    # the maximum range length.
    if len(new_index_range) < sliding_window_size:
        sliding_window_size = len(new_index_range)

    # get the rolling sum for the sliding window period and add it as new column to the existing dataframe.
    df_timestamp_visit_count['num_visits_in_window'] = df_timestamp_visit_count.rolling(
        window=sliding_window_size).sum().shift(-(sliding_window_size - 1))

    # Update the records with NaN values due to shift operation.
    for i in range(1, sliding_window_size):
        df_timestamp_visit_count.set_value(df_timestamp_visit_count.index[len(df_timestamp_visit_count) + i -
                                                                          sliding_window_size], 'num_visits_in_window',
                                           sum(df_timestamp_visit_count['num_visits'][i - sliding_window_size:]))

    # changing the data type of number of visits column to integer type
    df_timestamp_visit_count['num_visits_in_window'] = df_timestamp_visit_count['num_visits_in_window'].astype('int64')

    # extracting the timezone from the timezone column. Assuming all logs are from same timezone
    timezone = list(set(input_data_frame['timezone']))[0]

    # sorting the dataframe in descending order based on the number of visits in the period window.
    df_timestamp_visit_count.sort_values('num_visits_in_window', ascending=False, inplace=True)

    # list of top n busiest periods
    busiest_periods = [pd.to_datetime(df_timestamp_visit_count.index[i]).strftime('%d/%b/%Y:%H:%M:%S') +
                       ' ' + str(timezone) + ',' +
                       str(df_timestamp_visit_count['num_visits_in_window'][i]) for i in range(n)]

    # returns the top busiest periods in descending order
    return busiest_periods


def get_host_with_n_login_failures(n=0, input_data_frame=None):

    """Fetches all hosts and rows from dataframe with failed login attempts

    Filters the rows from the input data frame with failed login attempts i.e. with http status code
    as 401 and where number of such failed attempts for a particular host is greater or equal to n. The method
    returns the list of such hosts and the dataframe with filtered rows.

    Args:
        n: number of failure attempts by a host
        input_data_frame : the dataframe with the log data

    Returns:
        list, dataframe : A list of hosts with number of attempts greater than or equals to n and dataframe with
        all such failed attempt login rows.

    """

    # check if input parameters are valid
    if n == 0 or input_data_frame is None:
        return

    # get the dataframe with only failed login attempts i.e. http status code as 401 and count the number of
    # failed attempts for each host.
    df_failed_login_attempts = input_data_frame[input_data_frame['http_status_code'] == '401']
    df_failed_login_attempts_count = df_failed_login_attempts['host_name'].value_counts()

    # get the list of all hosts with failed attempts greater or equal to n
    hosts = df_failed_login_attempts_count[df_failed_login_attempts_count >= n].index

    # retain the failed attempt rows only for host names in hosts list.
    df_failed_login_attempts = df_failed_login_attempts[df_failed_login_attempts['host_name'].isin(hosts)]

    return hosts, df_failed_login_attempts


def get_host_block_window_start(input_data_frame, consecutive_failures_limit,
                                blocked_window_time, login_failure_window):

    """Fetches the host name and block window start time

    Retrieves the dataframe with host name and block window start time for all the hosts with consecutive login
    failures within the login failure window. The block start time will be used to get all the entries which could have
    been potentially blocked within the blocked time window.

    Args:
        blocked_window_time: blocked window time in minutes after consecutive login failures. E.g. 5 min attempts block
        consecutive_failures_limit: threshold for number of consecutive login failures. E.g. 3 failures
        login_failure_window: failure window time in seconds over which the consecutive failures occur. E.g. 20 seconds
        input_data_frame: the data frame with the server log data

    Returns:
        A dataframe with host name and block window start timestamp.

    """

    hosts = list()
    ban_start_timestamps = list()

    # iterate through each host and check for block start window
    for host in input_data_frame['host_name'].unique():

        # to track if failed attempt is already within block window
        prev_ban_start_window = None

        # dataframe with failed attempts for a particular host
        df_host_failed_timestamps = input_data_frame[input_data_frame['host_name'] == host]['timestamp']

        i = 0

        # iterate through all the failed attempts to check if there are consecutive failures and are in login failure
        # window.
        while i < len(df_host_failed_timestamps) - consecutive_failures_limit + 1:

            # get the current failure timestamp
            window_lower_bound = pd.to_datetime(df_host_failed_timestamps.iloc[i])

            if prev_ban_start_window is not None:

                # check if it falls in 5 minute time window
                delta_time = pd.Timedelta(window_lower_bound - prev_ban_start_window).seconds

                # if it is within blocked time window then ignore and move to next record.
                if 0 < delta_time <= 60*blocked_window_time:
                    i += 1
                    continue
                else:
                    prev_ban_start_window = None

            # get the failure timestamp of last consecutive failure limit
            window_upper_bound = pd.to_datetime(df_host_failed_timestamps.iloc[i + consecutive_failures_limit - 1])

            # get the time difference between the consecutive failures
            failure_time_window = pd.Timedelta(window_upper_bound - window_lower_bound).seconds

            # if time difference is within login failure window then add the host and last consecutive failure timestamp
            # to respective lists else move to the next record
            if 0 < failure_time_window < login_failure_window:

                # add to the list
                hosts.append(host)
                ban_start_timestamps.append(window_upper_bound)

                # set the the prev block start window as last consecutive failure timestamp
                prev_ban_start_window = window_upper_bound

                # move to the attempt immediately after the last consecutive failure timestamp
                i += consecutive_failures_limit
            else:
                i += 1

    return pd.DataFrame({'host_name': hosts, 'ban_start_timestamp': ban_start_timestamps})


def get_login_failure_blocked_records(blocked_window_time=0, consecutive_failure_limit=0,
                                      login_failure_window=0, input_data_frame=None):

    """Retrieves the potential blocked records in case of consecutive login failures

    Detects pattern of consecutive failed login attempts exceeding the defined consecutive failure limit for a
    particular host/IP Address over login failure window (in seconds). All the following attempts to reach the site by
    same host/IP Address within defined blocked window time (in minutes) is recorded. If a login attempt succeeds
    during login failure window then the failed login counter and login failure window gets reset.

    Args:
        blocked_window_time: blocked window time in minutes after consecutive login failures. E.g. 5 min attempts block
        consecutive_failure_limit: threshold for number of consecutive login failures. E.g. 3 failures
        login_failure_window: failure window time in seconds over which the consecutive failures occur. E.g. 20 seconds
        input_data_frame: the data frame with the server log data

    Returns:
        A list with original log entries of all the potential blocked attempts within the blocked window made after the
        consecutive login failures.
        For example:

        uplherc.upl.com - - [01/Aug/1995:00:00:07 -0400] "GET / HTTP/1.0" 304 0
        uplherc.upl.com - - [01/Aug/1995:00:00:08 -0400] "GET /images/ksclogo-medium.gif HTTP/1.0" 304 0

    """

    # check if input parameters are valid
    if blocked_window_time == 0 or consecutive_failure_limit == 0 or login_failure_window == 0 \
            or input_data_frame is None:
        return

    # Get the list of hosts with failed login attempts greater than the consecutive failure limit, not necessarily in
    # failure limit window. This is to slice the input data frame and also all failed login attempt rows in dataframe.
    filtered_hosts, df_failed_login_records = get_host_with_n_login_failures(n=consecutive_failure_limit,
                                                                             input_data_frame=input_data_frame)

    # sort the failed login attempts dataframe by hostname and timestamp
    df_failed_login_records = df_failed_login_records.sort_values(['host_name', 'timestamp'], ascending=[True, True])

    # get the dataframe with host name and block window start time for that hosts.
    df_host_block_window_start = get_host_block_window_start(df_failed_login_records, consecutive_failure_limit,
                                                             blocked_window_time, login_failure_window)

    # slice the input data frame and get the hosts with login failures equal to or greater than allowed failures.
    df_filtered_hosts = input_data_frame[input_data_frame['host_name'].isin(filtered_hosts)]

    blocked_records = list()

    # iterate through the sliced input dataframe and get all the attempts with blocked window period from the block
    # start time for each host with failure attempts equal or greater than threshold.
    for host in df_host_block_window_start['host_name']:

        # get records for one host
        host_all_records = df_filtered_hosts[df_filtered_hosts['host_name'] == host]

        # fetch the block start time for the host
        ban_window_start = df_host_block_window_start[df_host_block_window_start['host_name']
                                                      == host]['ban_start_timestamp'].iloc[0]

        # append the blocked records to the list which fall within blocked period window
        blocked_records.extend([row.log_entry for index, row in host_all_records.iterrows()
                                if 0 < pd.Timedelta(row['timestamp'] - ban_window_start).seconds <= 60 *
                                blocked_window_time])

    return blocked_records


def write_to_file(output_file=None, input_data=None):

    """Writes the list value to the output file.

    Reads the values from the list line and line and writes it to the specified output
    file. Each record is separated by new line character.

    Args:
        output_file: Output file to which the output has to be written
        input_data: the list with records to be written in the file

    Raises:
        IOError: if the output file is missing at the given location or there is some problem
        opening the output file.
    """

    # check if input parameters are valid
    if output_file is None or input_data is None:
        return

    try:
        # open the output file in write mode
        out_file = open(output_file, 'w')

    except IOError as e:
        # print the error message if issues in accessing output file
        print "Error opening the output file!!"
        print "I/O error({0}): {1}".format(e.errno, e.strerror)

    else:
        print ("\nWriting output to " + output_file)

        # write the list content to output file separated by new line character.
        out_file.write("\n".join(input_data))
        out_file.close()

        print ("Output written successfully!!")


def main():

    """



    """

    # get the list of parsed records and bad records
    parsed_records, bad_records = parse_log_file(input_file=LOG_FILE, regular_exp=REGEX)

    # write all the unprocessed records to bad records output file
    if bad_records is not None and len(bad_records) > 0:
        write_to_file(output_file=BAD_RECORDS_FILE, input_data=bad_records)

    # get the pandas data frame from the parsed records for further analysis
    df_log_data = get_data_frame(input_records=parsed_records)

    if df_log_data is None and len(df_log_data) == 0:
        print "Invalid dataframe or no records in dataframe to analyze."
        sys.exit()

    # feature 1 : get the top active hosts
    top_active_hosts = get_top_n_active_hosts(n=NUM_OF_ACTIVE_HOSTS, input_data_frame=df_log_data)

    # if top active hosts is not none then write to the hosts.txt file
    if top_active_hosts is not None:
        write_to_file(output_file=HOSTS_FILE, input_data=top_active_hosts)
    else:
        print "Error while getting top 10 active hosts"

    # feature 2 : get the top resources based on the bandwidth used
    top_resources = get_top_n_resources_max_bandwidth(n=NUM_OF_TOP_RESOURCES, input_data_frame=df_log_data)

    # if top resources is not none then write to the resources.text file
    if top_resources is not None:
        write_to_file(output_file=RESOURCES_FILE, input_data=top_resources)
    else:
        print "Error while getting top 10 resources"

    # feature 3 : get the busiest periods for the given time window
    top_busy_periods = get_top_n_busiest_periods(n=NUM_OF_BUSIEST_PERIODS, period_in_minutes=BUSY_PERIOD_WINDOW,
                                                 input_data_frame=df_log_data)

    # if top busiest periods is not none then write to the hours.text file
    if top_busy_periods is not None:
        write_to_file(output_file=HOURS_FILE, input_data=top_busy_periods)
    else:
        print "Error while getting top 10 busiest periods"

    # feature 4 : get the potential blocked entries in case of 3 consecutive login attempts in 20 second window
    potential_blocked_entries = get_login_failure_blocked_records(blocked_window_time=BLOCK_WINDOW_MIN,
                                                                  consecutive_failure_limit=LOGIN_FAILURES_LIMIT,
                                                                  login_failure_window=LOGIN_FAILURES_WINDOW_SEC,
                                                                  input_data_frame=df_log_data)

    # if the potential blocked entries is not none then write to the blocked.txt file
    if potential_blocked_entries is not None:
        write_to_file(output_file=BLOCKED_FILE, input_data=potential_blocked_entries)
    else:
        print "Error while getting the potential blocked entries in case of consecutive login failure"


if __name__ == '__main__':

    # check the length command line arguments for missing parameters.
    if len(sys.argv) != 7:
        print "Missing command line arguments. 7 arguments expected and " + str(len(sys.argv)) + " provided."
        print "Example Usage : \n python ./src/process_log.py ./log_input/log.txt ./log_output/hosts.txt " \
              "./log_output/hours.txt ./log_output/resources.txt ./log_output/blocked.txt " \
              "./log_output/bad_records.txt\n "
        sys.exit()

    # setting up the various parameter values for features 1 to 4
    NUM_OF_ACTIVE_HOSTS = 10
    NUM_OF_TOP_RESOURCES = 10
    NUM_OF_BUSIEST_PERIODS = 10
    BUSY_PERIOD_WINDOW = 60
    BLOCK_WINDOW_MIN = 5
    LOGIN_FAILURES_LIMIT = 3
    LOGIN_FAILURES_WINDOW_SEC = 20

    # reading the file path locations from system command line arguments
    LOG_FILE = os.path.abspath(sys.argv[1])
    HOSTS_FILE = os.path.abspath(sys.argv[2])
    HOURS_FILE = os.path.abspath(sys.argv[3])
    RESOURCES_FILE = os.path.abspath(sys.argv[4])
    BLOCKED_FILE = os.path.abspath(sys.argv[5])
    BAD_RECORDS_FILE = os.path.abspath(sys.argv[6])

    # regular expression object to match the line in the server logs.
    REGEX = re.compile(r"([^\s]+).*?\[(.*)?\s(.*)?\][\s]+\"(.*)?\"[\s]+([^\s]+)[\s]+([^\s]+)")

    # creating a time object to get the current time.
    start_time = time.time()

    # call the main method
    main()

    # print the time taken for the complete execution of the program
    print("\n--- %s seconds ---" % (time.time() - start_time))
