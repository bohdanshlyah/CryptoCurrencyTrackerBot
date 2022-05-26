class Config:
    def __init__(self):
        self._chat_id = None
        self._tracking_status = False
        self._interval = 3600
        self._pair = "BTC_USD"

    @property
    def status(self):
        return self._tracking_status

    @status.setter
    def status(self, new_status):
        self._tracking_status = new_status

    @property
    def chat_id(self):
        return self._chat_id

    @chat_id.setter
    def chat_id(self, id):
        self._chat_id = id

    @property
    def pair(self):
        return self._pair

    @pair.setter
    def pair(self, new_pair):
        self._pair = new_pair

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, new_interval):
        self._interval = new_interval
