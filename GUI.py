# coding=utf-8
from concurrent import futures
import tkinter
import logging
import re
import tkinter.ttk as ttk
from EMS_API import EMS_API

api = EMS_API()
logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)

# Define root element of GUI application
root = tkinter.Tk()
# Set title to main window
root.wm_title('EMS Calc')


class LocalDeliveryGUI:
    """
    GUI for work with local deliveries
    """
    def __init__(self, master):
        # root object for created gui elements
        self.master = master
        # local ThreadPool for execute future tasks
        self.executor = futures.ThreadPoolExecutor(max_workers=3)
        # Draw GUI elements, define in _draw_elements
        self._draw_elements()
        # Type of location, witch will be loaded
        self.locations = Locations('russia')
        self.executor.submit(self.locations.load_locations).add_done_callback(self.set_locations)
        # self.executor.submit(Locations, 'russia').add_done_callback(self.set_locations)
        # Get max weight from api
        self.max_weight = None
        self.executor.submit(api.get_max_weight).add_done_callback(self.set_max_weight)
        print(self.max_weight)

    def _draw_elements(self):
        """
        Add elements to master
        """
        self.label_from = ttk.Label(self.master, text='From location:')
        self.label_from.grid(row=0, column=0, sticky='e')

        self.label_to = ttk.Label(self.master, text='To location:')
        self.label_to.grid(row=1, column=0, sticky='e')

        self.combobox_from = ttk.Combobox(self.master, values=[], height=10, width=30)
        self.combobox_from.grid(row=0, column=2)

        self.combobox_to = ttk.Combobox(self.master, values=[], height=10, width=30)
        self.combobox_to.grid(row=1, column=2)

        self.label_weight = ttk.Label(self.master, text='Weight:')
        self.label_weight.grid(row=4, column=0, sticky='e')

        self.entry_weight = ttk.Entry(self.master)
        self.entry_weight.grid(row=4, column=2, sticky='w')

        self.label_cost = ttk.Label(self.master, text='Cost of delivery:')
        self.label_cost.grid(row=5, column=0, sticky='e')
        self.label_cost['state'] = 'disabled'

        self.label_cost_of_delivery = ttk.Label(self.master, text='')
        self.label_cost_of_delivery.grid(row=5, column=2, sticky='w')
        self.label_cost_of_delivery['state'] = 'disabled'

        self.label_duration = ttk.Label(self.master, text='Duration of delivery:')
        self.label_duration.grid(row=6, column=0, sticky='e')
        self.label_duration['state'] = 'disabled'

        self.label_duration_of_delivery = ttk.Label(self.master, text='')
        self.label_duration_of_delivery.grid(row=6, column=2, sticky='w')
        self.label_duration_of_delivery['state'] = 'disabled'

        self.button_calculate = ttk.Button(self.master, text='Calculate')

        # Click on button adds new job to ThreadPool, executes it,
        # and after execute invokes function in add_done_callback
        # We assign lambda expression as a command for prevent immediately execute of a function
        self.button_calculate['command'] = lambda: self.executor.submit(self.calculate_delivery). \
            add_done_callback(self.calculate_delivery_done)
        self.button_calculate.grid(row=7, column=2, sticky='e')

    def calculate_delivery(self):
        if not self.validate():
            return
        else:

            to_location = self.locations[self.combobox_to.get()]['value']
            from_location = self.locations[self.combobox_from.get()]['value']
            weight = self.entry_weight.get()

            return api.calculate(to_location=to_location,
                                 from_location=from_location,
                                 weight=weight)

    def calculate_delivery_done(self, future):
        calculate_results = future.result()
        if calculate_results:
            # Enable labels
            self.label_cost['state'] = 'enable'
            self.label_duration['state'] = 'enable'
            self.label_cost_of_delivery['state'] = 'enable'
            self.label_duration['state'] = 'enable'
            self.label_duration_of_delivery['state'] = 'enable'

            # Set result to labels
            self.label_cost_of_delivery['text'] = calculate_results['price'] + ' RUB'
            self.label_duration_of_delivery['text'] = "{} - {} days".format(calculate_results['min_days'],
                                                                            calculate_results['max_days'])

    def validate(self):
        errors = []
        # ===Check combobox_from=====
        if self.combobox_from.get() == '' or self.combobox_from.get() == 'Select location':
            errors.append("FROM location isn't selected\n")
        else:
            try:
                self.locations[self.combobox_from.get()]
            except KeyError:
                errors.append('Wrong FROM location\n')

        # ===Check combobox_to=====
        if self.combobox_to.get() == '' or self.combobox_to.get() == 'Select location':
            errors.append("TO location isn't selected\n")
        else:
            try:
                self.locations[self.combobox_to.get()]
            except KeyError:
                errors.append('Wrong TO location\n')

        # ===Check entry_weight=====
        if not self.entry_weight.get():
            errors.append("Weight isn't defined\n")
        else:
            try:
                float(self.entry_weight.get())
            except ValueError:
                errors.append('Weight field contains wrong symbols\n')
            else:
                if float(self.entry_weight.get()) > self.max_weight:
                    errors.append("Weight is more than max. Max weight is {}\n".format(self.max_weight))

        if not errors:
            return True
        else:
            self.executor.submit(self.show_validate_error_window, errors)

    def show_validate_error_window(self, errors):
        error_string = ''
        for error in errors:
            error_string += error
        error_window = tkinter.Toplevel(self.master)
        error_window.title('Error!')
        label_description = ttk.Label(error_window, text='Follow mistakes were founded:', )
        label_description.grid(row=0, column=0, sticky='w', ipadx=5, ipady=5)
        label_errors = ttk.Label(error_window, text=error_string)
        label_errors.grid(row=1, column=0, sticky='e', ipadx=5, ipady=5)
        button_ok = ttk.Button(error_window, text='OK', command=error_window.destroy)
        button_ok.grid(row=2, column=0)

    def set_max_weight(self, future):
        self.max_weight = future.result()

    def set_locations(self, future):
        self.locations = future.result()
        self.executor.submit(GUIControls.set_location_to_comboboxes,
                             self.locations,
                             self.combobox_from,
                             self.combobox_to)


class InternationalDeliveryGUI:
    def __init__(self, master):
        # root object for created gui elements
        self.master = master
        # local ThreadPool for execute future tasks
        self.executor = futures.ThreadPoolExecutor(max_workers=3)

        self.type_of_package_var = tkinter.StringVar(master, '')
        # Draw GUI elements, define in _draw_elements
        self._draw_elements()
        # Type of location, witch will be loaded
        self.locations = Locations('countries')
        self.executor.submit(self.locations.load_locations).add_done_callback(self.set_locations)
        # Get max weight from api
        self.max_weight = None
        self.executor.submit(api.get_max_weight).add_done_callback(self.set_max_weight)
        self.max_weight_doc = 2

    def _draw_elements(self):
        self.label_to = ttk.Label(self.master, text='To location:')
        self.label_to.grid(row=0, column=0, sticky='e')

        self.combobox_to = ttk.Combobox(self.master, values=[], height=10, width=30)
        self.combobox_to.grid(row=0, column=2)

        self.label_type = ttk.Label(self.master, text='Type of package:')
        self.label_type.grid(row=1, column=0, sticky='e', )

        self.radiobutton_doc = ttk.Radiobutton(self.master, variable=self.type_of_package_var, value='doc',
                                               text='Documents')
        self.radiobutton_doc.grid(row=1, column=2, sticky='w')

        self.radiobutton_attr = ttk.Radiobutton(self.master, variable=self.type_of_package_var, value='att',
                                                text='Commodity Investments')
        self.radiobutton_attr.grid(row=2, column=2, sticky='w')

        self.label_weight = ttk.Label(self.master, text='Weight:')
        self.label_weight.grid(row=3, column=0, sticky='e')

        self.entry_weight = ttk.Entry(self.master)
        self.entry_weight.grid(row=3, column=2, sticky='w')

        self.label_cost = ttk.Label(self.master, text='Cost of delivery:')
        self.label_cost.grid(row=4, column=0, sticky='e')
        self.label_cost['state'] = 'disabled'

        self.label_cost_of_delivery = ttk.Label(self.master, text='')
        self.label_cost_of_delivery.grid(row=4, column=2, sticky='w')

        self.button_calculate = ttk.Button(self.master, text='Calculate')

        # Click on button adds new job to ThreadPool, executes it,
        # and after execute invokes function in add_done_callback
        # We assign lambda expression as a command for prevent immediately execute of a function
        self.button_calculate['command'] = lambda: self.executor.submit(self.calculate_delivery). \
            add_done_callback(self.calculate_delivery_done)
        self.button_calculate.grid(row=7, column=2, sticky='e')

    def set_locations(self, future):
        self.locations = future.result()
        self.executor.submit(GUIControls.set_location_to_comboboxes,
                             self.locations,
                             self.combobox_to)

    def set_max_weight(self, future):
        self.max_weight = future.result()

    def validate(self):
        errors = []
        # ===Check combobox_to=====
        if self.combobox_to.get() == '' or self.combobox_to.get() == 'Select location':
            errors.append("TO location isn't selected\n")
        else:
            try:
                self.locations[self.combobox_to.get()]
            except KeyError:
                errors.append('Wrong TO location\n')

        # ===Check that type of package is selected=====
        if self.type_of_package_var:

            # =====If type of package is selected, weight can be checked=====
            if not self.entry_weight.get():
                errors.append("Weight isn't defined\n")
            else:
                try:
                    float(self.entry_weight.get())
                except ValueError:
                    errors.append('Weight field contains wrong symbols\n')
                else:

                    type_of_package = self.type_of_package_var.get()
                    weight = float(self.entry_weight.get())

                    # Case for Documents
                    if type_of_package == 'doc' and weight > self.max_weight_doc:
                        errors.append("Weight is more than max. Max weight is {}\n".format(self.max_weight_doc))

                    # Case for Commodity Investments
                    elif type_of_package == 'att' and weight > self.max_weight:
                        errors.append("Weight is more than max. Max weight is {}\n".format(self.max_weight))
        else:
            errors.append("Type of package isn't selected")

        if not errors:
            return True
        else:
            self.executor.submit(self.show_validate_error_window, errors)
            return False

    def show_validate_error_window(self, errors):
        error_string = ''
        for error in errors:
            error_string += error
        error_window = tkinter.Toplevel(self.master)
        error_window.title('Error!')
        label_description = ttk.Label(error_window, text='Follow mistakes were founded:', )
        label_description.grid(row=0, column=0, sticky='w', ipadx=5, ipady=5)
        label_errors = ttk.Label(error_window, text=error_string)
        label_errors.grid(row=1, column=0, sticky='e', ipadx=5, ipady=5)
        button_ok = ttk.Button(error_window, text='OK', command=error_window.destroy)
        button_ok.grid(row=2, column=0)

    def calculate_delivery(self):
        if not self.validate():
            return
        else:

            to_location = self.locations[self.combobox_to.get()]['value']
            type_of_package = self.type_of_package_var.get()
            weight = self.entry_weight.get()

            response = api.calculate(to_location=to_location,
                                     type=type_of_package,
                                     weight=weight)
            print(response)
            return response

    def calculate_delivery_done(self, future):
        calculate_results = future.result()
        if calculate_results:
            # Enable labels
            self.label_cost['state'] = 'enable'
            self.label_cost_of_delivery['state'] = 'enable'

            # Set result to labels
            self.label_cost_of_delivery['text'] = calculate_results['price'] + ' RUB'


# =========END GUI DESCRIPTION==========

class GUIControls:
    def __init__(self):
        pass

    @staticmethod
    def set_location_to_comboboxes(location, *comboboxes):
        for combobox in comboboxes:
            combobox['state'] = 'disabled'
            combobox.set('Loading locations...')
        for combobox in comboboxes:
            combobox['state'] = 'enable'
            combobox.set('Select location')
            for value in location.keys():
                combobox['values'] += (value,)


# def connection_status():
#     """
#     Check heartbeat of EMS API
#     :return:
#     """
#     while True:
#         if api.heartbeat():
#             label_status['text'] = 'API is available'
#             label_status['foreground'] = 'green'
#         else:
#             label_status['text'] = 'API is unavailable'
#             label_status['foreground'] = 'red'
#         time.sleep(5)


class Locations:
    """
    Used for load locations and return they in correct form
    """
    def __init__(self, *args):
        # Dict for locations in correct form
        self.locations = {}
        # Tuple with locations, witch will be parse
        self.args = args
        # Dict with mistakes and they replacements
        # For example we have string 'Краснодарскийкрай'
        # So we should replace 'край' to ' край'
        self.replacements = {
            u'край': u' край',
            u'округ': u' округ',
            u'автономный': u' автономный ',
            u'область': u' область',
            u'автономная': u' автономная ',
            u'республика': u' республика',
            u'район': u' район',
            u'промышленнный': u' промышленный ',  # sic!
            u'осетия': u' Осетия',
            u'алания': u'Алания',
            u'долгано': u' Долгано',
        }

    def load_locations(self):
        """
        Load locations via api.get_locations method
        :return: Dict with locations
        Example:
        {'Ростовская область': {
                                'value': 'region--rostovskaja-oblast',
                                'type': 'region'
                                }
        }
        """
        logging.debug('Loading locations: Start loading locations')
        #
        for type in self.args:
            locations_in_json = api.get_locations(type)
            for location in locations_in_json:
                self.locations[self.normalize_location(location['name'])] = {
                    'value': location['value'],
                    'type': location['type'],
                }
        logging.debug('Loading locations: ' + str(len(self.locations)) + ' locations has been loaded')
        return self.locations

    def normalize_location(self, location):
        """
        Normalize location to required format.
        By default, location is received from API has format like this 'РОСТОВСКАЯОБЛАСТЬ'
        :return: well formed string with location like this 'Ростовская область'
        """
        # For most cases only first letter should be capital
        location = location.capitalize()
        # Pattern, which will be use as re for search mistakes
        # Patter has form: '(first_condition)|(second_condition)|(third_condition)'
        pattern = ''
        # pattern prepare
        for key in self.replacements:
            pattern += '(%s)|' % key
        # remove redundant '|' at the end of pattern
        pattern = pattern[:-1]
        # Give results of search by string with pattern

        search_results = re.findall(pattern, location)

        # result of search has format ((),(),(third_condition)) ,
        # so we can iterate above this collection to find mistakes and replace they
        if search_results:
            for key in search_results:
                for x in key:
                    if x:
                        location = location.replace(x, self.replacements[x])
        return location


class MainGUI:
    """
    Main GUI class. Contains notebook element, witch will be contains different implementations of GUI
    """

    def __init__(self, master):
        # root element
        self.master = master
        self._draw_elements()

    def _draw_elements(self):
        """
        Add elements to master
        :return: None
        """
        self.notebook = ttk.Notebook(self.master)
        self.tab_local_delivery = ttk.Frame(self.notebook)
        self.tab_international_delivery = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_local_delivery, text="Local delivery")
        self.notebook.add(self.tab_international_delivery, text="International delivery")
        self.notebook.pack()

        LocalDeliveryGUI(self.tab_local_delivery)
        InternationalDeliveryGUI(self.tab_international_delivery)


MainGUI(root)

root.mainloop()
