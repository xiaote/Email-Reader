#Xiaote Zhu
#GUI

from Tkinter import *
import Calendar
import Email
import time

def drawEntries(root):
    frame=root.data.initFrame
    root.data.account=StringVar()
    root.data.password=StringVar()
    E1=Entry(frame,width=30,font="Times 14",textvariable=root.data.account)
    E2=Entry(frame,width=30,font="Times 14",textvariable=root.data.password,\
             show='*')
    L1=Label(frame,text="Gmail Account",font="Times 14 bold",fg="white",\
             bg=root.data.theme)
    L2=Label(frame,text="Gmail Password",font="Times 14 bold",fg="white",\
             bg=root.data.theme)
    E1.grid(row=3,column=4)
    E2.grid(row=5,column=4)
    L1.grid(row=3,column=3,sticky=E)
    L2.grid(row=5,column=3,sticky=E)
    
def drawButton1(root):
    frame=root.data.initFrame
    def f():
        checkEmailCalendar(root)
    B1=Button(frame,width=5,text="Enter",font="Times 14",fg="white",\
              bg=root.data.theme,activebackground="white",command=f)
    B1.grid(row=6,column=4,sticky=E)

def drawButton2(root):
    frame=root.data.secondFrame
    def f():
        if root.data.mailbox.get()=="Select a mailbox":
            drawErrMsg2(root,"Please select a mailbox")
        else:
            runEmailCalendar(root)
    B1=Button(frame,width=5,text="Enter",font="Times 14",fg="white",\
              bg=root.data.theme,activebackground="white",command=f)
    B1.grid(row=8,column=8,sticky=E)

def drawCanvas(root):
    width,height=root.data.canvasWidth, root.data.canvasHeight
    canvas=Canvas(root,width=width,height=height)
    canvas.grid(row=0,column=0,rowspan=10,columnspan=10)
    canvas.create_rectangle(0,0,width,height, fill=root.data.theme)
    canvas.create_text(10,10,anchor=NW,text="Email Reader",\
                       font="Times 30 bold",fill="white")
    root.data.canvas=canvas

def drawFrameCanvas(root,frame):
    width,height=root.data.frameWidth,root.data.frameHeight
    canvas=Canvas(frame,width=width,height=height)
    canvas.grid(row=0,column=0,rowspan=10,columnspan=10)
    canvas.create_rectangle(0,0,width,height,fill=root.data.theme)

def drawErrMsg(root,msg):
    frame=root.data.initFrame
    L=Label(frame,text=msg,font="Times 12",fg="red",bg=root.data.theme)
    L.grid(row=6,column=4)
    root.data.ErrMsg=L

def drawErrMsg2(root,msg):
    frame=root.data.secondFrame
    L=Label(frame,text=msg,font="Times 12",fg="red",bg=root.data.theme)
    L.grid(row=8,column=6)
    root.data.ErrMsg=L

def drawMsg(root,msg):
    canvas=root.data.canvas
    width,height=root.data.canvasWidth,root.data.canvasHeight
    root.data.msg=canvas.create_text(width/2.0,height/2.0,text=msg,\
                                     font="Times 34 bold", fill="white")

def listMailboxes(root):
    mailboxes=root.data.mailboxes
    secondFrame=Frame(root,width=root.data.frameWidth,\
        height=root.data.frameHeight)
    secondFrame.grid(row=0,column=0,rowspan=10,columnspan=10)
    drawFrameCanvas(root,secondFrame)
    root.data.secondFrame=secondFrame
    mailboxList=["Select a mailbox"]
    for mailbox in mailboxes:
        mailboxList.append(mailbox[0])
    root.data.mailbox=StringVar()
    root.data.mailbox.set(mailboxList[0])
    Om=OptionMenu(secondFrame,root.data.mailbox,*mailboxList)
    Om.grid(row=1,column=5)
    Om.config(fg="white",bg=root.data.theme,font="Times 16",\
              activeforeground="black",activebackground="white",width=15)
    Om["menu"].config(fg="white",bg=root.data.theme,font="Times 14")
    drawButton2(root)

def listMailboxes2(root):
    mailboxes=root.data.mailboxes
    secondFrame=Frame(root,width=root.data.frameWidth,\
        height=root.data.frameHeight)
    secondFrame.grid(row=0,column=0,rowspan=10,columnspan=10)
    drawFrameCanvas(root,secondFrame)
    root.data.secondFrame=secondFrame
    Msg=Message(secondFrame,bg=root.data.theme,fg="red",font="Times 16 bold",\
                text="""No unread emails are found in this mailbox. Please
select another one.""")
    Msg.grid(row=1,column=1)
    mailboxList=["Select a mailbox"]
    for mailbox in mailboxes:
        mailboxList.append(mailbox[0])
    root.data.mailbox=StringVar()
    root.data.mailbox.set(mailboxList[0])
    Om=OptionMenu(secondFrame,root.data.mailbox,*mailboxList)
    Om.grid(row=2,column=5)
    Om.config(fg="white",bg=root.data.theme,font="Times 16",\
              activeforeground="black",activebackground="white",width=15)
    Om["menu"].config(fg="white",bg=root.data.theme,font="Times 14")
    drawButton2(root)

def listEvents(root,eventsList):
    thirdFrame=Frame(root,width=root.data.frameWidth,\
                    height=root.data.frameHeight)
    thirdFrame.grid(row=0,column=0,rowspan=10,columnspan=10)
    drawFrameCanvas(root,thirdFrame)
    root.data.thirdFrame=thirdFrame
    yScroll=Scrollbar(thirdFrame,orient=VERTICAL)
    yScroll.grid(row=0,column=1,sticky=N+S)
    Lb=Listbox(thirdFrame,font="Times 12",bg=root.data.theme,fg="white",\
               width=80,height=20,yscrollcommand=yScroll.set,selectmode=SINGLE)
    Lb.grid(row=0,column=0)
    for i in xrange(len(eventsList)):
        if i!=0:
            Lb.insert("end"," ")
        for item in eventsList[i]:
            Lb.insert("end",item)
    yScroll['command'] = Lb.yview
    #part of these codes are modified based on:
    #http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/listbox-scrolling.html

def removeAll(frame):
    frame.destroy()

def removeErrMsg(root):
    root.data.ErrMsg.grid_forget()
    root.data.ErrMsg=None
    
def run():
    root=Tk()
    root.grid()
    class Struct: pass
    root.data=Struct()
    root.data.ErrMsg=None
    root.data.canvasWidth=700
    root.data.canvasHeight=500
    root.data.frameWidth=600
    root.data.frameHeight=400
    root.data.theme="dark slate blue"
    drawCanvas(root)
    initFrame=Frame(root,width=root.data.frameWidth,\
                    height=root.data.frameHeight)
    initFrame.grid(row=0,column=0,rowspan=10,columnspan=10)
    drawFrameCanvas(root,initFrame)
    root.data.initFrame=initFrame
    drawEntries(root)
    drawButton1(root)
    def f(event):
        if root.data.ErrMsg!=None:
            removeErrMsg(root)
    root.bind("<Button-1>",f)
    root.mainloop()

def checkEmailCalendar(root):
    account=root.data.account.get()
    password=root.data.password.get()
    if account=="" or password=="":
        drawErrMsg(root,"Please enter your account and password")
    else:
        check=Email.checkAccount(account,password)
        if check==None:
            drawErrMsg(root,"Wrong account or password!")
        else:
            try:
                service=Calendar.checkAccount(account)
                if service!=None:
                    root.data.service=service
                    root.data.mail,root.data.mailboxes=check
                    removeAll(root.data.initFrame)
                    listMailboxes(root)
                else:
                    drawErrMsg(root,"Cannot connect to the calendar")
            except:
                drawErrMsg(root,"Unable to find Google server")


def runEmailCalendar(root):
    removeAll(root.data.secondFrame)
    root.data.canvas.after(100,lambda:\
                           drawMsg(root,"I am reading very hard..."))
    mail=root.data.mail
    mailbox=root.data.mailbox.get()
    service=root.data.service
    def f():
        eventList=Email.run(mail,mailbox)
        if eventList=="No Unread":
            root.data.canvas.delete(root.data.msg)
            listMailboxes2(root)
        elif eventList!=[]:
            createdEvents=Calendar.createEvents(service,eventList)
            if createdEvents!=[]:
                root.data.canvas.delete(root.data.msg)
                listEvents(root,createdEvents)
            else:
                drawMsg(root,"No events created")
        else:
            root.data.canvas.delete(root.data.msg)
            drawMsg(root,"No events found")
    root.data.canvas.after(200,f)
    
run()
