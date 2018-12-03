class Congestion():
  def __init__(self):
    """
      description: init params of Congestion Control
      cwnd: congestion window
      ssthresh: threshold of congestion window
      dupACKcount: number of duplicate ACK
      status: 0/1/2
    """
    self.cwnd = 1
    self.ssthresh = 64
    self.dupACKcount = 0 
    self.status = 0
  
  def update(self, event):
    """
      description: update congestion control status according to the event
      :param event: event type(DUP_ACK, NEW_ACK, TIMEOUT)
      :type event: str
      :return: None
    """
    if self.status == 0:
      if event == 'DUP_ACK':
        self.dupACKcount += 1
      elif event == 'NEW_ACK':
        self.cwnd += 1
        self.dupACKcount = 0
      elif event == 'TIMEOUT':
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dupACKcount = 0

      if self.dupACKcount == 3:
        self.status = 2
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.ssthresh + 3
      elif self.cwnd >= self.ssthresh:
        self.status = 1

    elif self.status == 1:
      if event == 'NEW_ACK':
        self.cwnd += 1 / self.cwnd
        self.dupACKcount = 0
      elif event == 'DUP_ACK':
        self.dupACKcount += 1
      elif event == 'TIMEOUT':
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dupACKcount = 0
        self.status = 0

      if self.dupACKcount == 3:
        self.status = 2
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.ssthresh + 3
    
    elif self.status == 2:
      if event == 'DUP_ACK':
        self.cwnd += 1
      elif event == 'NEW_ACK':
        self.status = 1
        self.cwnd = self.ssthresh
        self.dupACKcount = 0
      elif event == 'TIMEOUT':
        self.status = 0
        self.ssthresh = self.cwnd / 2
        self.cwnd = 1
        self.dupACKcount = 0
