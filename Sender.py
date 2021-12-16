from socket import socket
import sys
import getopt

import Checksum
import BasicSender
import asyncio
import time

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False, sackMode=False, max_buf_size=5, timeout=0.5):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.current_seqno = 0
        self.max_buf_size = max_buf_size
        self.timeout = timeout
        if sackMode:
            raise NotImplementedError #remove this line when you implement SACK
 
    async def async_receive(self):
        return self.receive(self.timeout)

    # Main sending loop.
    def start(self):
        # raise NotImplementedError
        seqno = 0
        msg = self.infile.read(500)
        msg_type = None
        # firstly read the file and store all the packets
        buffer_size = self.max_buf_size
        send_window = []
        resend = False
        index = 0                   # index of the packet in the send_window
        while msg_type != 'end':
            while buffer_size == 0:
                pass
            if resend:
                if index >= len(send_window):
                    resend = False
                    msg = next_msg
                    continue
                print("resend: %s" % send_window[index][1])
                self.send(send_window[index][1])
                buffer_size -= 1
                index += 1
            else:
                next_msg = self.infile.read(500)
                if seqno == 0:
                    msg_type = 'start'
                elif next_msg == '':
                    msg_type = 'end'
                packet = self.make_packet(msg_type, seqno, msg)
                # send the packets
                send_window.append((seqno, packet))
                self.send(packet)
                print("sent: %s" % packet)
                buffer_size -= 1
                seqno += 1
                msg = next_msg
            
            # wait for the ack
            try:
                self.async_receive().send(None)
            except StopIteration as e:
                # notice that e.value which should be ack packet can be lost
                # thus, we can get None here
                # in that case, we should resend the packet
                response = e.value
                if response is not None:
                    response = response.decode()
                    if int(response.split('|')[1]) == send_window[0][0] + 1:
                        # received ideal ack
                        send_window.pop(0)
                        self.handle_response(response)
                        buffer_size += 1
                else:
                    # resend the packet
                    resend = True
                    buffer_size += 1
                    index = 0
                    
                # received ack for a packet that is not by the ideal order
                # simply drop it
            except TimeoutError:
                print("TimeoutError")
                self.handle_timeout()
            
        
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
    filename = "README.md"
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
