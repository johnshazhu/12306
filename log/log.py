import datetime

file = None

def log_file_name():
    return datetime.datetime.now().strftime('%Y%m%d') + '.txt'

def init_log(save_log):
    global file
    if save_log:
        file = open('log/' + log_file_name(), 'wb')
        file.write("ignore this err...'O' is not in list".encode())

def log(msg):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'{now}\t{msg}')
    if file is not None:
        file.write((msg + '\n').encode())
    if msg == 'exit':
        log_exit()

def log_exit():
    if file is not None:
        file.close()