import Tkinter
import logging
import time
import threading
import ttk
from EMS_API import EMS_API

api = EMS_API()
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                        level=logging.DEBUG)

# =========GUI DESCRIPTION==========
root = Tkinter.Tk()
root.wm_title('EMS Calc')

label_from = ttk.Label(root, text='From location:')
label_from.grid(row=0, column=0, sticky='e')

entry_from = ttk.Entry(root)
entry_from.grid(row=0, column=2)

label_to = ttk.Label(root, text='To location:')
label_to.grid(row=1, column=0, sticky='e')

combobox_from = ttk.Combobox(root, values=[u"..."], height=10, width=30)
combobox_from.grid(row=0, column=2)

combobox_to = ttk.Combobox(root, values=[u"..."], height=10, width=30)
combobox_to.grid(row=1, column=2)

type_of_package_var = Tkinter.IntVar()

label_type = ttk.Label(root, text='Type of package:')
label_type.grid(row=2, column=0, sticky='e',)

radiobutton_doc = ttk.Radiobutton(root, variable=type_of_package_var, value=1, text='Documents')
radiobutton_doc.grid(row=2, column=2, sticky='w')

radiobutton_attr = ttk.Radiobutton(root, variable=type_of_package_var, value=2, text='Commodity Investments')
radiobutton_attr.grid(row=3, column=2, sticky='w')

label_weight = ttk.Label(root, text='Weight:')
label_weight.grid(row=4, column=0, sticky='e')

entry_weight = ttk.Entry(root)
entry_weight.grid(row=4, column=2, sticky='w')

label_cost = ttk.Label(root, text='Cost of delivery:')
label_cost.grid(row=5, column=0, sticky='e')
label_cost['state'] = 'disabled'

label_cost_of_delivery = ttk.Label(root, text='')
label_cost_of_delivery.grid(row=5, column=2, sticky='w')

label_duration = ttk.Label(root, text='Duration of delivery:')
label_duration.grid(row=6, column=0, sticky='e')
label_duration['state'] = 'disabled'

label_duration_of_delivery = ttk.Label(root, text='')
label_duration_of_delivery.grid(row=6, column=2, sticky='w')

button_calculate = ttk.Button(root, text='Calculate')
button_calculate.grid(row=7, column=2)

label_status = ttk.Label(root, text='')
label_status.grid(row=8, column=0)
# =========END GUI DESCRIPTION==========


def new_thread(daemon=False):
    """
    Decorator for launch function in another thread
    :param func: function, which will be launch in another thread
    :param demon: if demon is True, than thread dies with main thread, i.e. will be work all time.
    By default it's False.
    :return: return pointer to function, witch will be run in another thread
    """
    def wrapper(func):
        def new_thread_func(*args, **kwargs):
            thread = threading.Thread(target=func, args=args, kwargs=kwargs)
            if daemon:
                thread.daemon = True
            else:
                thread.daemon = False
            thread.start()
            return thread

        return new_thread_func

    return wrapper



@new_thread(daemon=True)
def connection_status():
    """
    Check heartbeat of EMS API
    :return:
    """
    while True:
        if api.heartbeat():
            label_status['text'] = 'API is available'
            label_status['foreground'] = 'green'
        else:
            label_status['text'] = 'API is unavailable'
            label_status['foreground'] = 'red'
        time.sleep(5)


class Locations:
    def __init__(self, *args):
        self.locations = {}
        self.args = args

    @new_thread(daemon=False)
    def load_locations(self):
        logging.debug('Loading locations: Start loading locations')
        for type in self.args:
            locations_in_json = api.get_locations(type)
            for location in locations_in_json:
                self.locations[location['name']] = {
                    'value': location['value'],
                    'type': location['type'],
                }
        logging.debug('Loading locations: '+ str(len(self.locations))+ ' locations has been loaded')


connection_status()
root.mainloop()
