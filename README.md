# Weather History Canada Web App

Weather History Canada is an open source web application tool for accessing historical 
weather data from over 8000 active and inactive Environment and Climate Change Canada 
(ECCC) maintained weather stations going as far back as 1840. With a few clicks of the 
mouse you can search, download, and visualize hourly, daily, and monthly ECCC weather data 
for any desired record length. The goal of Weather History Canada is to better the user 
experience by making it easier and quicker to download and interpret large amounts of 
historical weather data. 


[CLICK HERE TO VISIT SITE](http://www.weatherhistorycanada.com)

### Key Features
 
- Built in pure Python using Plotly Dash and deployed to a Heroku free dyno
- Periodic URL request via AWS Lambda to avoid sleeping of free dynos (i.e. quick load times)
- Map based searching and realtime filtering of weather stations based on multiple
criterion
- Execution of long-running tasks as background jobs via Celery and Heroku Redis to avoid 
Heroku request timeouts 
- Handles concurrent download requests via execution of tasks in Celery using Gunicorn 
Gevent worker class
- No file storage on disk. Downloads are stored on AWS S3 and delivered on request via
pre-signed URL
- Interactive graphing and figure capture to quickly visualize and share data
- Multi-browser functionality. Manually tested on Chrome 78, IE11, Firefox 68, and Safari 
10.1


### What do the files do

[app.py](https://github.com/david-hurley/env-can-wx-app/blob/master/app.py)




web app to download wx data from env can
-metadata of stations added
