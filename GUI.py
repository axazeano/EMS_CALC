# coding=utf-8
import tkinter
import logging
import re
import time
import threading
import tkinter.ttk as ttk
from EMS_API import EMS_API

api = EMS_API()
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                        level=logging.DEBUG)

# =========GUI DESCRIPTION==========
root = tkinter.Tk()
root.wm_title('EMS Calc')

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

class LocalDeliveryGUI:
    def __init__(self, master):

        self.location = 'russia'

        self.label_from = ttk.Label(master, text='From location:')
        self.label_from.grid(row=0, column=0, sticky='e')

        self.label_to = ttk.Label(master, text='To location:')
        self.label_to.grid(row=1, column=0, sticky='e')

        self.combobox_from = ttk.Combobox(master, values=[u"..."], height=10, width=30)
        self.combobox_from.grid(row=0, column=2)

        self.combobox_to = ttk.Combobox(master, values=[u"..."], height=10, width=30)
        self.combobox_to.grid(row=1, column=2)

        self.label_weight = ttk.Label(master, text='Weight:')
        self.label_weight.grid(row=4, column=0, sticky='e')

        self.entry_weight = ttk.Entry(master)
        self.entry_weight.grid(row=4, column=2, sticky='w')

        self.label_cost = ttk.Label(master, text='Cost of delivery:')
        self.label_cost.grid(row=5, column=0, sticky='e')
        self.label_cost['state'] = 'disabled'

        self.label_cost_of_delivery = ttk.Label(master, text='')
        self.label_cost_of_delivery.grid(row=5, column=2, sticky='w')
        self.label_cost_of_delivery['state'] = 'disabled'

        self.label_duration = ttk.Label(master, text='Duration of delivery:')
        self.label_duration.grid(row=6, column=0, sticky='e')
        self.label_duration['state'] = 'disabled'

        self.label_duration_of_delivery = ttk.Label(master, text='')
        self.label_duration_of_delivery.grid(row=6, column=2, sticky='w')
        self.label_duration_of_delivery['state'] = 'disabled'

        self.button_calculate = ttk.Button(master, text='Calculate', command=self.calculate_delivery)
        self.button_calculate.grid(row=7, column=2, sticky='e')

        self.locations = Locations('russia')

        GUIControls.set_location_to_comboboxes(self.locations, self.combobox_from, self.combobox_to)

    def calculate_delivery(self):
        calculate_results = api.calculate(to_location=self.locations.locations[self.combobox_to.get()]['value'],
                                          from_location=self.locations.locations[self.combobox_from.get()]['value'],
                                          weight=self.entry_weight.get())
        result = calculate_results
        self.label_cost['state'] = 'enable'
        self.label_duration['state'] = 'enable'
        self.label_cost_of_delivery['state'] = 'enable'
        self.label_duration['state'] = 'enable'
        self.label_duration_of_delivery['state'] = 'enable'

        print(calculate_results)

        self.label_cost_of_delivery['text'] = result['rsp']['price'] + ' RUB'
        self.label_duration_of_delivery['text'] = result['rsp']['term']['min'] + ' - ' + result['rsp']['term']['max'] + ' days'


class InternationalDeliveryGUI:
    def __init__(self, master):

        self.type_of_package_var = tkinter.StringVar()

        self.label_to = ttk.Label(master, text='To location:')
        self.label_to.grid(row=0, column=0, sticky='e')

        self.combobox_to = ttk.Combobox(master, values=[u"..."], height=10, width=30)
        self.combobox_to.grid(row=0, column=2)

        self.label_type = ttk.Label(master, text='Type of package:')
        self.label_type.grid(row=1, column=0, sticky='e',)

        self.radiobutton_doc = ttk.Radiobutton(master, variable=self.type_of_package_var, value='doc', text='Documents')
        self.radiobutton_doc.grid(row=1, column=2, sticky='w')

        self.radiobutton_attr = ttk.Radiobutton(master, variable=self.type_of_package_var, value='att', text='Commodity Investments')
        self.radiobutton_attr.grid(row=2, column=2, sticky='w')

        self.label_weight = ttk.Label(master, text='Weight:')
        self.label_weight.grid(row=3, column=0, sticky='e')

        self.entry_weight = ttk.Entry(master)
        self.entry_weight.grid(row=3, column=2, sticky='w')

        self.label_cost = ttk.Label(master, text='Cost of delivery:')
        self.label_cost.grid(row=4, column=0, sticky='e')
        self.label_cost['state'] = 'disabled'

        self.label_cost_of_delivery = ttk.Label(master, text='')
        self.label_cost_of_delivery.grid(row=4, column=2, sticky='w')

        self.button_calculate = ttk.Button(master, text='Calculate', command=self.calculate_delivery)
        self.button_calculate.grid(row=5, column=2, sticky='e')

        self.locations = Locations('countries')

        GUIControls.set_location_to_comboboxes(self.locations, self.combobox_to)

    def calculate_delivery(self):
        calculate_results = api.calculate(to_location=self.locations.locations[self.combobox_to.get()]['value'],
                                          type=self.type_of_package_var.get(),
                                          weight=self.entry_weight.get())
        result = calculate_results
        self.label_cost['state'] = 'enable'
        self.label_cost_of_delivery['state'] = 'enable'
        print(calculate_results)
        self.label_cost_of_delivery['text'] = result['rsp']['price'] + ' RUB'

# =========END GUI DESCRIPTION==========

class GUIControls:
    def __init__(self):
        pass

    @staticmethod
    @new_thread(daemon=False)
    def set_location_to_comboboxes(location, *comboboxes):
        for combobox in comboboxes:
            combobox['state'] = 'disabled'
            combobox.set('Loading locations...')

        location.load_locations()

        for combobox in comboboxes:
            combobox['state'] = 'enable'
            combobox.set('Select location')
            for value in location.locations.keys():
                combobox['values'] += (value,)
            # combobox['values'] = location.locations.keys()


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
        self.replacements = {
            u'край': u' край',
            u'округ': u' округ',
            u'автономный': u' автономный ',
            u'область': u' область',
            u'автономная': u' автономная ',
            u'республика': u' республика',
            u'район': u' район',
            u'промышленнный': u' промышленный ', # sic!
            u'осетия': u' Осетия',
            u'алания': u'Алания',
            u'долгано': u' Долгано',
        }

    def load_locations(self):
        logging.debug('Loading locations: Start loading locations')
        for type in self.args:
            locations_in_json = api.get_locations(type)
            for location in locations_in_json:
                self.locations[self.normalize_location(location['name'])] = {
                    'value': location['value'],
                    'type': location['type'],
                }
        logging.debug('Loading locations: '+ str(len(self.locations))+ ' locations has been loaded')

    def normalize_location(self, location):
        location = location.capitalize()
        pattern = ''
        # pattern prepare
        for key in self.replacements:
            pattern += '(%s)|' % key
        # remove redundant '|' at the end of pattern
        pattern = pattern[:-1]
        search_results = re.findall(pattern, location)

        if search_results:
            for key in search_results:
                for x in key:
                    if x:
                        location = location.replace(x, self.replacements[x])
        return location


notebook = ttk.Notebook(root)
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)
notebook.add(tab1, text="Local delivery")
notebook.add(tab2, text="International delivery")
notebook.pack()

status_frame = ttk.Frame(root)
status_frame.pack()

label_status = ttk.Label(status_frame, text='Status:')
label_status.grid(row=0, column=0, sticky='e')

test = LocalDeliveryGUI(tab1)

test2 = InternationalDeliveryGUI(tab2)


root.mainloop()
