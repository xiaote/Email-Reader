#Xiaote Zhu
#Parse Email.py

from datetime import datetime,timedelta
import nltk
import string
from nltk.tokenize import sent_tokenize,word_tokenize
from nltk.tag import pos_tag
import re

listMonths=["january","february","march","april","may","june","july","august",
"september","october","november","december","jan","feb","mar","apr","jun","jul",
"aug","sept","oct","nov","dec"]

listDays=["monday","tuesday","wednesday","thursday","friday","saturday",
"sunday","mon","tues","wed","thur","fri","sat","sun"]

dictMonConvert={"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
"jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,"sept":9,"oct":10,
"nov":11,"dec":12}

dictDayConvert={"monday":1,"tuesday":2,"wednesday":3,"thursday":4,"friday":\
5,"saturday":6,"sunday":0,"mon":1,"tues":2,"wed":3,"thur":4,"thurs":4,\
"fri":5,"sat":6,"sun":0}

def createDict(Set):
    #create a dictionary out of a list based on the length of the elements in
    #the list
    Dict=dict()
    for element in Set:
        if len(element) in Dict:
            Dict[len(element)].add(element)
        else:
            Dict[len(element)]=set([element])
    return Dict

dictMonths=createDict(listMonths)
dictDays=createDict(listDays)

def breakIntoSentences(text):
    listOfSentences=sent_tokenize(text)
    result=[]
    for sent in listOfSentences:
        sent=sent.replace("\r\n"," ")
        sent=sent.replace("*","")
        sent=sent.replace("= ","")
        result.append(sent)
    return result

def breakIntoWords(sentence):
    return word_tokenize(sentence)

def tagSentence(sentence):
    words=breakIntoWords(sentence)
    return pos_tag(words)

def leadingNumbers(String):
    #return the string of number which starts from the first element in the
    #given string and ends before the first nonnumeric element in the given
    #string will return an empty string if the given string does not start with
    #a number
    result=""
    for element in String:
        if element in string.digits:
            result+=element
        else:
            return result
    return result

def isPreviousMessage(sentence):
    check=re.search(r"(>)+ (>)+ (>)+",sentence)
    return check!=None

def isPreviousHeader(sentence):
    check=re.search(r"(-)+ Forwarded message (-)+",sentence)
    return check!=None

def findTimeIndices(sentence):
    hour=r"\d{1,2}"
    minute=r"(\s?[:]\s?\d{2})"
    AMPM=r"(\s?[aApP][.]?[mM][.]?)"
    TO=r"(\s?(to|-)\s?)"
    indices=[]
    pattern0=hour+minute+AMPM+"?"+TO+hour+minute+"?"+AMPM+"?"
    #start time with optional AMPM, end time with optional minute, optional AMPM
    checkColon0=re.finditer(pattern0,sentence)
    for m in checkColon0:
        indices.append((m.start(0),m.end(0)))
        #cited from: http://stackoverflow.com/questions/3519565/
        #find-the-indexes-of-all-regex-matches-in-python
    pattern1=hour+AMPM+"?"+TO+hour+minute+AMPM+"?"
    #start time with no minute and optional AMPM, end time with optional AMPM
    checkColon1=re.finditer(pattern1,sentence)
    for m in checkColon1:
        indices.append((m.start(0),m.end(0)))
    pattern2=hour+minute+AMPM+"?"
    #start time with optional AMPM
    checkColon2=re.finditer(pattern2,sentence)
    for m in checkColon2:
        indices.append((m.start(0),m.end(0)))
    pattern3=hour+AMPM+"?"+"("+TO+hour+")"+"?"+AMPM
    #start time, optional end time, at least one AMPM
    checkAMPM=re.finditer(pattern3,sentence)
    for m in checkAMPM:
        indices.append((m.start(0),m.end(0)))
    indices.sort()
    indices=checkOverlap(indices)
    indices.sort()
    return indices

def checkOverlap(indexList):
    for i in xrange(len(indexList)):
        if i!=0:
            if indexList[i][1]<=indexList[i-1][1]:
                #end index is smaller or equal to the previous one but start
                #index is bigger
                indexList[i]=indexList[i-1]
        if i+1!=len(indexList):
            if indexList[i][0]==indexList[i+1][0]:
                #start index is the same as later one which indicates the end
                #index is smaller
                indexList[i]=indexList[i+1]
    return list(set(indexList))
    
def extractTime(sentence):
    indices=findTimeIndices(sentence)
    timeList=[]
    for timeIndex in indices:
        (sIndex,eIndex)=timeIndex
        timeString=sentence[sIndex:eIndex]
        if (sIndex==0 or re.match(r"\W",sentence[sIndex-1])) and \
           (eIndex==len(sentence) or re.match(r"\W",sentence[eIndex])):
            #make sure the start/end of the timeString is either the start/end
            #of a sentence or the start/end of a word.
            timeString=sentence[sIndex:eIndex]
            timeString=timeString.replace(" ","")
            #take out the spaces for easier parsing
            time=extractTimeFromString(timeString)
            if time!=False:
                timeList.append([timeIndex,"time",time])
    return timeList

def extractTimeFromString(timeString):
    sTimeKnown,sTime,sAMPM=False,"","Unsure"
    eTimeKnown,eTime,eAMPM=False,"","Unsure"
    #sTimeKnown, eTimeKnown takes record which information the program is
    #extracting
    examineMinute,examineEndTime=False,False
    for char in timeString:
        if char.isdigit():
            if sTimeKnown==False:sTime+=char
            elif eTimeKnown==False:eTime+=char
        elif char==":":
            examineMinute,digitCount=True,0
            #":" indicates the number after it is probably "the minute"
            if sTimeKnown==False:
                (sTime,sAMPM)=checkHour(sTime,sAMPM)
                #make sure "the hour" is in the correct form first
                if sTime==False: return False
            elif eTimeKnown==False:
                (eTime,eAMPM)=checkHour(eTime,eAMPM)
                if eTime==False: return False
        elif char=="a" or char=="A":
            if sTimeKnown==True:
                if examineEndTime==False:sAMPM="AM"
                else:eAMPM="AM"
            elif sTimeKnown==False:
                (sTime,sAMPM)=checkHour(sTime,sAMPM)
                #we find sAMPM without finding sMinute, so the hour has not
                #been checked yet
                if sTime==False: return False
                sTime,sTimeKnown,sAMPM=addDefaultMinute(sTime),True,"AM"
        elif char=="p" or char=="P":
            if sTimeKnown==True:
                if examineEndTime==False:sAMPM="PM"
                else:eAMPM="PM"
            elif sTimeKnown==False:
                (sTime,sAMPM)=checkHour(sTime,sAMPM)
                if sTime==False:return False
                sTime,sTimeKnown,sAMPM=addDefaultMinute(sTime),True,"PM"
        elif char=="-" or char=="o":
            if len(sTime)<=2:
                #"-" and "o" (part of "to") indicates the number after it is
                #probably "the end time"
                #we don't know sMinute yet, so the hour has not been checked
                (sTime,sAMPM)=checkHour(sTime,sAMPM)
                if sTime==False:return False
                sTime,sTimeKnown=addDefaultMinute(sTime),True
            examineEndTime=True
        if examineMinute==True:
            digitCount+=1
            if digitCount==3:
                #in case the program gets through the last iteration without
                #checking "the minute"
               if sTimeKnown==False:
                   minute=checkMinute(sTime[2:])
                   if minute==False:return False
                   else:sTime,sTimeKnown=sTime[:2]+minute,True
               elif eTimeKnown==False:
                   minute=checkMinute(eTime[2:])
                   if minute==False:return False
                   else:eTime,eTimeKnown=eTime[:2]+minute,True
    if 0<len(eTime)<=2:
        (eTime,eAMPM)=checkHour(eTime,eAMPM)
        if eTime==False:return False
        eTime,eTimeKnown=addDefaultMinute(eTime),True
    result=timeConversion([sTime,sAMPM,eTime,eAMPM])
    return result

def checkHour(hour,AMPM):
    if len(hour)>2 or len(hour)==0:
        #an hour is either one or two digits
        return False,False
    elif len(hour)==1:
        hour="0"+hour
    if int(hour)<0 or int(hour)>24:
        #there are only 24 hours
        return False,False
    elif int(hour)>12:
        AMPM="Sure"
    return (hour,AMPM)

def checkMinute(minute):
    if len(minute)!=2:
        #a minute should have 2 digits
        return False
    elif int(minute)<0 or int(minute)>59:
        #minute should be between 0 and 59
        return False
    else:
        return minute

def addDefaultMinute(time):
    default="00"
    if len(time)==2:
        time+=default
    return time

def timeConversion(currentResult):
    if currentResult[1]=="Sure" or currentResult[3]=="Sure":
        #it is probably in military time already
        return currentResult
    elif currentResult[1]=="Unsure" and currentResult[3]=="Unsure":
        #we cannot do anything about it for now :(
        return currentResult
    elif currentResult[1]!="Unsure" and currentResult[3]!="Unsure":
        currentResult=timeConversionHelper1(currentResult[:2])+\
                       timeConversionHelper1(currentResult[2:])
        return currentResult
    elif currentResult[1]=="Unsure":
        currentResult=timeConversionHelper2(currentResult,1)
        return currentResult
    elif currentResult[3]=="Unsure":
        if currentResult[2]!="":
            currentResult=timeConversionHelper2(currentResult,3)
        else:
            currentResult=timeConversionHelper1(currentResult[:2])+\
                           currentResult[2:]
        return currentResult
    else:
        return currentResult

def timeConversionHelper1(timeList):
    time=timeList[0]
    if timeList[1].startswith("A"):
        if time[:2]=="12":
            #don't want to be confused with 12 at noon
            timeList[0]="00"+time[2:]
        return timeList
    elif timeList[1].startswith("P"):
        if time[:2]<"12":
            timeList[0]=str(int(time[:2])+12)+time[2:]
        return timeList
    else:
        return timeList

def timeConversionHelper2(currentResult,problemIndex):
    #pass on the AMPM of stime/etime to the other
    correctIndex=4-problemIndex
    if (problemIndex-correctIndex)*(int(currentResult[problemIndex-1])-\
                                   int(currentResult[correctIndex-1]))>0:
        currentResult[problemIndex]=currentResult[correctIndex]
    currentResult=timeConversionHelper1(currentResult[:2])+\
                   timeConversionHelper1(currentResult[2:])
    currentResult[problemIndex]="Default"
    return currentResult

def formattedDateExists(sentence):
    check=re.finditer(r"\d{1,2}/\d{1,2}(/\d{1,4})?",\
                      sentence)
    #MM/DD/YYYY
    result=[(m.start(0),m.end(0)) for m in check]
    #cited from http://stackoverflow.com/questions/3519565/
    #find-the-indexes-of-all-regex-matches-in-python
    return result

def extractDates(sentence,year,sentDate):
    convertedDate=datetime.strptime(sentDate,"%Y%m%d")
    dateList,word,sIndex=[],"",0
    for i in xrange(len(sentence)):
        if sentence[i].isalpha():
            if word=="":
                #start of a new word
                sIndex=i
            word+=sentence[i]
        else:
            eIndex=i
            #end of a word
            if sentence[i] in string.punctuation:
                #punctuation should be part of the previous word
                eIndex+=1
            word=word.lower()
            if word in dictMonConvert:
                dateInfo=extractDateFromMonth(year,sIndex,eIndex,word,sentence)
                if dateInfo!=None:dateList.append(dateInfo)
            elif word in dictDayConvert:
                day=dictDayConvert[word]
                wordA,ASIndex=extractWordBefore(sIndex-1,sentence)
                wordB,BSIndex=extractWordBefore(ASIndex-1,sentence)
                date=extractDateFromDay(convertedDate,day,wordA,wordB,BSIndex,\
                                        ASIndex,sIndex,eIndex)
                dateList.append(date)
            elif word=="today":
                dateList.append([(sIndex,eIndex),"date",sentDate])
            elif word=="tonight":
                dateList.append([(sIndex,eIndex),"date",sentDate,"night"])
            elif word=="tomorrow":
                eventDate=convertedDate+timedelta(days=1)
                dateList.append([(sIndex,eIndex),"date",str(eventDate.year)+\
                                 str(eventDate.month)+str(eventDate.day)])
            elif word in set(["morning","afternoon","evening","night"]):
                wordA,ASIndex=extractWordBefore(sIndex-1,sentence)
                wordB,BSIndex=extractWordBefore(ASIndex-1,sentence)
                AMPM=checkAMPMWord(word,wordB,wordA,BSIndex,ASIndex,sIndex,\
                                   eIndex)
                if AMPM!=None:dateList.append(AMPM)
            word=""
    formattedDateList=formattedDateExists(sentence)
    if formattedDateList!=[]:
        for index in formattedDateList:
            if (sIndex==0 or re.match(r"\W",sentence[sIndex-1])) and \
           (eIndex==len(sentence) or re.match(r"\W",sentence[eIndex])):
            #make sure the start/end of the dateString is either the start/end
            #of a sentence or the start/end of a word.
                (sIndex,eIndex)=index
                dateString=sentence[sIndex:eIndex]
                date=extractFormattedDateDMY(dateString,year)
                if date!=False:dateList.append([index,"date",date])
    return dateList

def extractWordBefore(sIndex,sentence):
    word=""
    if sIndex>=0:
        for i in xrange(sIndex,-1,-1):
            char=sentence[i]
            if char!=" ":
                word=char+word
            elif char==" " and word=="":
                #this might be whitespace between words
                pass
            else:
                return (word,i+1)
    return (word,0)

def extractWordAfter(eIndex,sentence):
    word=""
    if eIndex<len(sentence):
        for i in xrange(eIndex,len(sentence)):
            char=sentence[i]
            if char!=" ":
                word+=char
            elif char==" " and word=="":
                #this might be whitespace between words
                pass
            else:
                return (word,i)
    return (word,len(sentence))

def extractDateFromMonth(year,sIndex,eIndex,word,sentence):
    month=str(dictMonConvert[word])
    if month!=None:
        if len(month)<2:
            month="0"+month
        wordA,ASIndex=extractWordBefore(sIndex-1,sentence)
        wordB,BEIndex=extractWordAfter(eIndex,sentence)
        wordC,CEIndex=extractWordAfter(BEIndex,sentence)
        if wordC==",":
            wordC,CEIndex=extractWordAfter(CEIndex+1,sentence)
        possibleDates=[]
        possibleDates.append(extractDateMDY(year,month,wordB,\
                            wordC,sIndex,BEIndex,CEIndex))
        possibleDates.append(extractDateDMY(year,month,wordA,\
                            wordB,ASIndex,sIndex,eIndex,BEIndex))
        possibleDates.append(extractDateYMD(year,month,wordB,\
                            wordA,ASIndex,sIndex,eIndex,BEIndex))
        for date in possibleDates:
            if date[2]!=None:
                Date=date[0]+date[1]+date[2]
                return[date[3],"date",Date]
    
def checkAMPMWord(word,wordA,wordB,sIndex,mSIndex,eSIndex,eIndex):
    wordA,wordB=wordA.lower(),wordB.lower()
    if wordB in set(["this","the"]):
        if wordA in set(["on","in","at","by"]):
            return [(sIndex,eIndex),"AMPM",word]
        else:
            return [(mSIndex,eIndex),"AMPM",word]
    elif wordB in set(["on","in","at","by"]):
        return [(mSIndex,eIndex),"AMPM",word]
    
def extractDateFromDay(sentDate,eventDay,wordA,wordB,sIndex,msIndex,esIndex,\
                       eIndex):
    sentDay=int(sentDate.strftime("%w"))
    if eventDay>sentDay:
        dayDiff=eventDay-sentDay
    else:
        dayDiff=eventDay+7-sentDay
    eventDate=sentDate+timedelta(days=dayDiff)
    monthStr=str(eventDate.month)
    if len(monthStr)<2:
        monthStr="0"+monthStr
    dayStr=str(eventDate.day)
    if len(dayStr)<2:
        dayStr="0"+dayStr
    eventDateStr=str(eventDate.year)+monthStr+dayStr
    if wordA!="" and tagSentence(wordA)[0][1]=="IN":
        return [(msIndex,eIndex),"date?",eventDateStr]
    elif wordB!= "" and tagSentence(wordB)[0][1]=="IN":
        return [(sIndex,eIndex),"date?",eventDateStr]
    else:
        return [(esIndex,eIndex),"date?",eventDateStr]

def extractDate(month,dayWord,yearWord):
    day=None
    year=None
    Dnumber=leadingNumbers(dayWord)
    if 0<len(Dnumber)<=2:
        #a "day" is at most two-digit
        day=extractDay(dayWord)
    Ynumber=leadingNumbers(yearWord)
    if len(Ynumber)==4:
        #a "year" is always four-digit
        year=extractYear(yearWord)
    return (year,month,day)
        
def extractDateDMY(year,month,dayWord,yearWord,sIndex,msIndex,meIndex,eIndex):
    altYear,month,day=extractDate(month,dayWord,yearWord)
    if altYear==None:
        if day==None:
            return (year,month,day,(msIndex,meIndex))
        else:
            return (year,month,day,(sIndex,meIndex))
    else:
        if day==None:
            return (altYear,month,day,(msIndex,eIndex))
        else:
            return (altYear,month,day,(sIndex,eIndex))
        
def extractDateYMD(year,month,dayWord,yearWord,sIndex,msIndex,meIndex,eIndex):
    altYear,month,day=extractDate(month,dayWord,yearWord)
    if altYear==None:
        if day==None:
            return (year,month,day,(msIndex,meIndex))
        else:
            return (year,month,day,(msIndex,eIndex))
    else:
        if day==None:
            return (altYear,month,day,(sIndex,meIndex))
        else:
            return (altYear,month,day,(sIndex,eIndex))

def extractDateMDY(year,month,dayWord,yearWord,sIndex,mIndex,eIndex):
    altYear,month,day=extractDate(month,dayWord,yearWord)
    if altYear==None:
        return (year,month,day,(sIndex,mIndex))
    else:
        return (altYear,month,day,(sIndex,eIndex))
    
def extractDay(word):
    day=""
    word=word.lower()
    if word[-1] in string.punctuation:
        word=word[:-1]
    if len(word)==1:
        day="0"+word
    elif len(word)==3 or len(word)==4:
        if word[-2:]=="st" or word[-2:]=="nd" or word[-2:]=="rd" or \
           word[-2:]=="th":
            day=word[:-2]
            if len(day)<2:
                day="0"+day
    elif len(word)==2:
        day=word
    if len(day)>0 and 1<=int(day)<=31:
        #there are at most 31 days in a given month
        return day

def extractYear(word):
    year=""
    if word[-1] in string.punctuation:
        word=word[:-1]
    if len(word)==4:
        year=word
    if len(year)>0:
        return year

def extractFormattedDateDMY(dateString,year):
    month,day,alterYear="","",""
    monthKnown,dayKnown=False,False
    #monthKnown and dayKnown helps to keep track of what information the program
    #is extracting
    for char in dateString:
        if monthKnown==False:
            if char.isdigit():month+=char
            elif char=="/":
                month=checkMonth(month)
                if month==False:return False
                else:monthKnown=True
        elif dayKnown==False:
            if char.isdigit():day+=char
            elif char=="/":
                day=checkDay(day)
                if day==False:return False
                else:dayKnown=True
        elif dayKnown==True:
            if char.isdigit():alterYear+=char
    alterYear=checkYear(alterYear,year)
    if alterYear!=False:year=alterYear
    return year+month+day

def checkMonth(month):
    if len(month)>2 or len(month)==0:
        return False
    elif len(month)==1:
        month="0"+month
    if int(month)==0 or int(month)>12:
        return False
    else:
        return month

def checkDay(day):
    if len(day)>2 or len(day)==0:
        return False
    elif len(day)==1:
        day="0"+day
    if int(day)==0 or int(day)>31:
        return False
    else:
        return day

def checkYear(alterYear,year):
    if len(alterYear)>4 or len(alterYear)==0:
        return False
    elif len(alterYear)==2:
        alterYear=year[:2]+alterYear
    if len(alterYear)==4:
        return alterYear
    return False

def parseHeaderDate(header):
    adjustIndex=0
    if header[0][:-1] in listDays:
        #the first element in the list is the day of the week
        adjustIndex=0
    elif len(header[0])==1 or len(header[0])==2:
        #the first element in the list is the day of the week
        adjustIndex=1
    elif header[0] in listMonths:
        #the first element in the list is the month
        adjustIndex=2
    if adjustIndex<2:
        day=header[1-adjustIndex]
        #by default, the day should be the second element in the list
        if len(day)==1:
            day="0"+day
        month=str(dictMonConvert[header[2-adjustIndex].lower()])
        year=header[3-adjustIndex]
        date=year+month+day
        time=header[4-adjustIndex]
        timezone=header[5-adjustIndex]
        return (date,time,timezone)

def findPPCC(taggedSentence):
    PPgrammar="""PP:{(<IN>|<VBP>)(<DT>?<NNP><POS>?)?<CD>?<DT>?(<NNP>|<NNPS>)+<CD>?(<,>?<NNP>+<CD>?|<IN><NNP>+)?}
    CC:{(<NNP>|<WRB>|<NN>)?<:>(<DT>?<NNP><POS>?)?<CD>?<DT>?<NNP>+<CD>?(<,>?<NNP>+<CD>?|<IN><NNP>+)?}"""
    cp=nltk.RegexpParser(PPgrammar)
    tree=cp.parse(taggedSentence)
    PPsubtrees=[]
    CCsubtrees=[]
    for subtree in tree.subtrees():
        if subtree.node=="PP" and len(subtree)>1:
            PPsubtrees.append(subtree)
        if subtree.node=="CC" and len(subtree)>1:
            CCsubtrees.append(subtree)
    return (PPsubtrees,CCsubtrees)

def extractLocationFromPP(tree):
    leaves=tree.leaves()
    prep=leaves[0][0]
    location=""
    if prep in {"in","at","on","inside","by"}:
        location=""
        for i in xrange(1,len(leaves)):
            leave=leaves[i]
            if leave in dictMonConvert or leave in dictDayConvert:
                break
            elif leave[-1]=="." and (leave[:-1] in dictMonConvert or\
                                     leave[:-1] in dictDayConvert):
                break
            elif len(location)!=0 and leave[0]!=",":
                location+=" "
            location+=leave[0]
        return location        
    return

def extractLocationFromCC(tree):
    leaves=tree.leaves()
    title=leaves[0][0]
    location=""
    if title.lower() in {"location","place","where"}:
        if 2<len(leaves):
            for i in xrange(2, len(leaves)):
                leave=leaves[i]
                if len(location)!=0 and leave[0]!=",":
                    location+=" "
                location+=leave[0]
            return location
    return
    
def untagSentence(taggedSentence):
    sentence=""
    for taggedWord in taggedSentence:
        sentence+=" "+taggedWord[0]
    return sentence

def extractLocation(sentence):
    taggedSentence=tagSentence(sentence)
    trees=findPPCC(taggedSentence)
    PPtrees=trees[0]
    CCtrees=trees[1]
    locations=[]
    for tree in CCtrees:
        location=extractLocationFromCC(tree)
        if location!=None:
            locations.append((location,"location","CC"))
    for tree in PPtrees:
        location=extractLocationFromPP(tree)
        if location!=None:
            locations.append((location,"location","PP"))
    return locations

