import gevent
from gevent.queue import Queue
from gevent import Greenlet
from actor import Actor

with open('config.yaml') as f:
    config = yaml.load(f)

max_attempts = config['max_attempts']
batch_size = config['batch_size']
openvox_endpoint = config['openvox_endpoint']#'http://192.168.5.250:80/sendsms'
messages_collection_url = config['messages_collection_url']
available_ports = config['ports']
cooling_time = config['cooling_time']
poll_wait = config['poll_wait'] #waiting time for db polling
messages = []
p = {
    'username' : config['username'],
    'password' : config['password'],
    'port' : '',
    'phonenumber' : '',
    'message' : ''
}

mongo_client = MongoClient(messages_collection_url)
messages_db = mongo_client.messages

def save_to_mongo(message):
    messages_db.find_one_and_update({'_id': message['_id']},
    {'$set':
        {
        'status': message['status'],
        'attempts': message['attempts'],
        'report': message['report']
        }
    })

def clean():
    pass

def send (message, params, url=openvox_endpoint):
    '''
    Sends request to url with params as parameters and requeues port when
    the request is complete. (Has optional cooling_time)
    '''
    def requeue(cooling_time = None):
        if cooling_time:
            #wait cooling_time seconds
            pass
        available_ports.push(params['port'])
    # response = urlopen('http://httpbin.org/get?datetime={}'.format(dt.strftime(dt.now(), '%Y-%m-%d_%H:%M:%S')))
    response = clean(rget(p, callback = requeue))
    #update message status
    message['status'] = response['report']['status']
    message['attempts']+=1
    message['report'] = response['report']
    return response, message

def fetch_messages():
    '''
    Fetches batch_size messages from messages_collection_url
    '''
    return messages_db.find({'status':{'$ne': 'sent'}, 'attempts' : {'$lt': max_attempts}}).batchSize(batch_size)

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


while True:
    message = get_current_message()
    p['port'] = get_current_port()
    p['phonenumber'] = message.number
    p['message'] = message.text
    response, message = send(message, p)
    save_to_mongo(message)
