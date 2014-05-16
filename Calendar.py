#Xiaote Zhu
#Calendar.py

import argparse
import httplib2
import os
import sys

from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
    
#########All the codes below is borrowed from Google sample file###########
#########################(with slight modification)########################
def checkAccount(username):
    # Parser for command-line arguments.
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[tools.argparser])

    # CLIENT_SECRETS is name of a file containing the OAuth 2.0 information for
    # this application, including client_id and client_secret. You can see the
    # Client ID and Client secret on the APIs page in the Cloud Console:
    # <https://cloud.google.com/console#/project/39017739811/apiui>
    CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), \
                                  'client_secrets.json')

    # Set up a Flow object to be used for authentication.
    # Add one or more of the following scopes. PLEASE ONLY ADD THE SCOPES YOU
    # NEED. For more information on using scopes please see
    # <https://developers.google.com/+/best-practices>.
    FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
      scope=[
          'https://www.googleapis.com/auth/calendar'
        ],
        message=tools.message_if_missing(CLIENT_SECRETS))

    argv=sys.argv
    
    # Parse the command-line flags.
    flags = parser.parse_args(argv[1:])

    # If the credentials don't exist or are invalid run through the native
    # client flow. The Storage object will ensure that if successful the good
    # credentials will get written back to the file.

    fileName='%s.dat'%username
    storage = file.Storage(fileName)
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(FLOW, storage, flags)

    # Create an httplib2.Http object to handle our HTTP requests and authorize
    # it with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    service = discovery.build('calendar', 'v3', http=http)

    return service

#########All the codes above is borrowed from Google sample file###########
#########################(with slight modification)########################
def getCalendarTimeZone(service,calendarId="primary"):
    calendar_list_entry=\
            service.calendarList().get(calendarId=calendarId).execute()
    return calendar_list_entry['timeZone']

def getAllEventsDateTime(service,calendarId="primary",page_token=None):
    dateTimeList=[]
    events=\
    service.events().list(calendarId=calendarId,pageToken=page_token).execute()
    for event in events["items"]:
    #cited from
    #https://developers.google.com/google-apps/calendar/v3/reference/events/list
        dateTimeList.append((event["start"]["dateTime"][:-6]+".000",\
                             event["end"]["dateTime"][:-6]+".000"))
    return dateTimeList

def createEvent(timeZone,dateTimeList,service,summary,start,end,location=None,
                calendarId="primary"):
    if (start,end) not in dateTimeList:
        if len(start)==10:
            event={"summary":summary,
               "location":location,
               "start":{'date':start,"timeZone":timeZone},
               "end":{'date':end,"timeZone":timeZone}}
        else:
            event={"summary":summary,
                   "location":location,
                   "start":{'dateTime':start,"timeZone":timeZone},
                   "end":{'dateTime':end,"timeZone":timeZone}}
        service.events().insert(calendarId=calendarId,body=event).execute()
        return True

def createEvents(service,eventList):
    defaultTZ=getCalendarTimeZone(service)
    dateTimeList=getAllEventsDateTime(service)
    createdEvents=[]
    for event in eventList:
        if createEvent(defaultTZ,dateTimeList,service,event[0],event[1],\
                       event[2],event[3]):
            sDate="%s/%s/%s"%(event[1][5:7],event[1][8:10],event[1][:4])
            sTime=event[1][11:16]
            eDate="%s/%s/%s"%(event[2][5:7],event[2][8:10],event[2][:4])
            eTime=event[2][11:16]
            if sDate==eDate:
                displayList=["Subject: %s"%event[0],\
                             "Date: %s"%sDate,"Time: %s - %s"%(sTime,eTime)]
            else:
                displayList=["Subject: %s"%event[0],\
                             "Date: %s - %s"%(sDate,eDate),
                             "Time: %s - %s" %(sTime,eTime)]
            loc=event[3]
            if loc!=None:
                displayList.append("Location: %s"%loc)
            createdEvents.append(displayList)
    return createdEvents
