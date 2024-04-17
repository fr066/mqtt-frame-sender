import json
import logging
import random
import time
from datetime import datetime
import threading
from tkinter import filedialog
from tkinter import messagebox

import tkinter as tk
from tkinter import *
from tkinter import ttk 
from paho.mqtt import client as mqtt_client
from threading import Thread


BROKER = '192.168.1.129'
PORT = 1883
# mqtt topic
MAIN_TOPIC = "FV-robotics-mqtt/tcp"
SEND_TOPIC = "FV-robotics-mqtt/"
SEND_TOPIC1 = "FV-robotics-mqtt/01"
SEND_TOPIC2 = "FV-robotics-mqtt/02"
# client ID
CLIENT_ID = f'FV-robotics-mqtt-tcp-sender'

USERNAME = ''
PASSWORD = ''


FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60
MSG_LOOP = False
FLAG_EXIT = False
FILE_OPENED = False
app = tk.Tk()
app.title("Mqtt frame sender app")
app.geometry("800x740+200+200")
items = ["Файл не загружен"]
var = tk.StringVar(value=items)
loop_var = tk.StringVar(value='0')



def to_log(msg):
    ltime = datetime.now().strftime('%H:%M:%S')
    log_text.insert(tk.END, ltime + ": " + msg + '\n')
    log_text.see(tk.END)

    
def loop_cb_click():
    if loop_var.get() == 1:
        MSG_LOOP = True
    else:
        MSG_LOOP = False

def open_file():
    global FILE_OPENED
    global items
    global var
    fin = filedialog.askopenfile(mode='r',title='Select a File')
    if fin is not None:
        
        f_list = fin.readlines()
        FILE_OPENED = True
        #items = dir(f_list)
        
        items.clear()
        ff_list = [x.rstrip() for x in f_list]
            
            
        items = ff_list
        var.set(value=items)
        
    fin.close()

def on_connect(client, userdata, flags, rc):
    if rc == 0 and client.is_connected():
        print("Connected to MQTT Broker!")
        to_log("Присоеденились к MQTT брокеру!")
        client.subscribe(MAIN_TOPIC)
        submit_button["text"] = "Отключится"
    else:
        print(f'Failed to connect, return code {rc}')
        to_log(f'Ошибка подключения, код возврата {rc}')
    
def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
    global FLAG_EXIT
    FLAG_EXIT = True
    
def update_tree(m_in):
    if tree.exists(m_in["online"]["id"]):
        tree.item(m_in["online"]["id"], tags="online")
    else:
        tree.insert("", m_in["online"]["id"], iid=m_in["online"]["id"], text="Контроллер #"+ str(m_in["online"]["id"]), open=False,tags="online")
        for rob in m_in["online"]["robots"]:
            tree.insert(m_in["online"]["id"], index=END, text=rob)
    app.after(14950,tree_offline)
    
def tree_offline():
    for k in tree.get_children(""):
        tree.item(k,tags="offline")
        
    #tree.item(2,tags="offline")
    #app.after(59000,tree_offline)

def on_message(client, userdata, msg):
    #print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')
    to_log(f'Получено `{msg.payload.decode()}` от `{msg.topic}` топика')
    m_decode = str(msg.payload.decode("utf-8", "ignore"))
    #print(f"data type: {type(m_decode)}")
    #print(f"data decoded: {m_decode}")
    #print("Converting from Json to Object...")
    m_in = json.loads(m_decode)
    #print(f"converted data type: {type(m_in)}")
    #print(f"converted data: {m_in}")
    #print('\n')
    if m_in["type"] == 'ping':
        update_tree(m_in)
    if m_in["type"] == 'connect':
        update_tree(m_in)
        
    
def connect_mqtt():
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, CLIENT_ID)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=120)
    client.on_disconnect = on_disconnect
    
    return client


    
def publish(client):
    global FLAG_EXIT
    global MSG_LOOP
    msg_count = 0
    while not FLAG_EXIT:
        msg_list.activate(msg_count)
        msg = msg_list.get(msg_count) 
        new_msg = []  #BAD CODE !!!! - need rewrite 
        jmsg = json.loads(msg)  
        jmsg2 = json.loads(msg)
        if jmsg["type"] == "frame":
            
            #msg = json.dumps(msg_dict).strip('\"') #remove first and last commas
           
            
            jmsg["angles"].pop()
            jmsg["angles"].pop()
            jmsg["angles"].pop()
            jmsg["angles"].pop()
            jmsg["angles"].pop()
            jmsg["angles"].pop()
            del jmsg2["angles"][0]
            del jmsg2["angles"][0]
            del jmsg2["angles"][0]
            del jmsg2["angles"][0]
            del jmsg2["angles"][0]
            del jmsg2["angles"][0]
            
            #to_log(json.dumps(jmsg))
            #to_log(json.dumps(jmsg2))
        if not client.is_connected():
            logging.error("publish: MQTT client is not connected!")
            time.sleep(1)
            continue
       
        result = client.publish(SEND_TOPIC1, json.dumps(jmsg))
        client.publish(SEND_TOPIC2, json.dumps(jmsg2))
        # result: [0, 1]
        status = result[0]
        if status == 0:
            to_log(f'Отправлено: `{json.dumps(jmsg)}` в топик `{SEND_TOPIC1}`')
            to_log(f'Отправлено: `{json.dumps(jmsg2)}` в топик `{SEND_TOPIC2}`')
            #print(f'Send `{msg}` to topic `{TOPIC}`')
        else:
            to_log(f'Failed to send message to topic `{SEND_TOPIC1}`')
            
        msg_count += 1
        time.sleep(0.02)
        if msg_count == msg_list.size():
            if MSG_LOOP:
                msg_count = 0
            else:
                FLAG_EXIT = True
    play_button()           

def run():
    if FLAG_EXIT:
        logging.info("EXIT FLAG - quit thread run")
        return
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                        level=logging.DEBUG)
    client = connect_mqtt()
    client.loop_start()
    time.sleep(0.01)
    play_button["state"] = NORMAL
    tEvent.wait()
    if client.is_connected():
        submit_button["text"] = "Отключится"
        
        publish(client)
    else:
        client.loop_stop()

def on_disconnect(client, userdata, rc):
    logging.info("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        logging.info("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            logging.info("Reconnected successfully!")
            return
        except Exception as err:
            logging.error("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    logging.info("Reconnect failed after %s attempts. Exiting...", reconnect_count)
    
def play_file():
    if tEvent.is_set():
       tEvent.clear()
       play_button["text"] = "Отправить"
    else:
        tEvent.set()
        play_button["text"] = "Остановить"
    
def on_submit():
    mqttThread = Thread(target=run, daemon=True)
    if submit_button["text"] == "Подключится":
        sAdr = entry.get()
        BROKER = sAdr
        mqttThread.start()
        
    if submit_button["text"] == "Отключится":
       global FLAG_EXIT
       FLAG_EXIT = True
       tEvent.clear()

def on_exit():
    if messagebox.askokcancel("Выход", "Закрыть приложение ?"):
        FLAG_EXIT = True
        tEvent.clear()
        time.sleep(0.5)
        app.destroy()
    
def msg_select(event):
    i = msg_list.curselection()[0]
    item.set(items[i])

def msg_update(event):
    i = msg_list.curselection()[0]
    items[i] = item.get()
    var.set(items)

tEvent = threading.Event()



#var = tk.StringVar(value=items)

mainframe = ttk.Frame(borderwidth=1, relief=SOLID, padding=[8, 10])
mainframe.grid(row=0,column=0,padx=4,pady=4)
open_button = ttk.Button(mainframe, text="Открыть", command=open_file)
open_button.grid(row=0,column=0,padx=4,pady=4,sticky=E)
loop_cb = ttk.Checkbutton(mainframe, text="Повторять", command=loop_cb_click)
loop_cb.grid(row=0,column=0,padx=4,pady=4,sticky=W)


msg_list = tk.Listbox(mainframe, width=88, height=30,listvariable=var)
msg_list.grid(row=1,column=0)
msg_list.bind('<<ListboxSelect>>', msg_select)
item = tk.StringVar()


yscroll = ttk.Scrollbar(mainframe,command=msg_list.yview, orient=tk.VERTICAL)
yscroll.grid(row=1, column=1, sticky=tk.N+tk.S)
msg_list.configure(yscrollcommand=yscroll.set)
entryEdit = ttk.Entry(mainframe, textvariable=item, width=88)
entryEdit.grid(row=2,column=0)
entryEdit.bind('<Return>', msg_update)

play_button = ttk.Button(mainframe, text="Отправить", command=play_file, )
play_button.grid(row=3,column=0)
play_button["state"] = DISABLED



leftframe = ttk.Frame(borderwidth=1, relief=SOLID, padding=[8, 10])
leftframe.grid(row=0,column=1)

label = ttk.Label(leftframe, text="Адресс MQTT сервера:")
label.grid(row=1,column=0)

entry = ttk.Entry(leftframe)
entry.grid(row=2,column=0)
entry.insert(0, BROKER)

submit_button = ttk.Button(leftframe, text="Подключится", command=on_submit)
submit_button.grid(row=3,column=0)
gstyle = ttk.Style()
gstyle.configure("Treeview",
                 fieldbackground="lightgreen",
                 rowheight=25
)
tree = ttk.Treeview(leftframe)
# установка заголовка
tree.heading("#0", text="Подключенные устройства", anchor=NW)
tree.tag_configure("online",foreground="green")
tree.grid(row=4,column=0,sticky=NW)

logframe = ttk.Frame(borderwidth=1, relief=SOLID, padding=[8, 10])
logframe.grid(row=3,column=0,columnspan=3)
log_text = tk.Text(logframe, width=96, height=8, bg="black", fg='lightgreen', wrap=WORD)
log_text.bind("<Key>", lambda e: "break")
log_text.pack()
exit_button = ttk.Button(leftframe, text="Выход", command=on_exit)
exit_button.grid(row=10,column=0,padx=10,pady=10)

app.mainloop()