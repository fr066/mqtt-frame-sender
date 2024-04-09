import json
import logging
import random
import time
import threading
from tkinter import filedialog
from tkinter import messagebox

import tkinter as tk
from tkinter import *
from tkinter import ttk 
from paho.mqtt import client as mqtt_client
from threading import Thread


BROKER = '127.0.0.1'
PORT = 1883
# mqtt topic
TOPIC = "python-mqtt/tcp"
# client ID
CLIENT_ID = f'python-mqtt-tcp-pub-sub-sender'

USERNAME = ''
PASSWORD = ''


FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

FLAG_EXIT = False
FILE_OPENED = False
app = tk.Tk()
app.title("Mqtt frame sender app")
app.geometry("800x600+300+300")
items = dir("tk")
var = tk.StringVar(value=items)

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
        items = f_list
        var.set(value=items)
        print(items[0])
    #for index, fstr in f_list:
    #         items[index] = fstr
    
    fin.close()

def on_connect(client, userdata, flags, rc):
    if rc == 0 and client.is_connected():
        print("Connected to MQTT Broker!")
        client.subscribe(TOPIC)
        submit_button["text"] = "Отключится"
    else:
        print(f'Failed to connect, return code {rc}')

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


def on_message(client, userdata, msg):
    print(f'Received `{msg.payload.decode()}` from `{msg.topic}` topic')


def connect_mqtt():
    client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, CLIENT_ID)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=120)
    client.on_disconnect = on_disconnect
    
    return client


    
def publish(client):
    msg_count = 0
    while not FLAG_EXIT:
        msg_list.activate(msg_count)
        msg_dict = msg_list.get(msg_count)
        msg = json.dumps(msg_dict)
        if not client.is_connected():
            logging.error("publish: MQTT client is not connected!")
            time.sleep(1)
            continue
        result = client.publish(TOPIC, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            pass
            #print(f'Send `{msg}` to topic `{TOPIC}`')
        else:
            print(f'Failed to send message to topic {TOPIC}')
        msg_count += 1
        time.sleep(0.01)
        if msg_count > msg_list.size():
            msg_count = 0

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
mainframe.grid(row=0,column=0)
open_button = ttk.Button(mainframe, text="Открыть", command=open_file)
open_button.grid(row=0,column=0)
msg_list = tk.Listbox(mainframe, width=88, height=30,listvariable=var)
msg_list.grid(row=1,column=0)
msg_list.bind('<<ListboxSelect>>', msg_select)
item = tk.StringVar()


yscroll = tk.Scrollbar(mainframe,command=msg_list.yview, orient=tk.VERTICAL)
yscroll.grid(row=1, column=1, sticky=tk.N+tk.S)
msg_list.configure(yscrollcommand=yscroll.set)
entryEdit = tk.Entry(mainframe, textvariable=item, width=88)
entryEdit.grid(row=2,column=0)
entryEdit.bind('<Return>', msg_update)

play_button = ttk.Button(mainframe, text="Отправить", command=play_file, )
play_button.grid(row=3,column=0)
play_button["state"] = DISABLED
leftframe = ttk.Frame(borderwidth=1, relief=SOLID, padding=[8, 10])
leftframe.grid(row=0,column=1)
label = ttk.Label(leftframe, text="Адресс сервера:")
label.grid(row=1,column=0)

entry = ttk.Entry(leftframe)
entry.grid(row=2,column=0)
entry.insert(0, "127.0.0.1")

submit_button = ttk.Button(leftframe, text="Подключится", command=on_submit)
submit_button.grid(row=3,column=0)


exit_button = ttk.Button(leftframe, text="Выход", command=on_exit)
exit_button.grid(row=10,column=0,padx=10,pady=10)

app.mainloop()