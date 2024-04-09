import json
import logging
import random
import time
import threading
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
        msg_dict = {
            'msg': msg_count
        }
        msg = json.dumps(msg_dict)
        if not client.is_connected():
            logging.error("publish: MQTT client is not connected!")
            time.sleep(1)
            continue
        result = client.publish(TOPIC, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f'Send `{msg}` to topic `{TOPIC}`')
        else:
            print(f'Failed to send message to topic {TOPIC}')
        msg_count += 1
        time.sleep(1)


def run():
    if FLAG_EXIT:
        logging.info("EXIT FLAG - quit thread run")
        return
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                        level=logging.DEBUG)
    client = connect_mqtt()
    client.loop_start()
    time.sleep(0.01)
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

def on_submit():
    mqttThread = Thread(target=run, daemon=True)
    if submit_button["text"] == "Подключится":
        sAdr = entry.get()
        BROKER = sAdr
        mqttThread.start()
    
    if submit_button["text"] == "Отключится":
       FLAG_EXIT = True
       tEvent.clear()

def on_exit():

    FLAG_EXIT = True
    tEvent.clear()
    time.sleep(0.5)
    quit()

tEvent = threading.Event()
app = tk.Tk()
app.title("Mqtt frame sender app")
app.geometry("800x600+300+300")
mainframe = ttk.Frame(borderwidth=1, relief=SOLID, padding=[8, 10])

leftframe = ttk.Frame(borderwidth=1, relief=SOLID, padding=[8, 10])
label = ttk.Label(leftframe, text="Адресс сервера:")
label.pack(anchor=NE, padx=10,pady=1)

entry = ttk.Entry(leftframe)
entry.pack(anchor=NE, padx=10,pady=1)
entry.insert(0, "127.0.0.1")
submit_button = ttk.Button(leftframe, text="Подключится", command=on_submit)
submit_button.pack(anchor=NE, padx=10,pady=2)
leftframe.pack(anchor=NE, fill=Y, padx=5, pady=5)

exit_button = ttk.Button(app, text="Выход", command=on_exit)
exit_button.pack(anchor=SE,side=BOTTOM,padx=10,pady=10)

app.mainloop()