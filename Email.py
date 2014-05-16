#Xiaote Zhu
#Email.py

import string
from datetime import datetime,timedelta
import imaplib
import email
import ParseEmail
import Calendar
from email.parser import HeaderParser
import re

dictTimeRange={"morning":(0000,1200),"afternoon":(1200,1700),\
               "evening":(1700,2200),"night":(2000,500),\
               "default":(0700,2359)}

list_response_pattern = re.compile\
                    (r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')
def getMailboxes(mail):
    mailboxesInfo=mail.list()[1]
    mailboxes=[]
    for mailboxInfo in mailboxesInfo:
        flags, delimiter, mailbox_name = \
               list_response_pattern.match(mailboxInfo).groups()
        mailbox_name = mailbox_name.strip('"')
        mailboxes.append((mailbox_name,flags,delimiter))
    return mailboxes
#part of these codes are modified based on:
#http://pymotw.com/2/imaplib/

def getAllEmailID(mail):
    strIDs=mail.search(None,"ALL")[1][0]
    listIDs=strIDs.split(" ")
    return listIDs

def getUnreadEmailID(mail):
    strIDs=mail.search(None,"UnSeen")[1][0]
    listIDs=strIDs.split(" ")
    return listIDs

def getEmailBody(mail,emailID):
    emailStr=mail.fetch(emailID,"(RFC822)")[1][0][1]
    #get the email body as a string
    emailInstance=email.message_from_string(emailStr)
    #convert the string into an instance
    plainBody=[]
    for part in emailInstance.walk():
        if part.get_content_type() == 'text/plain':
            plainBody.append(part.get_payload())
    return plainBody
#part of these codes are modified based on:
#http://stackoverflow.com/questions/7519964/
#python-pull-back-plain-text-body-from-message-from-imap-account

def getHeader(mail,emailID):
    header=mail.fetch(emailID,"(BODY[HEADER])")[1][0][1]
    parser=HeaderParser()
    return parser.parsestr(header)

def getEmailSubject(header):
    return header["Subject"]

def getEmailDate(header):
    dateStr=header["Date"]
    dateList=dateStr.split(" ")
    return dateList
    #return a list of strings. eg.['Tue,', '19', 'Nov', '2013', '12:12:39',
    #'-0500']

def getEventList(mail,emailID,header):
    mailread=getEmailBody(mail,emailID)
    if len(mailread)>0:
        mailbody,mailsubject=mailread[0],getEmailSubject(header)
        sentences=[mailsubject]+ParseEmail.breakIntoSentences(mailbody)
        emailTime=getEmailDate(header)
        (date,time,timezone)=ParseEmail.parseHeaderDate(emailTime)
        year,dateTimeList,dateTimeLocDict=date[:4],[],dict()
        for i in xrange(len(sentences)):
            sentence=sentences[i]
            if sentence!=None and len(sentence)>0 and \
               ParseEmail.isPreviousMessage(sentence)==False and \
               ParseEmail.isPreviousHeader(sentence)==False:
                Date=ParseEmail.extractDates(sentence,year,date)
                Time=ParseEmail.extractTime(sentence)
                dateTimeList.extend(Date)
                dateTimeList.extend(Time)
                dateTimeList.sort()
                dateTimeList=takeOutOverlap(dateTimeList)
                dateTimeLocDict[i]=getLocationIn(dateTimeList,sentence)
            else:
                dateTimeLocDict[i]=[]
            dateTimeList=[]
        eventList=groupDateTimeLocation(dateTimeLocDict,date,mailsubject)
        eventList.sort()
        eventList=takeOutDuplicates(eventList)
        return eventList

def takeOutOverlap(dateTimeList):
    newDateTimeList=[]
    for i in xrange(len(dateTimeList)):
        sIndex,eIndex=dateTimeList[i][0]
        category=dateTimeList[i][1]
        if i>0 and dateTimeList[i-1]!="deleted" and \
           sIndex<dateTimeList[i-1][0][1]:
    #part of a string that fits date format might also fits time format, the
    #assumption is the date information extraction is probably more accurate
    #in this case, so the other one will be taken out
            if dateTimeList[i-1][1]=="date" and category=="time":
                dateTimeList[i]="deleted"
            elif category=="date" and dateTimeList[i-1][1]=="time":
                dateTimeList[i-1]="deleted"
        elif category=="date?":
    #if two date information are close to each other in a sentence and one is
    #extracted from words like "Thursday" and the other is extracted from words
    #like "Nov", the assumption is that the one with month name is more accurate
    #and the other one will be taken out
            if i+1<len(dateTimeList) and dateTimeList[i+1][1]=="date" and\
               dateTimeList[i+1][0][0]-eIndex<=2:
                #possibly these two are talking about the same date
                dateTimeList[i+1][0]=(sIndex,dateTimeList[i+1][0][1])
                dateTimeList[i]="deleted"
            elif i>0 and dateTimeList[i-1][1]=="date" and\
                 sIndex-dateTimeList[i-1][0][1]<=2:
                #possible these two are talking about the same date
                dateTimeList[i-1][0]=(dateTimeList[i-1][0][0],eIndex)
                dateTimeList[i]="deleted"
    for item in dateTimeList:
        if item!="deleted":
            newDateTimeList.append(item)
    return newDateTimeList

def getLocationIn(dateTimeList,sentence):
    #parse each segment of the sentence to get locations and insert the
    #locations into "dateTimeList" based on their order in the sentence
    dateTimeLocationList=[]
    if len(dateTimeList)>0:
        for i in xrange(len(dateTimeList)):
            if i==0:
                eIndex=dateTimeList[i][0][0]
                segment=string.strip(sentence[:eIndex])
                if len(segment)>0:
                    dateTimeLocationList.extend\
                                    (ParseEmail.extractLocation(segment))
                dateTimeLocationList.append(dateTimeList[i])
            else:
                sIndex,eIndex=dateTimeList[i-1][0][1],dateTimeList[i][0][0]
                segment=string.strip(sentence[sIndex:eIndex])
                if len(segment)>0:
                    dateTimeLocationList.extend\
                                    (ParseEmail.extractLocation(segment))
                dateTimeLocationList.append(dateTimeList[i])
            if i==len(dateTimeList)-1:
                sIndex=dateTimeList[i][0][1]
                segment=string.strip(sentence[sIndex:])
                if len(segment)>0:
                    dateTimeLocationList.extend\
                                    (ParseEmail.extractLocation(segment))
    else:
        sentence=string.strip(sentence)
        if len(sentence)>0:
            dateTimeLocationList.extend(ParseEmail.extractLocation(sentence))
    return dateTimeLocationList

def takeOutDuplicates(eventList):
    #take out events that have idential information
    #if two events happen at the same time, the one with missing information
    #is also taken out
    for i in xrange(len(eventList)):
        if i+1<len(eventList):
            if eventList[i][1]==eventList[i+1][1] and \
               eventList[i][2]==eventList[i+1][2]:
                #these two talk about events that happen at exactly the same
                #time
                if eventList[i][3]==None:
                    #missing location
                    eventList[i]=eventList[i+1]
                elif eventList[i+1][3]==None:
                    #missing location
                    eventList[i+1]=eventList[i]
    eventList=list(set(eventList))
    return eventList
    
def groupDateTimeLocation(dateTimeLocDict,sentDate,mailsubject):
    #whenever the function finds a list that contains time info, it searches for
    #the closest three lists that contian date, AMPM and location info in the
    #same sentence.
    #if date info is not present in the given sentence, the lastSeenDate, if
    #present, is considered the default date for the time found.
    eventList,lastSeenDate=[],None
    for key in xrange(len(dateTimeLocDict)):
        dateTimeLocList=dateTimeLocDict[key]
        for i in xrange(len(dateTimeLocList)):
            itemInfo=dateTimeLocList[i]
            if itemInfo[1]=="time":
                dateAInfo,locAInfo,AMPMAInfo=lookBefore(dateTimeLocList)
                dateBInfo,locBInfo,AMPMBInfo=lookAfter(dateTimeLocList)
                sIndex,eIndex=itemInfo[0]
                dateInfo=pickOne(dateAInfo,dateBInfo,sIndex,eIndex,"A")
                locInfo=pickOne(locAInfo,locBInfo,sIndex,eIndex,"B",False)
                AMPMInfo=pickOne(AMPMAInfo,AMPMBInfo,sIndex,eIndex,"A")
                if locInfo!=None:
                    loc=locInfo[1][0]
                else:
                    loc=None
                if dateInfo==None:
                    dateInfo=lastSeenDate
                    if dateInfo!=None and AMPMInfo==None:
                        AMPMInfo=lookBefore(dateTimeLocDict[lastSeenDateKey])[2]
                if dateInfo!=None and AMPMInfo!=None:
                    dateInfo.append(AMPMInfo[2])
                result=finalCheckTimeDate(itemInfo[2],dateInfo,sentDate)
                if result!=None:date,time=result
                if time!=None:
                    sConvert=convertDateTime(date[0],time[0])
                    eConvert=convertDateTime(date[1],time[1])
                    eventList.append((mailsubject,sConvert,eConvert,loc))
            elif itemInfo[1]=="date":
                lastSeenDate,lastSeenDateKey=itemInfo,key
    return eventList

def convertDateTime(date,time=None):
    if time==None:
        return "%s-%s-%s"  %(date[:4],date[4:6],date[6:])
    else:
        return "%s-%s-%sT%s:%s:00.000" %(date[:4],date[4:6],date[6:],time[:2],\
                                         time[2:])

def pickOne(infoA,infoB,sIndex,eIndex,prefer,indexExists=True):
    if infoA!=None and infoB!=None:
        if indexExists:
            diffA=sIndex-infoA[0][1]
            diffB=infoB[0][0]-eIndex
        else:
            diffA=infoA[0]
            diffB=infoB[0]
        if prefer=="A":
            return pickOneHelper(infoA,infoB,diffA,diffB)
        elif prefer=="B":
            return pickOneHelper(infoB,infoA,diffB,diffA)
    elif infoA!=None:
        return infoA
    elif infoB!=None:
        return infoB

def pickOneHelper(infoA,infoB,diffA,diffB):
    #give priority to infoA
    if diffA>diffB:
        return infoB
    else:
        return infoA

def finalCheckTimeDate(timeInfo,dateInfo,sentDate):
    sTime,eTime=timeInfo[0],timeInfo[2]
    if dateInfo!=None:
        sDate=eDate=dateInfo[2]
    else:
        sDate=eDate=sentDate
    if "Unsure" not in timeInfo:
        finalDateTime=finalCheckTime(sDate,eDate,sTime,eTime)
        return finalDateTime
    elif dateInfo!=None and len(dateInfo)>3:
        timeRange=dictTimeRange[dateInfo[3]]
        if dateInfo[3]=="night":
            (sDate,eDate),(sTime,eTime)=changeToNight(timeRange,timeInfo,sDate)
            finalDateTime=finalCheckTime(sDate,eDate,sTime,eTime)
            return finalDateTime
        else:
            (sDate,eDate),(sTime,eTime)=changeIntoRange\
                                         (timeRange,timeInfo,sDate)
            finalDateTime=finalCheckTime(sDate,eDate,sTime,eTime)
            return finalDateTime
    else:
        timeRange=dictTimeRange["default"]
        (sDate,eDate),(sTime,eTime)=changeIntoRange(timeRange,timeInfo,sDate)
        finalDateTime=finalCheckTime(sDate,eDate,sTime,eTime,True)
        return finalDateTime

                
def finalCheckTime(sDate,eDate,sTime,eTime,changeTime=False):
    if eTime=="":
        eDate,eTime=addHours(sDate,sTime,1)
        #default for an event is one hour
        return ((sDate,eDate),(sTime,eTime))
    else:
        if int(sDate+sTime)>=int(eDate+eTime):
            if changeTime==True and int(eTime[:2])<12:
                eTime=str(int(eTime[:2])+12)+eTime[2:]
            else:
                #not sure why an event ends before it starts
                #right now assume this is wrong
                return None
        if int(sDate+sTime)<int(eDate+eTime):
            return ((sDate,eDate),(sTime,eTime))

def changeIntoRange(timeRange,timeInfo,sDate):
    lBound,uBound=timeRange
    sTime,eTime=timeInfo[0],timeInfo[2]
    eDate=sDate
    if timeInfo[1]=="Unsure":
        if lBound>int(sTime):
            (sDate,sTime)=addHours(sDate,sTime,12)
    if eTime!="" and timeInfo[3]=="Unsure":
        if lBound>int(eTime):
            (eDate,eTime)=addHours(eDate,eTime,12)
    return ((sDate,eDate),(sTime,eTime))

def addHours(date,time,hour):
    dateTime=datetime.strptime(date+time,"%Y%m%d%H%M")
    dateTime+=timedelta(hours=hour)
    year,month,day=str(dateTime.year),str(dateTime.month),str(dateTime.day)
    hour,minute=str(dateTime.hour),str(dateTime.minute)
    if len(month)==1:
        month="0"+month
    if len(day)==1:
        day="0"+day
    if len(hour)==1:
        hour="0"+hour
    if len(minute)==1:
        minute="0"+minute
    date=year+month+day
    time=hour+minute
    return (date,time)
  
def changeToNight(timeRange,timeInfo,sDate):
    lBound,uBound=timeRange   
    sTime,eTime=timeInfo[0],timeInfo[2]
    eDate=sDate
    if timeInfo[1]=="Unsure":
        if uBound<int(sTime)<lBound:
            (sDate,sTime)=addHours(sDate,sTime,12)
        elif int(sTime)<=uBound:
            (sDate,sTime)=addHours(sDate,sTime,24)
    if eTime!="" and timeInfo[3]=="Unsure":
        if uBound<int(eTime)<lBound:
            (eDate,eTime)=addHours(eDate,eTime,12)
        elif int(eTime)<=uBound:
            (eDate,eTime)=addHours(eDate,eTime,24)
    return ((sDate,eDate),(sTime,eTime))
                    
def lookBefore(dateTimeLocList):
    #searching date, loc and AMPM infos backwards
    dateFound=locFound=AMPMFound=None
    for i in xrange(len(dateTimeLocList)-1,-1,-1):
        item=dateTimeLocList[i]
        if dateFound==None and item[1][:4]=="date":
            dateFound=item
        elif locFound==None and item[1]=="location":
            locFound=(i,item)
        elif AMPMFound==None and item[1]=="AMPM":
            AMPMFound=item
        if dateFound!=None and locFound!=None and AMPMFound!=None:
            return dateFound,locFound,AMPMFound
    return dateFound,locFound,AMPMFound

def lookAfter(dateTimeLocList):
    #searching date, loc and AMPM infos forwards
    dateFound=locFound=AMPMFound=None
    for i in xrange(len(dateTimeLocList)):
        item=dateTimeLocList[i]
        if dateFound==None and item[1][:4]=="date":
            dateFound=item
        elif locFound==None and item[1]=="location":
            locFound=(i,item)
        elif AMPMFound==None and item[1]=="AMPM":
            AMPMFound=item
        if dateFound!=None and locFound!=None and AMPMFound!=None:
            return dateFound,locFound,AMPMFound
    return dateFound,locFound,AMPMFound      

def checkAccount(username,password):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        mail.login(username,password)
        mailboxes=getMailboxes(mail)
        return mail,mailboxes
    except:
        return None

def run(mail,mailbox):
    mail.select(mailbox)
    unreads=getUnreadEmailID(mail)
    finalEventList=[]
    if unreads==['']:
       return "No Unread"
    else:
        for i in unreads:
            header=getHeader(mail,i)
            subject=getEmailSubject(header)
            eventList=getEventList(mail,i,header)
            if eventList!=None:
                finalEventList.extend(eventList)
        return finalEventList
    
    
