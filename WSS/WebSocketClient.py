import websocket
import logging
import time
import datetime
from threading import Thread, Event


class Connection(Thread):
    def __init__(
            self,
            *arge,
            url,
            onOpen=None,
            onMessage=None,
            onClose=None,
            onError=None,
            log_level=None,
            reconnect_interval=30,
            **kwargs):

        self._url = url
        self._onOpen = onOpen
        self._onClose = onClose
        self._onMessage = onMessage
        self._onError = onError
        self._reconnect_interval = reconnect_interval if reconnect_interval else 10

        self._socket = None
        self.isConnected = Event()
        self._disconnecte_required = Event()
        self._reconnect_required = Event()
        self._lastReceiveTime = datetime.datetime.now()

        self._log = None
        self._init_log(log_level)

        Thread.__init__(self)
        self.daemon = True

    def _init_log(self, log_level):
        self._log = logging.getLogger(__name__)
        self._log.setLevel(level=log_level)
        formatter = logging.Formatter('%(asctime)s|%(levelname)s - %(message)s')

        handler = logging.FileHandler("socket.log")
        handler.setLevel(log_level)
        handler.setFormatter(formatter)
        self._log.addHandler(handler)

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        self._log.addHandler(console)

    def _connect(self):
        self._log.debug('鍒濆鍖杦ebsocket骞跺彂璧烽摼鎺�')
        self._socket = websocket.WebSocketApp(
            self._url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_close=self._on_close,
            on_error=self._on_error
        )
        self._socket.run_forever()

        # 浠ヤ笅鐢ㄤ簬閲嶈繛
        while self._reconnect_required.is_set():
            if not self._disconnecte_required.is_set():
                self._socket.sock = None
                delay = self._reconnect_interval
                while delay > 0:
                    self._log.info('%ds 鍚庨噸杩�' % delay)
                    time.sleep(1)
                    delay -= 1
                self._socket.keep_running = True
                self._socket.run_forever()

    def run(self):
        self._connect()

    def send(self, msg):
        self._socket.send(msg)

    def disconnect(self):
        self._log.debug("涓诲姩鏂紑")
        self._reconnect_required.clear()
        self._disconnecte_required.set()
        if self._socket:
            self._socket.close()
        self.join(1)

    def reconnect(self):
        self._log.debug("涓诲姩閲嶈繛")
        self.isConnected.clear()
        self._reconnect_required.set()
        if self._socket:
            self._socket.close()

    def _on_open(self, ws):
        self._log.debug('杩炴帴鎴愬姛')
        self.isConnected.set()
        self._reconnect_required.set()
        if self._onOpen:
            self._onOpen()
        self._startCheckDataTimer()

    def _on_message(self, ws, message):
        self._lastReceiveTime = datetime.datetime.now()
        if self._onMessage:
            self._onMessage(message)

    def _on_close(self, ws):
        self.isConnected.clear()
        self._log.debug('閾炬帴宸茬粡鍏抽棴')
        if self._onClose:
            self._onClose()

    def _on_error(self, ws, error):
        self._log.debug('websocket鍑洪敊 %s' % error)
        self.isConnected.clear()
        if self._onError:
            self._onError(error)

    def _lastChance(self):
        span = (datetime.datetime.now() - self._lastReceiveTime).total_seconds()
        if span >= 30:
            self._socket.close()

    def _loop(self):
        while self.isConnected.is_set():
            time.sleep(1)
            self._lastChance()

    def _startCheckDataTimer(self):
        self._checkDataThread = Thread(target=self._loop, name='CheckData ' + self.name)
        self._checkDataThread.start()
