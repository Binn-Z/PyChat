# -*- coding: utf-8 -*-
from Tkinter import *
from socket import *
import tkFileDialog
import tkMessageBox
import time
import re
import threading
import sys     #解决字符流的编码问题
reload(sys)
sys.setdefaultencoding('utf-8')

dst_ip='0'  #对方ip
Port=46217  #通讯的端口号
Port_file=46216 #传输文件的端口
Size=1024   #接收的最大数据

#开始要求输入ip的对话框
class Dialog():
    def __init__(self):
        self.root=Tk()
        self.root.title('局域网聊天')
        self.root.geometry("300x150")
        self.txt_ip=Entry(self.root)
        self.txt_ip.place(x=120,y=20)
        self.lab=Label(self.root,text='请输入对方ip地址')
        self.lab.place(x=20,y=20)
        self.btn=Button(self.root,command=self.submit,text='确认')
        self.root.bind('<Return>',self.Keydown)
        self.btn.place(x=120,y=80)
        self.root.protocol("WM_DELETE_WINDOW", self.close)#直接关闭则退出程序
        self.root.mainloop()
        
    def submit(self):
       global dst_ip
       #通过正则表达式判断输入的ip地址是否合法
       pattern=r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$' 
       dst_ip=self.txt_ip.get()
       ip=re.match(pattern,dst_ip)
       if(ip):          
           if int(0<=ip.group(1))<=255 and 0<=int(ip.group(2))<=255 and 0<=int(ip.group(3))<=255 and 0<=int(ip.group(4))<=255:
               dst_ip=ip.group(0)
               self.root.destroy()
           else:
               tkMessageBox.showinfo('错误','输入地址不合法')
       else:
           tkMessageBox.showinfo('错误','输入地址不合法')

    def close(self):
        self.root.destroy()
        sys.exit(0)

    def Keydown(self,event):
        self.submit()


#主窗口
class MainWindow():
    def __init__(self):
        self.window=Tk()
        self.window.title('局域网聊天')
        self.window.geometry('450x500')
        #聊天记录窗口
        self.MessageList=Listbox(self.window,fg='red')
        self.MessageList.pack(expand=1,fill=BOTH)
        #输入窗口
        self.MessageInput=Entry(self.window,borderwidth=1)
        self.MessageInput.pack(padx=20,pady=50,fill=BOTH)
        self.MessageInput.bind('<Return>',self.Keydown)
        #发送消息按钮
        self.btn_send=Button(self.window,text='发送',width=10,command=self.SendMessage)
        self.btn_send.pack(side=BOTTOM and RIGHT,padx=20,pady=10)
        self.btn_filesend=Button(self.window,text='发送文件',width=10,command=self.SendFile)
        self.btn_filesend.pack(side=BOTTOM and RIGHT,padx=20,pady=10)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
    #按下回车键发送消息
    def Keydown(self,event):
        self.SendMessage()
        
    def close(self):
        self.window.destroy()
        sys.exit(0)
        
    #发送消息函数
    def SendMessage(self):
        message=self.MessageInput.get()
        #若有输入，则将其插入聊天记录
        if message:
            now=time.localtime()
            self.MessageList.insert(END,('你说[%s-%s-%s %s:%s:%s]'
                                     %(now.tm_year,now.tm_mon,now.tm_mday,
                                       now.tm_hour,now.tm_min,now.tm_sec)))
            self.MessageList.insert(END,message)
            self.MessageList.insert(END,'')
            self.MessageList.see(END)
            self.MessageInput.delete(0,message.__len__())
            SendSocket=socket(AF_INET,SOCK_STREAM)
            try:
                SendSocket.connect((dst_ip,Port))
            except BaseException,e:
                tkMessageBox.showinfo('异常',(e,'对方端口未打开'))
            SendSocket.send(message)
            SendSocket.close()
   
    #发送文件函数
    def SendFile(self):
        filepath=tkFileDialog.askopenfilename(initialdir = '')
        Send_file=open(filepath,'r')
        self.MessageList.insert(END,'文件发送中......')
        SendSocket=socket(AF_INET,SOCK_STREAM)
        try:
            SendSocket.connect((dst_ip,Port_file))
        except BaseException,e:
            tkMessageBox.showinfo('异常',(e,'对方端口未打开'))
        data=Send_file.read(Size)
        while data:
            SendSocket.sendall(data)
            data=Send_file.read(Size)                  
        SendSocket.close()
        Send_file.close()
        self.MessageList.insert(END,'文件发送完毕!')
        self.MessageList.insert(END,'')
        self.MessageList.see(END)
      

def main():
    dialog=Dialog()
    mainwindow=MainWindow()
    Host=''
    Addr=(Host,Port)
    Addr_File=(Host,Port_file)
    ReceiveSocket=socket(AF_INET,SOCK_STREAM)
    ReceiveFileSocket=socket(AF_INET,SOCK_STREAM)
    ReceiveSocket.bind(Addr)
    ReceiveFileSocket.bind(Addr_File)
    ReceiveSocket.listen(1)
    ReceiveFileSocket.listen(1)

    #监听即时消息的线程函数
    def ReceiveMessage():
        while True:
            conn,address=ReceiveSocket.accept()
            while True:
                msg=conn.recv(Size)
                if not msg:
                    break
                #将消息显示在聊天记录中
                now=time.localtime()
                mainwindow.MessageList.insert(END,('对方说[%s-%s-%s %s:%s:%s]'
                                         %(now.tm_year,now.tm_mon,now.tm_mday,
                                           now.tm_hour,now.tm_min,now.tm_sec)))
                mainwindow.MessageList.insert(END,msg)
                mainwindow.MessageList.insert(END,'')
                mainwindow.MessageList.see(END)
            conn.close()

    #监听文件传输的线程函数
    def ReceiveFile():
        while True:
            conn,address=ReceiveFileSocket.accept()
            now=time.localtime()
            filepath='%s%s%s-%s%s%s'%(now.tm_year,now.tm_mon,now.tm_mday,
                                      now.tm_hour,now.tm_min,now.tm_sec)
            try:
                ReceiveFile=open(filepath,'w')
            except IOError,e:
                tkMessageBox.showinfo('文件操作异常',e)
            mainwindow.MessageList.insert(END,'正在接收文件......')
            while True:
                data=conn.recv(Size)
                if not data:
                    break
                ReceiveFile.write(data)
            mainwindow.MessageList.insert(END,'文件接收完毕！')
            mainwindow.MessageList.insert(END,'')
            mainwindow.MessageList.see(END)
            ReceiveFile.close()
            conn.close()
            
             
            
        
        
    #主界面的线程和监听线程
    t1 = threading.Thread(target=ReceiveMessage)
    t2 = threading.Thread(target=mainloop)
    t3 = threading.Thread(target=ReceiveFile)
    t1.start()
    t2.start()
    t3.start()
    
if __name__=='__main__':
    try:
        main()
    except BaseException,e:
        if str(e)!='0':
            tkMessageBox.showinfo('异常',str(e))
            sys.exit(0)
