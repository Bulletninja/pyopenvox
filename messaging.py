from time import sleep
from collections import deque
from threading import Thread, Lock
import weakref
import requests
import queue

class Message:
    """Message object"""
    def __init__(self, number = None, text = None, attempts = 0, status = "not sent", due_date = None):
        """
        number: cellphone number
        text: the message itself
        attempts: number of attempts so far (usually, you don't want to mess with this param manually)
        status: message status: ['succesful', 'not sent', 'failed']
        due_date: due date in ISO 8601 format (date only, not datetime)
        """
        self.number = number
        self.text = text
        self.attempts = attempts
        self.status = status
        self.due_date = due_date

    def update_status(self, status):
        self.status = status

def run_async2(f, lock=None):
    import weakref
    from threading import Thread
    def args_wrapper(*args, **kwargs):
        class FunctionRunner(Thread):
            def run(self):
                if lock is not None: lock.acquire()
                try:
                    self.result = f(*args, **kwargs)
                finally:
                    if lock is not None: lock.release()
        t = FunctionRunner()
        t.start()
        def callback():
            t.join()
            return t.result
        proxy = weakref.proxy(callback)
        return proxy
    return args_wrapper

def run_async(func):
	from threading import Thread
	from functools import wraps

	@wraps(func)
	def async_func(*args, **kwargs):
		func_hl = Thread(target = func, args = args, kwargs = kwargs)
		func_hl.start()
		return func_hl

	return async_func

class QueueManager:
    """
    Manages modules and ports.
    There are 3 possible status: "available", "unavailable" and "down"
    the difference between "unavailable" and "down" is that, in the former case
    the corresponding port is working, and therefore temporarily unavailable;
    and the latter, it means the port is down for (almost surely) unplanned reasons
    """
    ports = ['umts-1.1', 'umts-2.3']#list of ports
    def __init__(self, username = 'admin', password = 'admin', available_ports = ports, wait_time = 15):
        """
        available_ports: queue of available ports (all the ports initially, unless otherwise stated)
        waiting_time: port waits this time (in seconds) to make itself available after getting a response
        """
        tmp = available_ports
        self.available_ports = queue.Queue()
        [self.available_ports.put(element) for element in tmp]
        print("available_ports: ", available_ports)
        self.wait_time = wait_time
        self.username = username
        self.password = password

    def takedown(self, port):
        """
        takes down a port
        """
        pass

    @run_async2
    def requeue(self, response, message, params):
        sleep(self.wait_time)
        print("requeueing port {}.".format(params['port']))
        self.available_ports.put(params['port'])
        message.status = response
        return response

    @run_async2
    def send(self, message, cb = requeue, url='http://192.168.5.250:80/sendsms'):
        le_port = self.available_ports.get()
        p = {
            'username' : self.username,
            'password' : self.password,
            'port' : le_port,
            'phonenumber' : message.number,
            'message' : message.text
        }
        print("sending message through port {}: ".format(le_port), message)
        r = requests.get(url, params = p)
        print("message sent")
        response = cb(self, r, message, p)
        print(response)
        return response

class Messages(object):
    """Messages methods."""
    def __init__(collection_url, max_attempts, batch_size):
        self.messages_collection_url = collection_url
        self.max_attempts = max_attempts
        self.batch_size = batch_size

    def fetch_messages():
        '''
        Fetches batch_size messages from messages_collection_url
        '''
        return messages_db.find({'status':{'$ne': 'sent'}, 'attempts' : {'$lt': self.max_attempts}}).batchSize(self.batch_size)

    def get_current_message():
        '''
        Returns "current" message. Fetches messages from the corresponding
        collection (in batch_size batches) if necessary (when messages is empty).
        If there is no available messages waits for poll_time seconds.
        '''
        messages = fetch_messages() if messages.isEmpty()
        if messages.count() == 0:
            #wait poll_time seconds
            pass
        return messages.pop()

    def save_to_mongo(message):
        messages_db.find_one_and_update({'_id': message['_id']},
        {'$set':
            {
            'status': message['status'],
            'attempts': message['attempts'],
            'report': message['report']
            }
        })

class Ports(object):
    """docstring for Ports."""
    def __init__(self, arg):
        super(Ports, self).__init__()
        self.arg = arg
