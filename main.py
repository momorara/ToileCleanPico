# -*- coding: utf-8 -*-
#!/usr/bin/python3
"""
2025/05/12  RemotePicoを基本にToileCleanPicoを作成する
    v01     sw 2個対応でとりあえず作成、あとは基板ができてから
2025/05/13  tilet基板に対応
2025/05/26  人感センサー対応
    v02

ToileCleanPico_02.py
"""
import time
from machine import Pin

# Wを使う場合は、wifiをきる
#wlan.active(False) 

# 消費電力抑制のためGPIO 2～28 をプルダウン（使用ピンは除外）
for i in range(0, 29):
    if i not in (1,13,14,15,17):  # sw,LEDなど使用中のピンは除外
        Pin(i, Pin.IN, Pin.PULL_DOWN)

""" GPIO pin 設定 """""""""
# Remote pin設定
# tx_GPIO = 17   <--  send_file.pyで設定する
rx_GPIO = 15
# 表示用+ED　pin設定
display_LED = 13
# スイッチのpin設定
sw_n = 6 # swの数 6個全て
sw_pin = [14,14,14,14,14,14] # swのGPIO pin sw-no:4
SR_602 = 1 # 人感センサーのピン
""""""""""""  """"""""""""
SR_602 = Pin(SR_602, Pin.IN)

led2 = Pin(display_LED, Pin.OUT,Pin.PULL_DOWN)
def LED_flash(count=3):
    for _ in range(count):
        led2.on()
        time.sleep(.02)
        led2.off()
        time.sleep(.05)
LED_flash()

# picoボード上のLED
led = Pin('LED', Pin.OUT)
def LEDonoff(i=3):
    for _ in range(i):
        led.on()
        time.sleep(.1)
        led.off()
        time.sleep(.05)
LEDonoff()

# from UpyIrTx import UpyIrTx  <--  send_file.pyで設定する
from UpyIrRx import UpyIrRx
import json
import uos

# 信号送信用pin設定  <--  send_file.pyで設定する
# tx_pin = Pin(tx_GPIO, Pin.OUT) 
# tx = UpyIrTx(0, tx_pin)

# 信号受信用pin設定
rx_pin = Pin(rx_GPIO, Pin.IN) 
rx = UpyIrRx(rx_pin)

# picoのGPIOとSWの対応pinの設定
SW = [0,0,0,0,0,0]
SW[0] = Pin(sw_pin[0], Pin.IN, Pin.PULL_UP)
SW[1] = Pin(sw_pin[1], Pin.IN, Pin.PULL_UP)
SW[2] = Pin(sw_pin[2], Pin.IN, Pin.PULL_UP)
SW[3] = Pin(sw_pin[3], Pin.IN, Pin.PULL_UP)
SW[4] = Pin(sw_pin[4], Pin.IN, Pin.PULL_UP)
SW[5] = Pin(sw_pin[5], Pin.IN, Pin.PULL_UP)


# microPythonにはファィルコピーのコマンドが無いみたいなので作る
def copy_file(source, destination):
    try:
        # コピー元ファイルを読み込む
        with open(source, 'rb') as f_source:
            # コピー先ファイルに書き込む
            with open(destination, 'wb') as f_destination:
                # コピー元ファイルからデータを読み取り、コピー先ファイルに書き込む
                while True:
                    data = f_source.read(1024)  # データを1024バイトずつ読み取る
                    if not data:
                        break
                    f_destination.write(data)  # コピー先ファイルにデータを書き込む
        return True
    except OSError as e:
        print("Error:", e)
        return False


# ------------------- main loop ---------------------
start = time.time()  # 現在のUNIX時間（秒）
while True:
    sw_all = sw_n
    on_sw_no = 4 # 洗浄ボタンを指定 4しかないのでここで指定
    loop_count = 0
    # swがどれか押されるまでswのチェックをする 複数押された場合は 若番が認識される
    while sw_all == sw_n:
        sw_all = 0
        #print(SW[0].value(),SW[1].value())
        time.sleep(0.1)
        for i in range(sw_n):
            sw_all = sw_all + SW[i].value() 
        
        # -------- LED 点滅
        loop_count = loop_count +1
        if loop_count > 80: # 約8秒周期で点滅
            # print(loop_count)
            loop_count = 0
            LED_flash(3)
            #LEDonoff() #Thonnyで停止すると次エラーになる 本番ではこちらを使いたい
            # print(time.time() - start)


        # 人感センサーが動作したら6時間タイマーをリセット
        # if 人感センサーon
        #   start = time.time()  # 現在のUNIX時間（秒）カウンターのリセット

        # 人感センサーを確認し、感知したらタイマーリセット
        if SR_602.value() == 1:
            start = time.time()  # 現在のUNIX時間（秒）カウンターのリセット
            led2.on()
        if SR_602.value() == 0:
            led2.off()        

        # 6時間タイマーをチェックして、6時間経過すれば、洗浄信号を出す。
        # if time.time() - start >= 60*60*6:
        if time.time() - start >= 60:
            start = time.time()  # 現在のUNIX時間（秒）カウンターのリセット
            try:
                print("send file toiletClean")
                # 不要ファィルを削除
                try:uos.remove("data.json")
                except:pass
                #送信するファイルを'data.json'としてコピー
                # コピー元ファイル名とコピー先ファイル名を指定
                source_file = "iR_code_" + str(on_sw_no) + ".json"
                destination_file = 'data.json'
                # ファイルをコピーする
                if copy_file(source_file, destination_file):
                    print("File copied successfully.")
                else:
                    print("File copy failed.")
                # data.jsonを送信する
                with open('send_file.py', 'r') as f:
                    code = f.read()
                exec(code)
            except:
                print("ファイルなし")


    # 0.8秒後に再度確認して、押されていたら「長押し」、押されていなかったら「チョン押し」
    time.sleep(0.8)
    if SW[on_sw_no].value() == 0:
        on_sw_mode = "長押し"
    else:
        on_sw_mode = "チョン押し"
    print(on_sw_no, on_sw_mode)


    # チョン押しなら　押されたスイッチのリモコン信号を送信
    if on_sw_mode == "チョン押し":
        try:
            print("send file")
            start = time.time()  # 現在のUNIX時間（秒）カウンターのリセット

            # 不要ファィルを削除
            try:uos.remove("data.json")
            except:pass
            #送信するファイルを'data.json'としてコピー
            # コピー元ファイル名とコピー先ファイル名を指定
            source_file = "iR_code_" + str(on_sw_no) + ".json"
            destination_file = 'data.json'
            # ファイルをコピーする
            if copy_file(source_file, destination_file):
                print("File copied successfully.")
            else:
                print("File copy failed.")

            # data.jsonを送信する
            with open('send_file.py', 'r') as f:
                code = f.read()
            exec(code)

        except:
            print("ファイルなし")


    # 長押しなら　　　押されたスイッチのリモコン信号登録処理を行う
    if on_sw_mode == "長押し":
        print("read file")
        led2.off()
        time.sleep(0.8)
        LED_flash()
        led2.on()
        signal_list = []
        recive = 0
        while recive == 0:
            rx.record(3000)
            if rx.get_mode() == UpyIrRx.MODE_DONE_OK:
                signal_list = rx.get_calibrate_list()
                recive = 1
                print("1")
            else:
                # リモコン信号を待ったが、受信できなかったのでキャンセル
                signal_list = []
                print("2")
                break
        # on_sw_noからファィル名を作成
        file_name = "iR_code_" + str(on_sw_no) + ".json"
        # 受信したiR信号をファイルに保存
        with open(file_name, "w") as file:
            json.dump(signal_list, file)
        led2.off()

        # 読み取りの結果空データならLED点滅
        if signal_list == []:
            LED_flash()
            print("読み取り失敗空データでした")

