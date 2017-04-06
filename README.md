# datainsight-coding-challenge

## Table of Contents
1. [Introduction](README.md#introduction)
2. [Dataset](README.md#dataset)
3. [Data Loading](README.md#data-loading)
4. [Features Implementation](README.md#feature-implementation)   
	1. [Feature 1](README.md#feature-1)
	2. [Feature 2](README.md#feature-2)
	3. [Feature 3](README.md#feature-3)  
	4. [Feature 4](README.md#feature-4)  
5. [Run the program](README.md#run-the-program)
6. [References](README.md#references)


## Introduction
This repository contains the source code for the DataInsight Coding Challenge. The original code challenge description 
could be found [here](challenge-description.md). The overview of the challenge is to perform basic analytics on the NASA web server log file, provide useful metrics, and implement basic security measures.

### Pre-requisites
- Python 2.7 or later  
	The code has been written and tested on Ubuntu 16.04 using Python 2.7. 
	
- [pandas v0.19.2](http://pandas.pydata.org/pandas-docs/stable/)  
	pandas is a Python package which provides fast, flexible, and expressive data structures designed to make working with “relational” or “labeled” data both easy and intuitive. It aims to be the fundamental high-level building block for doing practical, real world data analysis in Python. 
	
	
	Install using pip command:

		pip install pandas
		
	The package can be installed in different ways, as described [here](http://pandas.pydata.org/pandas-docs/stable/install.html).  
	 
	 
## Dataset
NASA web server logs data can be downloaded from [here](https://drive.google.com/file/d/0B7-XWjN4ezogbUh6bUl1cV82Tnc/view).

The log data is in ASCII format with one line per request. Below are two sample records from the logs:

    208.271.69.50 - - [01/Aug/1995:00:00:02 -400] "POST /login HTTP/1.0" 401 1420
    uplherc.upl.com - - [01/Aug/1995:00:00:07 -0400] "GET / HTTP/1.0" 304 0

- **host** making the request  
`208.271.69.50` and `uplherc.upl.com` are the hosts/IP address making the request. 

- **timestamp** is enclosed in the square brackets. Format : `[DD/MON/YYYY:HH:MM:SS -0400]`      
`DD` - Day of the month  
`MON` - Abbreviated name of the month   
`YYYY` - Calendar Year   
`HH:MM:SS` - Time of the days using a 24-hour clock    
`-0400` - Timezone or Locale    

	e.g., `[01/Aug/1995:00:00:02 -400]` 

* **HTTP request** in quotes. It consists of three parts:   
`HTTP method request` - GET, PUT, POST, HEAD, DELETE   
`Uniform Resource Identifier` -  /login, /   
`HTTP Version` - HTTP version used by the client

	e.g., `"POST /login HTTP/1.0"` 

* **HTTP reply code**  - 200, 304, 302, 404, 401, 403, 500, 501, 400  
	
	e.g.,   
`200` is for successful request.   
`401` is for unauthorized access or login failure.
			
* **bytes** bytes transferred or consumed by a resource in the reply.   
	e.g., 
`1420`- bytes consumed for /login request.

   

## Data Loading

### Parsing the log file
The log file is read line by line and regular expression is applied to match the above mentioned data fields from the log entry. All the regular expression matching records are stored in a list i.e. valid records and others are stored in separate list i.e. invalid records. The invalid records are written into `bad_records.txt` file for further analysis.

Regular expression used:
`([^\s]+).*?\[(.*)?\s(.*)?\][\s]+\"(.*)?\"[\s]+([^\s]+)[\s]+([^\s]+)`   

The parts of regular expression in parenthesis are the groups or request fields described above.

	Group 1 (host_name/IP address) `([^\s]+)` : Extracts everthing before the first space is encountered.
	Group 2 (timestamp without timezone) `\[(.*?)` : Does a greedy search for first space within the square brackets in order to get the timestamp without the timezone.   
	Group 3 (timezone) `(.*?)\]` : Gets the timezone.   
	Group 4 (HTTP request) `\"(.*)?\"` : Gets everything between the double quotes.    
	Group 5 (HTTP reply code) `([^\s]+)` : Gets the http reply code i.e. 200, 400, etc.    
	Group 6 (Bytes Transferred) `([^\s]+)` : Gets the bytes transferred for each request.   
	
The log data used for analysis consists of `4400644` lines. The regular expression is able to parse all the records successfully.

`Total records : 4400644 | Valid records  : 4400644 | Invalid records : 0`  

### Loading into pandas dataframe
The valid records list generated after parsing the log file is then loaded into pandas dataframe. pandas dataframe provide very useful and powerful inbuilt functions and tools for data analysis.

The column headers are specified for all the columns to allow us to query later using the column name. Once the data is loaded into dataframe, we need to some preprocessing and data cleaning.

- Update the '-' values in `bytes_transferred` columns to 0 and update the column datatype to float64.
- Convert the extracted timestamp format to pandas datetime format `%d/%b/%Y:%H:%M:%S`     
- Generate `http_method` and `uri` columns from the `http_request` column by splitting the `http_request` column values by space. Some of the http requests have http request method and HTTP version missing, so only URI column is updated and others are left blank.   
	e.g.;   `'klothos.crl.research.digital.com - - [10/Jul/1995:16:45:50 -0400] "\x05\x01" 400 -'`   
- Added a log_entry column containing the complete log line read from the server log file.   
- Filter out the rows with empty http_request field.

Dataframe datatypes:

`print (df_log_data.dtypes)`

	host_name                    object
	timestamp            datetime64[ns]
	timezone                     object
	http_request                 object
	http_status_code             object
	bytes_transferred           float64
	log_entry                    object
	http_method                  object
	uri                          object
	dtype: object


Dataframe Values:

	host_name                                                 199.72.81.55
	timestamp                                          1995-07-01 00:00:01
	timezone                                                         -0400
	http_request                             GET /history/apollo/ HTTP/1.0
	http_status_code                                                   200
	bytes_transferred                                                 6245
	log_entry            199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] ...
	http_method                                                        GET
	uri                                                   /history/apollo/



This dataframe will be used throughout the code for various features implementation.   


## Features Implementation
For feature implementation, below variables have been used to define the various method parameters. These allow us to extend the code to extract and analyze different types of similar features by tuning parameters and making updates only at one place.  

	NUM_OF_ACTIVE_HOSTS = 10
	NUM_OF_TOP_RESOURCES = 10
	NUM_OF_BUSIEST_PERIODS = 10
	BUSY_PERIOD_WINDOW = 60
	BLOCK_WINDOW_MIN = 5
	LOGIN_FAILURES_LIMIT = 3
	LOGIN_FAILURES_WINDOW_SEC = 20
	
For e.g.,    
`NUM_OF_ACTIVE_HOSTS` - defines number of top active hosts required for feature 1.    
`LOGIN_FAILURES_LIMIT` - defines the consecutive login failures limit.    
`BLOCK_WINDOW_TIME` - defines the time for which the potential attempts to be blocked.     

### Feature 1
List the top 10 most active host/IP addresses that have accessed the site.    

#### Implementation
To implement this feature, value_counts() function avialable in pandas dataframe is used. The value_counts() function groups the dataframe rows based on a key and sorts the rows based on the frequency count of each key in descending order. In our case, the key is host_name column values. Once the new frequency count dataframe is generated, iteration over top 10 rows is done to get a list of most active hosts along with frequency counts separated by comma. The list is then written into `hosts.txt` file. 


Top 10 active hosts `cat hosts.txt` :      

	piweba3y.prodigy.com,22309  
	piweba4y.prodigy.com,14903
	piweba1y.prodigy.com,12876
	siltb10.orl.mmc.com,10578
	alyssa.prodigy.com,10184
	edams.ksc.nasa.gov,9095
	piweba2y.prodigy.com,7961
	163.206.89.4,6520
	www-d3.proxy.aol.com,6299
	vagrant.vf.mmc.com,6096


### Feature 2
Identify the 10 resources that consume the most bandwidth on the site

#### Implementation
To implement this feature, groupby() in combination with sum() function is used. The groupby() function creates a grouped object based on a key i.e. `uri` column values and then sum() function aggregates the values over a particular group key i.e. `bytes_transferred` column values. From this grouped object, a dataframe is created with resource and the bandwidth consumed by that resource and sorted in descending order based on bandwidth consumed. Using this dataframe, a list of top 10 resources is extracted and written to `resources.txt` file. 

Top 10 resources `cat resources.txt` :

	/shuttle/missions/sts-71/movies/sts-71-launch.mpg
	/
	/shuttle/missions/sts-71/movies/sts-71-tcdt-crew-walkout.mpg
	/shuttle/missions/sts-53/movies/sts-53-launch.mpg
	/shuttle/countdown/count70.gif
	/shuttle/missions/sts-71/movies/sts-71-hatch-hand-group.mpg
	/shuttle/technology/sts-newsref/stsref-toc.html
	/shuttle/countdown/video/livevideo2.gif
	/shuttle/countdown/count.gif
	/shuttle/countdown/video/livevideo.gif



### Feature 3
List the top 10 busiest (or most frequently visited) 60-minute periods

#### Implementation
To implement this feature, the rolling() window function along with sum() and shift() is used. The rollling window function allows to aggregate the values over the given time window for every row. However, the rolling function is left aligned i.e. it sums the values ending at a timestamp but sum of requests starting from timestamp till the window period are required. In order to achieve this, shift function is used to shift the rows by the length of window period. The sum function aggregates all the frequency counts in the window period.

##### Visits per timestamp
Like feature 1, value_counts() function is used to get number of visits for each timestamp and added as a new column in the frequency count dataframe. While calling rolling sum function, values in number of visits column are aggregated. 

##### Reindexing
Since the windows could start from any timestamp, not necessarily when the event has occurred, reindexing is done based on timestamp to fill in missing timestamp gaps. The minimum and maximum timestamp value is extracted from the frequency dataframe and a new index range is created using `date_range` function. Then `reindex` function is used and new index range values are used. For timestamps with no events, the frequency count is filled as 0.

##### Rolling sum
As described above, the rolling sum along with shift is taken over the reindexed dataframe and aggregated values are added in new column `window_period_visits`. Due to shift function, the last n records, where n is shift window period will be set as NaN. In order to update the NaN, another loop is executed for last n records and values are summed over `num_vists` column starting from the record till the end of dataframe.

##### Formatting and writing the output
The dataframe is then sorted based on `window_period_visits` in descending order. The timestamp is converted back to original time format and timezone is appended to it. Finally, a list with complete timestamp along with `window_period_visits` is appended to list and then written to `hours.txt` file.

Top 10 busiest hours `cat hours.txt`:
	
	13/Jul/1995:08:59:33 -0400,35027
	13/Jul/1995:08:59:39 -0400,35019
	13/Jul/1995:08:59:40 -0400,35019
	13/Jul/1995:08:59:35 -0400,35015
	13/Jul/1995:08:59:34 -0400,35014
	13/Jul/1995:08:59:41 -0400,35013
	13/Jul/1995:08:59:32 -0400,35012
	13/Jul/1995:08:59:42 -0400,35011
	13/Jul/1995:08:59:36 -0400,35008
	13/Jul/1995:08:59:38 -0400,35007


### Feature 4
Detect patterns of three failed login attempts from the same IP address over 20 seconds so that all further attempts to the site can be blocked for 5 minutes. Log those possible security breaches.

#### Implementation
To implement this feature, first the filtered list of hosts with 3 or more than 3 login failure attempts is extracted. And then attempts for these individuals hosts are checked for 3 consecutive login failures within 20 second period, if found then attempts for next 5 minute window are recorded.

##### Filter hosts
First step is to filter the list of hosts with 3 or more than 3 login failure attempts is extracted. All the records from dataframe with `http_status_code == '401'` i.e. status code for failed login are filtered. Then value_count function is used to get the number of failed attempts for individual host_name. Only the hosts with count greater than or equal to 3 are retained and rest are filtered out. This step reduces the size of our data for analysis significantly and speeds up the analysis process.

##### Fetch filtered hosts dataframe 
The filtered host list is then used to fetch the rows from the original dataframe corresponding to these hosts using isin() function.

##### Getting blocked attempts and writing the output
For every host in the filtered hosts list, the rows corresponding to that host are fetched from the filtered hosts dataframe and sorted based on timestamp. A loop is executed to iterate over each row in the filtered hosts dataframe. Within loop a sliced dataframe of size 3 i.e. consecutive login failure limit is created. All the consecutive login failure conditions are checked on this sliced dataframe. If all conditions are met, then another while loop is executed to record all the blocked attempts for next 5 mins in `blocked_records` list, else the outer loop is iterated over next set of rows. Once the blocked_records list is obtained, then it is written to `blocked.txt`.

Potential blocked attempts `head blocked.txt`:

	207.125.54.37 - - [01/Jul/1995:20:50:15 -0400] "POST /login HTTP/1.0" 401 1420
	207.125.54.37 - - [01/Jul/1995:20:50:16 -0400] "GET / HTTP/1.0" 200 7074
	207.125.54.37 - - [01/Jul/1995:20:50:17 -0400] "GET /shuttle/missions/51-l/51-l-patch-small.gif HTTP/1.0" 200 10495
	207.133.42.32 - - [07/Jul/1995:05:46:28 -0400] "POST /login HTTP/1.0" 401 1420
	207.133.42.32 - - [07/Jul/1995:05:46:29 -0400] "GET / HTTP/1.0" 200 7074
	207.133.42.32 - - [07/Jul/1995:05:46:30 -0400] "GET /images/ksclogo-medium.gif HTTP/1.0" 200 5866
	207.140.62.73 - - [02/Jul/1995:17:13:20 -0400] "POST /login HTTP/1.0" 401 1420
	207.140.62.73 - - [02/Jul/1995:17:13:21 -0400] "GET / HTTP/1.0" 200 7074
	207.140.62.73 - - [02/Jul/1995:17:13:22 -0400] "GET /shuttle/missions/sts-71/images/KSC-95EC-0423.gif HTTP/1.0" 200 64939
	207.147.82.83 - - [16/Jul/1995:08:30:49 -0400] "POST /login HTTP/1.0" 401 1420
	...


Total potential blocked attempts found `wc -l blocked.txt` : `1758`


#### Custom test_case for Feature 4

The below records are from the `log.txt` file present under `custom_tests`.

	199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:09 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:20 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:00:23 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:34 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:45 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:46 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:47 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:50 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:00:58 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:59 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:01:00 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:01:47 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:05:47 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:05:48 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:05:49 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:05:50 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:06:00 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:06:10 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:06:14 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:06:30 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:07:17 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:10:51 -0400] "POST /login HTTP/1.0" 401 1420
	
	
Expected output for above case:

	199.72.81.55 - - [01/Jul/1995:00:00:47 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:50 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:00:58 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:59 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:01:00 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:01:47 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:06:00 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:06:10 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:06:14 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:06:30 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:07:17 -0400] "POST /login HTTP/1.0" 401 1420

The above input log file tests various scenarios described in the [feature4.png](https://github.com/agoyal3/datainsight-coding-challenge/tree/master/images/feature4.png). 

##### Scenario 1
A successful login after two failed attempts resets the failure window.

	199.72.81.55 - - [01/Jul/1995:00:00:01 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:09 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:20 -0400] "POST /login HTTP/1.0" 200 1420
	
##### Scenario 2
Three consecutive login failures but outside 20 seconds time window.

	199.72.81.55 - - [01/Jul/1995:00:00:23 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:34 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:45 -0400] "POST /login HTTP/1.0" 401 1420

##### Scenario 3
Three consecutive login failures within 20 second window.

	199.72.81.55 - - [01/Jul/1995:00:00:34 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:45 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:46 -0400] "POST /login HTTP/1.0" 401 1420
	
Block attempts for next 5 mins until `01/Jul/1995:00:05:46 -0400`:
	
	199.72.81.55 - - [01/Jul/1995:00:00:47 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:50 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:00:58 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:00:59 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:01:00 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:01:47 -0400] "POST /login HTTP/1.0" 200 1420

The failure window resets from `01/Jul/1995:00:05:47 -0400` onwards so entries immediately following this timestamp are not logged.

##### Scenario 4
Again 3 consecutive failures after 5 minutes block attempts window.

	199.72.81.55 - - [01/Jul/1995:00:05:48 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:05:49 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:05:50 -0400] "POST /login HTTP/1.0" 401 1420

Block attempts for next 5 mins until `01/Jul/1995:00:010:50 -0400`:

	199.72.81.55 - - [01/Jul/1995:00:06:00 -0400] "POST /login HTTP/1.0" 200 1420
	199.72.81.55 - - [01/Jul/1995:00:06:10 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:06:14 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:06:30 -0400] "POST /login HTTP/1.0" 401 1420
	199.72.81.55 - - [01/Jul/1995:00:07:17 -0400] "POST /login HTTP/1.0" 401 1420
	
Last record falls outside the 5 minute window so its not recorded in the blocked attempts.



## Run the program

The repository directory structure :

    ├── README.md 
    ├── run.sh
    ├── src
    │   └── process_log.py
    ├── log_input
    │   └── log.txt
    ├── log_output
    |   └── hosts.txt
    |   └── hours.txt
    |   └── resources.txt
    |   └── blocked.txt
    ├── insight_testsuite
        └── run_tests.sh
        └── tests
            └── test_features
            |   ├── log_input
            |   │   └── log.txt
            |   |__ log_output
            |   │   └── hosts.txt
            |   │   └── hours.txt
            |   │   └── resources.txt
            |   │   └── blocked.txt
            ├── custom-tests
                ├── log_input
                │   └── log.txt
                |__ log_output
                    └── hosts.txt
                    └── hours.txt
                    └── resources.txt
                    └── blocked.txt
		    
Use below command from the main directory to run the program:    

`~$ ./run.sh`

or 

`~$ python ./src/process_log.py ./log_input/log.txt ./log_output/hosts.txt ./log_output/hours.txt ./log_output/resources.txt ./log_output/blocked.txt ./log_output/bad_records.txt`   

The process_log.py takes below command line arguments:    

	arg 0 (./src/process_log.py) : python source code file
	arg 1 (./log_input/log.txt) : input NASA web server log file
	arg 2 (./log_output/hosts.txt) : file to write the feature 1 i.e. top 10 active hosts
	arg 3 (./log_output/hours.txt) : file to write the feature 3 i.e. top busiest hours
	arg 4 (./log_output/resources.txt) : file to write the feature 2 i.e. top 10 resources based on bandwidth consumded
	arg 5 (./log_output/blocked.txt) : file to write the feature 4 i.e. blocked attempts
	arg 6 (./log_output/bad_records.txt) : file to write the records which were not parsed by the regular expression

Successful scenario output:
	
	Parsing the log file...
	Log file parsing completed!!
	Total records : 4400644 | Valid records  : 4400644 | Invalid records : 0

	Writing output to ../log_output/hosts.txt
	Output written successfully!!

	Writing output to ../log_output/resources.txt
	Output written successfully!!

	Writing output to ../log_output/hours.txt
	Output written successfully!!

	Writing output to ../log_output/blocked.txt
	Output written successfully!!

	--- 98.736390114 seconds ---

Few Failure scenarios:

	Missing command line arguments output:

		Missing command line arguments. 7 arguments expected and 1 provided.
		Example Usage : 
		 python ./src/process_log.py ./log_input/log.txt ./log_output/hosts.txt ./log_output/hours.txt ./log_output/resources.txt ./log_output/blocked.txt ./log_output/bad_records.txt



	Empty log file output:

		Parsing the log file...
		Log file parsing completed!!
		Total records : 0 | Valid records  : 0 | Invalid records : 0

		No records present in the log file for analysis.

### Testing the directory structure and output format

To test the correct directory structure and the format of the output files, run the test script, called `run_tests.sh` in the `insight_testsuite` folder.

The tests are stored as text files under the `insight_testsuite/tests` folder. All the tests (insight tests and custom tests) are in separate folders and within have a `log_input` folder for `log.txt` and a `log_output` folder for outputs corresponding to the current test.

Run the tests with the following from the `insight_testsuite` folder:

    insight_testsuite~$ ./run_tests.sh 

On success:

	Parsing the log file...
	Log file parsing completed!!
	Total records : 23 | Valid records  : 23 | Invalid records : 0

	Writing output to ../temp/log_output/hosts.txt
	Output written successfully!!

	Writing output to ../temp/log_output/resources.txt
	Output written successfully!!

	Writing output to ../temp/log_output/hours.txt
	Output written successfully!!

	Writing output to ../temp/log_output/blocked.txt
	Output written successfully!!

	--- 0.132741928101 seconds ---
	[PASS]: custom_tests (hosts.txt)
	[PASS]: custom_tests (resources.txt)
	[PASS]: custom_tests (hours.txt)
	[PASS]: custom_tests (blocked.txt)
	[Wed Apr  5 20:12:55 EDT 2017] 4 of 8 tests passed

	Parsing the log file...
	Log file parsing completed!!
	Total records : 10 | Valid records  : 10 | Invalid records : 0

	Writing output to ../temp/log_output/hosts.txt
	Output written successfully!!

	Writing output to ../temp/log_output/resources.txt
	Output written successfully!!

	Writing output to ../temp/log_output/hours.txt
	Output written successfully!!

	Writing output to ../temp/log_output/blocked.txt
	Output written successfully!!

	--- 0.0247581005096 seconds ---
	[PASS]: test_features (hosts.txt)
	[PASS]: test_features (resources.txt)
	[PASS]: test_features (hours.txt)
	[PASS]: test_features (blocked.txt)
	[Wed Apr  5 20:12:58 EDT 2017] 8 of 8 tests passed


## References

- [pandas official documentation](http://pandas.pydata.org/pandas-docs/stable/index.html)
