import queue




#Status:
status_queue = queue.Queue()

def get_status():
    if not status_queue.empty():
        return status_queue.get()
    return " "

def update_status_info(new_status):
    status_queue.put(f": {new_status}")

def update_status_warning(new_status):
    status_queue.put(f"Warning: {new_status}")

def update_status_error(new_status):
    status_queue.put(f"Error: {new_status}")

def update_status_critical(new_status):
    status_queue.put(f"Criticial: {new_status}")


#Values:
values_queue = queue.Queue()

def get_values():
    if not values_queue.empty():
        return values_queue.get()
    return " "

def update_values(new_value):
    values_queue.put(new_value)