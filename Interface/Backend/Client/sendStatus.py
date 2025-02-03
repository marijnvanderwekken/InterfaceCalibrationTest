import queue

status_queue = queue.Queue()



def get_status():
    if not status_queue.empty():
        return status_queue.get()
    return " "

def update_status(new_status):
    status_queue.put(new_status)
    print(f"Status updated: {new_status}")
