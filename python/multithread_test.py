
import threading
# import Queue

def thread1():
	count1 = 0

	while True:

		count1 += 1

		if count1 % 10000000 == 0:
			print('Thread1 is at', count1)



def message_queued(name):
	print('I was printed', name)


class thread(threading.Thread):

	def __init__(self, name):
		threading.Thread.__init__(self)
		self.count = 0
		self.name = name


	def run(self):

		while True:

			self.count += 1
			
			if self.count % 10000000 == 0:
				self.print_output()
				message_queued(self.name)
	
	def print_output(self):
		print('Thread', self.name, 'is at', self.count)

new_thread = thread('thread2')

new_thread.start()

if __name__ == "__main__":

	thread1()