import websocket
import ssl
import _thread
import time
import json

class News():

    def __init__(self, api_key, api_secret, target_symbols, on_news):
        self.api_key = api_key
        self.api_secret = api_secret
        self.target_symbols = target_symbols
        self.on_news = on_news

    def on_message(self, ws, message):

        try:
            msgs = json.loads(message)
            for msg in msgs:
                print(msg)

                # if this if statment isnt the first to run it will not run
                # probbly the dumbest thing ive encountered in python
                if msg['T'].strip() == 'n':
                    # got news, call the function
                    self.on_news({
                        "headline": msg["headline"],
                        "summary": msg["summary"],
                        "created_at": msg["created_at"],
                        "updated_at": msg["updated_at"],
                        "symbols": msg["symbols"],
                    })

                if msg['msg'] == 'authenticated' and msg['T'] == 'success':
                    ws.send(json.dumps({"action":"subscribe","news": self.target_symbols}))
                
        except Exception as error:
            print(error)


    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        ws.send(json.dumps({"action": "auth","key": self.api_key,"secret": self.api_secret}))

    def run(self):
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp("wss://stream.data.alpaca.markets/v1beta1/news",
                                on_open=self.on_open,
                                on_message=self.on_message,
                                on_error=self.on_error,
                                on_close=self.on_close)

        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})