import websocket
import ssl
import _thread
import time
import json

class News():

    def __init__(self, api_key, api_secret, on_news):
        self.api_key = api_key
        self.api_secret = api_secret
        self.on_news = on_news

    def on_message(self, ws, message):
        # print(message)
        try:
            msgs = json.loads(message)
            for msg in msgs:
                if msg['msg'] == 'authenticated' and msg['T'] == 'success':
                    ws.send(json.dumps({"action":"subscribe","news":['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSM', 'META', 'AVGO', 'AMD']}))
                elif msg['T'] == 'n':
                    # got news, call the function
                    self.on_news({
                        "headline": msg["headline"],
                        "summary": msg["summary"],
                        "created_at": msg["created_at"],
                        "updated_at": msg["updated_at"],
                        "symbols": msg["symbols"],
                    })
                else:
                    print(msg)
        except Exception as error:
            print(error)


    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        ws.send(json.dumps({"action": "auth","key": self.api_key,"secret": self.api_secret}))

    def run(self):
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("wss://stream.data.alpaca.markets/v1beta1/news",
                                on_open=self.on_open,
                                on_message=self.on_message,
                                on_error=self.on_error,
                                on_close=self.on_close)

        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})