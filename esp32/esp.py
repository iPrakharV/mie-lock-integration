import network
import socket
import time
import json
from machine import Pin
import os
import urequests as requests
import micropython
from ServoControl.KSTServo import KSTServo

# Configuration constants
WIFI_CONFIG_FILE = 'wifi_config.json'
DOMAIN = '#TODO'
SERVO_DATA_PIN = 12
UNLOCK_PERIOD = 10         # in seconds
STATUS_CHECK_INTERVAL = 5  # in seconds

class Lock:
    
    def __init__(self):
        self.ap = network.WLAN(network.AP_IF)
        self.sta = network.WLAN(network.STA_IF)
        self.ip = None
        self.servo = KSTServo(SERVO_DATA_PIN)
        self.last_status_check = time.time()
        self.locked = True
        self.username = None
        self.added = False
        

    def start_ap_mode(self):
        self.ap.active(True)
        self.ap.config(essid='ESP32-Setup', password='12345678')
        while not self.ap.active():
            pass
        self.ip = self.ap.ifconfig()[0]
        print('AP mode started, IP:', self.ip)
        return self.ip

    def serve_webpage(self, ip):
        addr = socket.getaddrinfo(ip, 80)[0][-1]
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        s.listen(1)
        print('Listening on', addr)

        try:
            gotCreds = False
            while not gotCreds:
                cl, addr = s.accept()
                print('Client connected from', addr)
                request = cl.recv(1024)
                
                if 'POST /save' in request:
                    try:
                        ssid, password, username = self.parse_post_request(request)
                        self.username = username
                        print("SSID: ", ssid)
                        print("Password: ", password)
                        with open(WIFI_CONFIG_FILE, 'w') as f:
                            json.dump({'ssid': ssid, 'password': password, 'username': username}, f)
                        
                        response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
                        response += 'Credentials saved. You can now close this page.'
                        cl.send(response)
                        cl.close()
                        time.sleep(1)
                        gotCreds = True
                    except Exception as e:
                        print('Error:', e)
                
                else:
                    response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
                    response += '<form action="/save" method="post">'
                    response += 'Username: <input type="text" name="username"><br>'
                    response += 'SSID: <input type="text" name="ssid"><br>'
                    response += 'Password: <input type="password" name="password"><br>'
                    response += '<input type="submit" value="Save">'
                    response += '</form>'
                    cl.send(response)
                    cl.close()
        except Exception as e:
            print('Server error:', e)
        finally:
            s.close()

    def connect_to_wifi(self):
        try:
            if WIFI_CONFIG_FILE not in os.listdir():
                print('Config file not found. Creating default config file.')
                with open(WIFI_CONFIG_FILE, 'w') as f:
                    json.dump({'ssid': '', 'password': '', 'username': ''}, f)
                raise OSError('Config file created, but no valid WiFi credentials found.')
            
            with open(WIFI_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                ssid = config.get('ssid')
                password = config.get('password')
                username = config.get('username')
                # print('WiFi credentials:', ssid, password, username)
            
            if not ssid or not password:
                raise OSError('Invalid WiFi credentials')

            self.sta.active(True)
            self.sta.connect(ssid, password)
            
            for _ in range(20):
                if self.sta.isconnected():
                    print('Connected to WiFi, IP:', self.sta.ifconfig()[0])
                    self.ip = self.sta.ifconfig()[0]
                    self.send_data_to_server(username)
                    return
                time.sleep(1)
            print('Failed to connect to WiFi')
            raise OSError('Failed to connect to WiFi with provided credentials')
        except OSError as e:
            print('Error:', e)
            raise

    def url_decode(self, s):
        decoded = ''
        i = 0
        while i < len(s):
            if s[i] == '%':
                decoded += chr(int(s[i+1:i+3], 16))
                i += 3
            else:
                decoded += s[i]
                i += 1
        return decoded

    def parse_post_request(self, request):
        try:
            headers, body = request.split(b'\r\n\r\n', 1)
            header_lines = headers.split(b'\r\n')
            ssid, password, username = None, None, None
            
            for line in header_lines:
                if line.startswith(b'Content-Length:'):
                    break
            
            body_data = body.decode('utf-8')
            data_pairs = body_data.split('&')
            
            for pair in data_pairs:
                key, value = pair.split('=')
                if key == 'ssid':
                    ssid = value
                elif key == 'password':
                    password = self.url_decode(value)
                elif key == 'username':
                    username = value
            
            return ssid, password, username
        
        except Exception as e:
            print('Error parsing POST request:', e)
            return None, None, None

    def get_mac_address(self):
        mac = network.WLAN().config('mac')
        return ':'.join('{:02x}'.format(b) for b in mac)

    def send_data_to_server(self, username):
        url = DOMAIN + '/add_device'
        data = {
            'device_id': self.get_mac_address(),
            'name': 'Lock: ' + self.get_mac_address(),
            'username': username,
            'ip_address': self.ip,
            'locked': self.locked
        }
        print("Sending this data: ", data)
        try:
            response = requests.post(url, json=data)
            response.close()
            if response.status_code == 201:
                self.added = True
                print('Device added successfully')
            else:
                print('Failed to add device, status code:', response.status_code)
        except Exception as e:
            print('Exception occurred while adding device:', e)

    def check_lock_status(self):
        url = DOMAIN + '/get_status'
        data = {'device_id': self.get_mac_address()}
        if not self.added:
            if self.username:
                self.send_data_to_server(self.username)
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                status = response.json().get('status')
                if status is not None:
                    self.locked = status
                    print('Lock status:', self.locked)
                    if not self.locked:
                        self.unlock()
                else:
                    print('Invalid response from server')
            elif response.status_code == 407:
                print('Device not found on server, adding device...')
                self.added = False
            else:
                print('Failed to fetch armed status from server, status code:', response.status_code)
                if self.username:
                    self.send_data_to_server(self.username)
            response = None
        except Exception as e:
            print('Exception occurred while checking armed status:', e)
    
    def unlock(self):
        self.servo.set_angle(-60, speed=1)
        time.sleep(UNLOCK_PERIOD)
        self.servo.set_angle(0, speed=1)
        

    def main(self):
        try:
            self.connect_to_wifi()
        except:
            self.start_ap_mode()
            self.serve_webpage(self.ip)
            self.connect_to_wifi()
        
        while True:
            current_time = time.time()
            if current_time - self.last_status_check > STATUS_CHECK_INTERVAL:
                micropython.mem_info()
                self.check_lock_status()
                self.last_status_check = current_time
        
        
    def remove_json(self):
        if WIFI_CONFIG_FILE in os.listdir():
            os.remove(WIFI_CONFIG_FILE)
            print('Config file removed')
        else:
            print('Config file not found')

if __name__ == '__main__':
    lock = Lock()
    # lock.main()
    # lock.remove_json()
