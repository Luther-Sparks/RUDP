# RUDP
This tiny project is to implement reliable UDP protocol according to Computer Network course in Fudan University 2021 Autumn.
## Implemented Features
- The Go-Back-N policy and the Selective Repeat policy. You can get to know more about these policies in the [source code](./Sender.py).
- The simulator for [packet random drop](tests/RandomDropTest.py), [packet arrives out of order](tests/OutOfOrderTest.py) and [Sender receive duplicated ack](tests/DupPacketTest.py).

## FIXME
- [ ] Due to the decoding problem, this project only supports utf-8. Which means photos are not supported.
