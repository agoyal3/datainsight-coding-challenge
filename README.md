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
5. [Execution](README.md#execution)


## Introduction
This repository contains the source code for the DataInsight Coding Challenge. The original code challenge description 
could be found [here](challenge-description.md). The overview of the challenge is to perform basic analytics on the NASA web server log file, provide useful metrics, and implement basic security measures.

### Pre-requisites
- Python 2.7 or later  
	The code has been written and tested on Ubuntu 16.04 using Python 2.7. 
	
- [pandas v0.19.2](http://pandas.pydata.org/pandas-docs/stable/)  
	pandas is a Python package which provides fast, flexible, and expressive data structures designed to make working with “relational” or “labeled” data both easy and intuitive. It aims to be the fundamental high-level building block for doing practical, real world data analysis in Python. 
	
	The package can be installed in different ways, as described [here](http://pandas.pydata.org/pandas-docs/stable/install.html).   
	
	Install using pip command:

		pip install pandas
	 
## Dataset
NASA web server logs data can be downloaded from [here](https://drive.google.com/file/d/0B7-XWjN4ezogbUh6bUl1cV82Tnc/view).

The log data is in ASCII format with one line per request. Below are two sample records from the logs:

    208.271.69.50 - - [01/Aug/1995:00:00:02 -400] "POST /login HTTP/1.0" 401 1420
    uplherc.upl.com - - [01/Aug/1995:00:00:07 -0400] "GET / HTTP/1.0" 304 0

- **host** making the request  
`208.271.69.50` and `uplherc.upl.com` are the hosts making the request. A hostname when possible, otherwise the Internet address if the name could not be looked up.

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
			
* **bytes** bytes transferred or consumed by that resource in the reply.   
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
The valid records list is then loaded into pandas dataframe for feature extraction. pandas dataframe provide very useful inbuilt functions and tools for data analysis.

The column headers are specified for all the columns to allow us to query later using the column name. Once the data is loaded into dataframe, we need to some preprocessing and data cleaning.

- Update the '-' values in `bytes_transferred` columns to 0 and update the column datatype to float64.
- Convert the extracted timestamp format to pandas datetime format `%d/%b/%Y:%H:%M:%S`     
- Generate `http_method` and `uri` columns from the `http_request` column by splitting the `http_request` column values by space. Some of the http requests have http request method and HTTP version missing, so only URI column is updated and others are left blank. e.g.;   `'klothos.crl.research.digital.com - - [10/Jul/1995:16:45:50 -0400] "\x05\x01" 400 -'`   

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






