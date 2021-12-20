from binascii import Error
from socket import socket
import sys
import getopt

import Checksum
import BasicSender
import time

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    
    
    
    def __init__(self, dest, port, filename, debug=False, sackMode=False, window_size=5, timeout=0.5):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.seqno = 0                              # current seqno
        self.window_size = window_size              # send window size
        self.packet_size = 500                      # packet size
        self.data = [None, self.infile.read(self.packet_size)]                      # current data and next data
        self.timeout = timeout                      # timeout
        self.sackMode = sackMode                    # SACK mode
        if self.sackMode:
            self.ack_list = []                      # acknowlegded seqno in send window
        self.spacket = None                         # the packet to be sent
        self.rpacket = None                         # the packet last received - can be None if no packets received
        self.packets  = dict()                      # the packet dict which stores unacknowledged packets
        self.connected = False                      # connection status
        self.endseqno = None                        # end sequence number
        
    def get_data(self):
        """get the data to send and store next data to be sent

        Returns:
            (str, str): return a tuple which first element is the type of the packet 
            and the second element is the data in the packet
        """
        msg_type = 'data'
        self.data[0] = self.data[1]
        self.data[1] = self.infile.read(self.packet_size)
        if self.data[1] == '':
            msg_type = 'end'
        return (msg_type, self.data[0])

    def connect(self):
        """connect to the receiver

        Raises:
            Error: Connection failed for at least 5 times
        """
        self.spacket = self.make_packet('start', self.seqno, '')
        try_times = 0
        while not self.connected:
            self.send(self.spacket)
            try:
                self.rpacket = self.receive(self.timeout)
                if self.rpacket is not None:
                    self.rpacket = self.rpacket.decode()
            except:
                try_times += 1
                if try_times >= 5:
                    raise Error("Connection failed")
                continue
            if self.rpacket is not None:
                
                if Checksum.validate_checksum(self.rpacket):
                    # managed to connect
                    self.connected = True
                    print("Connected")
    
    def get_ack(self):
        """ get ack from rpacket and return the ack number
            if in sackMode, get the ack list from rpacket
        Returns:
            [int]: ack number
        """
        ack = self.split_packet(self.rpacket)[1]
        if self.sackMode:
            sack = ack.split(';')
            if sack[1] != '':
                self.ack_list = [int(i) for i in sack[1].split(',')]
            return int(sack[0])
        return int(ack)
    
    def store_packet(self, seqno, packet):
        self.packets[seqno] = {'packet': packet, 'time': time.time()}
    
    def send_data(self):
        """send data to receiver and store the packet in packets
        """
        # check if send window is full. if so, simply do nothing
        if self.seqno - self.window_start < self.window_size:
            # send window is not full yet
            msg_type, msg = self.get_data()
            self.spacket = self.make_packet(msg_type, self.seqno, msg)
            if msg_type == 'end':
                self.endseqno = self.seqno
            # store the packet information in the packet dict
            # so that we can examine timeout and resend it later
            self.store_packet(self.seqno, self.spacket)
            print("Sending packet [%d]: %s" % (self.seqno, self.spacket))
            self.send(self.spacket)
            self.seqno += 1
        
    def gbn_resend(self, start):
        """GBN policy. Resend the packets in the window

        Args:
            start ([int]): the start position of resend window
        """
        for i in range(start, self.seqno):
            self.spacket = self.packets[i]['packet']
            print("Resending packet [%d]: %s" % (i, self.spacket))
            self.send(self.spacket)
            
    def sack_resend(self):
        """Sack policy. Select all unacknowledged packets in send window and resend them all
        """
        for i in range(self.ack, self.seqno):
            if i not in self.ack_list:
                self.send(self.packets[i]['packet'])
            
    def receive_packet(self):
        """receive packet from receiver. 
        """
        try:
            self.rpacket = self.receive(self.timeout).decode()
            # print('seqno:', self.seqno, 'rpacket:', self.rpacket)
            if Checksum.validate_checksum(self.rpacket):
                self.ack = self.get_ack()
                if self.ack > self.window_start and self.ack <= self.seqno:
                    # received ack within the window
                    # update window start
                    while self.window_start < self.ack:
                        # remove the packet from the packet dict
                        del self.packets[self.window_start]
                        self.window_start += 1
        except:
            self.rpacket = None
            
    def check_timeout(self):
        """check if any packets in the window has timed out
        """
        now = time.time()
        for seqno, packet in self.packets.items():
            if now - packet['time'] > self.timeout:
                self.log("timeout: %d" % seqno)
                return seqno
        return None

    # Main sending loop.
    def start(self):
        print("Sender starting up")
        self.connect()
        self.ack = self.get_ack()
        self.seqno = self.ack
        self.window_start = self.seqno
        while self.connected:
            self.send_data()
            timeout_seqno = self.check_timeout()
            if timeout_seqno != None:
                if not self.sackMode:
                    self.gbn_resend(timeout_seqno)
                else:
                    self.sack_resend()
            
            self.receive_packet()
            if self.endseqno != None and self.ack > self.endseqno:
                # received end packet
                # disconnect
                self.connected = False
            
        
    def handle_response(self, response):
        if Checksum.validate_checksum(response):
            print("recv: %s" % response)
        else:
            print("recv: %s <--- CHECKSUM FAILED" % response)

    def handle_timeout(self):
        pass

    def handle_new_ack(self, ack):
        pass

    def handle_dup_ack(self, ack):
        pass

    def log(self, msg):
        if self.debug:
            print(msg)


'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print("RUDP Sender")
        print("-f FILE | --file=FILE The file to transfer; if empty reads from STDIN")
        print("-p PORT | --port=PORT The destination port, defaults to 33122")
        print("-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost")
        print("-d | --debug Print debug messages")
        print("-h | --help Print this usage message")
        print("-k | --sack Enable selective acknowledgement mode")

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:dk", ["file=", "port=", "address=", "debug=", "sack="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = "README"
    debug = False
    sackMode = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True
        elif o in ("-k", "--sack="):
            sackMode = True

    s = Sender(dest, port, filename, debug, sackMode)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
