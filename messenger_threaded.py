from messaging import Message, QueueManager
manager = QueueManager(available_ports = ['umts-1.1', 'umts-2.3'])
message_queue = [Message(number='6681610296', text='esta es la prueba '+str(i)) for i in range(1, 3)]
for i in range(len(message_queue)):
    current_message = message_queue.pop()
    curr = manager.send()
    curr.join()
