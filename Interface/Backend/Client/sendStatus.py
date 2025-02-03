import queue

status_queue = queue.Queue()
values_queue = queue.Queue()


def get_status():
    if not status_queue.empty():
        return status_queue.get()
    return " "

def get_values():
    if not values_queue.empty():
        return values_queue.get()
    return " "

def update_values(new_value):
    values_queue.put(new_value)
    
def update_status(new_status):
    status_queue.put(new_status)
    #print(f"Status updated: {new_status}")
