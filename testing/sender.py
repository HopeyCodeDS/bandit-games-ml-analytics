#sender

import pika

class Sender(object):

    def send(self, str):
	connection = pika.BlockingConnection(pika.ConnectionParameters(
        	host='localhost'))
	channel = connection.channel()


	channel.queue_declare(queue='game_data_queue')

	channel.basic_publish(exchange='battleshipDataExchange',
        	              routing_key='queue1',
                	      body='msg from python : echo ' + str)
	print(" [x] Sent 'test'")
	connection.close()
