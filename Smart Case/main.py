from pop import Window, Switch, Fan, RgbLedBar, Light, Tphg, Textlcd
from network import WLAN
import BlynkLib
import time

auto_temp = 30  # reference Temperature value   20~35
auto_light = 750  # reference Light value       
auto_humi = 35# reference Humidity value     20~50

BLYNK_AUTH = "79zFohbjHi2adKwyrX3Xkt3bWRDtvaCv"
SSID = 'U+NetC8B3'
PASSWORD = '4000024172'

auto_mode = False
light_value = temp_value = humidity_value = 0
color_value = [0, 0, 0]

switch_up = Switch('P8')
switch_down = Switch('P23')
fan = Fan()
window = Window()
rgbledbar = RgbLedBar()
tphg = Tphg(0x76)
light = Light(0x5C)
textlcd = Textlcd()

# Wi-Fi 연결 설정
wlan = WLAN(mode=WLAN.STA)
wlan.connect(SSID, auth=(WLAN.WPA2, PASSWORD))
while not wlan.isconnected():
    print('x')  # 원래는 print(x)가아니라 time.sleep(1)

# Blynk 연결 설정
blynk = BlynkLib.Blynk(BLYNK_AUTH)
blynk.run()

# 센서 콜백 함수
def light_callback(param):
    global light_value
    light_value = param.read()

def tphg_callback(param):
    global temp_value, humidity_value
    temp_value,_,humidity_value,_ = param.read()  # TPHG 센서의 반환값에서 온도와 습도를 읽음

# Blynk 가상 핀 제어 함수
@blynk.on("V1")
def Auto_Callback(value):
    global auto_mode
    auto_mode = value[0] == '1'
    print("auto mode %s" % ('on' if auto_mode else 'off'))

@blynk.on("V2")
def Temp_Callback(value):
    global auto_temp
    auto_temp = int(value[0])

@blynk.on("V3")
def Humi_Callback(value):
    global auto_humi
    auto_humi = int(value[0])
    
@blynk.on("V4")
def Light_Callback(value):
    global auto_mode
    if not auto_mode:
        if value[0] == '1':
            rgbledbar.setColor([139, 49, 0])
        else:
            rgbledbar.setColor([0, 0, 0])
    
@blynk.on("V5")
def RgbLedBar_R_Callback(value):
    if not auto_mode:
        global color_value
        color_value[0] = int(value[0])
        rgbledbar.setColor(color_value)

@blynk.on("V6")
def RgbLedBar_G_Callback(value):
    if not auto_mode:
        global color_value
        color_value[1] = int(value[0])
        rgbledbar.setColor(color_value)

@blynk.on("V7")
def RgbLedBar_B_Callback(value):
    if not auto_mode:
        global color_value
        color_value[2] = int(value[0])
        rgbledbar.setColor(color_value)

@blynk.on("V8")
def Fan_Callback(value):
    if not auto_mode:
        if value[0] == '1':
            fan.on()
        else:
            fan.off()

@blynk.on("V10")
def Window_Callback(value):
    if not auto_mode:
        if value[0] == '1':
            window.open()
        else:
            window.close()

# 센서 콜백 설정
light.setCallback(func=light_callback, param=light)
tphg.setCallback(func=tphg_callback, param=tphg)

# 장치 초기화
rgbledbar.on()
textlcd.print(" Blynk Auto Control ", x=0, y=0)
textlcd.print("Press both switches to exit", x=0, y=2)
textlcd.cursorOff()

log = time.time()

# 메인코드

while switch_up.read() or switch_down.read():
    blynk.run()

    if time.time() - log >= 1:
        log = time.time()
        blynk.virtual_write(0, "\n\nLight                :  " + str(light_value) + "lx")
        blynk.virtual_write(0, "\nTemperature         :   " + str(temp_value) + "C")
        blynk.virtual_write(0, "\nHumidity             :   " + str(humidity_value) + "%")
        
    if auto_mode:
    # 온도 조건 우선
        if temp_value > auto_temp + 3:  # 온도가 최대 기준 초과
            fan.on()
            window.open()
        elif temp_value < auto_temp - 3:  # 온도가 최소 기준 이하
            fan.off()
            window.close()
        else:
        # 온도가 적정 범위 내에 있을 때만 습도 조건 평가
            if humidity_value > auto_humi + 10:  # 습도가 최대 기준 초과
                fan.on()
            elif humidity_value < auto_humi - 10:  # 습도가 최소 기준 이하
                fan.off()
        # 온도와 습도가 모두 적정 범위에 있으면 아무 동작도 하지 않음
            else:
                pass
    time.sleep(0.001)
    
# 프로그램 종료 처리
window.close()
rgbledbar.off()
fan.off()
textlcd.clear()
# 콜백 해제
light.setCallback(None)
tphg.setCallback(None)