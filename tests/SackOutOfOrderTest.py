import random

from tests.BasicTest import BasicTest


class SackOutOfOrderTest(BasicTest):
    def __init__(self, forwarder, input_file):
        super(SackOutOfOrderTest, self).__init__(forwarder, input_file, sackMode = True)
        self.tick_times = 0                              # tick_times records the number of ticks
        self.temp_out_queue = []                         # temp_out_queue records the packets that are sent from sender
        # later we will shuffle the packets in temp_out_queue and send them to receiver to simulate out of order
        
    def handle_tick(self, tick_interval):
        self.tick_times += 1
        if self.tick_times % 50 != 0:
            # store the packet from sender in temp_out_queue
            # wait for 50 ticks before sending the packet at once
            self.temp_out_queue.extend(filter(lambda x: x.msg_type != 'sack', self.forwarder.out_queue))
            self.forwarder.out_queue = filter(lambda x: x.msg_type == 'sack', self.forwarder.out_queue)
        else:
            # send the packet from temp_out_queue
            # before sending the packet to receiver, shuffle the packets to simulate out-of-order packets
            # 50 is a hyper-parameter, you can change it to any number you want
            # if it is too small, the amount of stored packets will be too small, thus shuffle may be ineffective
            # therefore, I chosed 50 ticks as the interval to send packets
            self.temp_out_queue = list(set(self.temp_out_queue))
            self.forwarder.out_queue = self.temp_out_queue
            random.shuffle(self.forwarder.out_queue)
            self.temp_out_queue = []
            # print('tick', self.tick_times,' :' ,self.forwarder.out_queue)