from database import CreatingDatabase, ClearDatabase
from update import bus_lines, bus_stops, bus_hours
from env import STATUS
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno, showerror, showinfo
from tkinter import font
import sqlite3
import requests
import re
import webview


class DynamicButton(tk.Button):
    def __init__(self, master, column, row, text, grid_options=None, width=5, height=2, font=('Verdana', 10), command=None, **kwargs):
        if grid_options is None:
            grid_options = {}
        super().__init__(master, text=text, command=command, width=width, height=height, font=font, **kwargs)
        self.grid(row=row, column=column, **grid_options)


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        CreatingDatabase()

        self.title("Ostrów Wielkopolski MZK")

        self.container = tk.Frame(self)
        self.container.grid(row=0, column=0)

        self.frame = LoadingPage(self.container, self)
        self.frame.grid(row=0, column=0)

    def show_frame(self, pagename):
        self.frame.grid_forget()
        self.frame = pagename(self.container, self)
        self.frame.grid(row=0, column=0)

    def quit_app(self):
        result = askyesno("Zamknij aplikację", "Czy na pewno chcesz zamknąć aplikację?")
        if result:
            self.destroy()

    def open_toplevel_window(self, toplevel_class, arg):
        toplevel = toplevel_class(self.container, self, arg)
        toplevel.grab_set()

    def load_web_frame(self, arg=None):
        if arg is None:
            result = showerror("Błąd", "Brak lokalizacji w bazie danych")
        else:
            if STATUS == "x":
                result = showinfo("Informacja", "Jesteś w trybie offline")
            else:
                webview.create_window('Mapa', 'http://rozklad.com/maps/'+arg[2])
                webview.start()


class LoadingPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        bold_font = font.Font(family="Verdana", size=10, weight="bold")

        label_frame = tk.Frame(self)
        label_frame.grid(row=0, column=0)
        self.label = tk.Label(label_frame, text="Sprawdzanie połączenia z internetem...", font=bold_font)
        self.label.pack(pady=100, padx=10)

        self.button_options = {"height": 2, "width": 20, "pady": 10, "padx": 10}
        self.grid_button_options = {"pady": 10, "padx": 15}

        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=1, column=0)
        self.goto_button = tk.Button(buttons_frame, text='Przejdź do menu', **self.button_options, command=lambda: controller.show_frame(Menu))
        self.exit_button = tk.Button(buttons_frame, text='Wyjdź', **self.button_options, command=controller.quit_app)

        self.check_internet_connection()

    def check_internet_connection(self):
        try:
            response = requests.get("https://www.google.com", timeout=5)
            if response.status_code == 200:
                self.label.config(text="Połączenie powiodło się.")
                if STATUS == "online":
                    self.label.config(text="Aktualizacja rozkładu jazdy...\nTo może chwilę potrwać.")
                    ClearDatabase()
                    lines, hrefs = bus_lines()
                    bus_station_attr = bus_stops(lines, hrefs)
                    bus_hours(bus_station_attr)
                    self.label.config(text="Pobrano rozkład jazdy.")
                    self.goto_button.grid(row=0, column=0, **self.grid_button_options)
                    self.exit_button.grid(row=0, column=1, **self.grid_button_options)
                else:
                    self.label.config(text="Ustawiono tryb offline.")
                    self.goto_button.grid(row=0, column=0, **self.grid_button_options)
                    self.exit_button.grid(row=0, column=1, **self.grid_button_options)
            else:
                self.label.config(text="Brak połączenia z internetem.\nPrzełączono na tryb offline.")
                env_file = Path('env.py')
                env_file.write_text(env_file.read_text().replace("online", "offline"))
                self.goto_button.grid(row=0, column=0, **self.grid_button_options)
                self.exit_button.grid(row=0, column=1, **self.grid_button_options)

        except requests.ConnectionError:
            self.label.config(text="Brak połączenia z internetem.\nPrzełączono na tryb offline.")
            env_file = Path('env.py')
            env_file.write_text(env_file.read_text().replace("online", "offline"))
            self.goto_button.grid(row=0, column=0, **self.grid_button_options)
            self.exit_button.grid(row=0, column=1, **self.grid_button_options)


class Menu(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        button_options = {"height": 2, "width": 20, "pady": 10, "padx": 10}
        grid_button_options = {"pady": 10, "padx": 15}

        button_home = tk.Button(self, text='Rozkład jazdy', **button_options, command=lambda: controller.show_frame(SelectLine))
        button_home.grid(column=0, row=0, **grid_button_options)

        button_home = tk.Button(self, text='Wyszukaj trasę', **button_options, state=tk.DISABLED)
        button_home.grid(column=0, row=1, **grid_button_options)

        exit_button = tk.Button(self, text='Wyjdź', **button_options, command=controller.quit_app)
        exit_button.grid(column=0, row=2, **grid_button_options)


class SelectLine(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        db_connection = sqlite3.connect('database.db')
        db_cursor = db_connection.cursor()
        bus_lines_tuples = db_cursor.execute('SELECT line_name FROM bus_lines').fetchall()
        db_connection.close()
        bus_lines_list = [result[0] for result in bus_lines_tuples]

        button_options = {"height": 2, "width": 20, "pady": 10, "padx": 10}
        grid_button_options = {"pady": 10, "padx": 15}
        bold_font = font.Font(family="Verdana", size=10, weight="bold")

        line_label_frame = tk.Frame(self)
        line_label_frame.grid(row=0, column=0, padx=20, pady=20)
        label_select_line = tk.Label(self, text="Wybierz linię autobusową", font=bold_font, padx=10, pady=10)
        label_select_line.grid(row=0, column=0)

        line_buttons_frame = tk.Frame(self)
        line_buttons_frame.grid(row=1, column=0, padx=20, pady=20)
        button_col_value = 0
        button_row_value = 0

        bold_font = font.Font(family="Verdana", size=10, weight="bold")

        for buttons in bus_lines_list:
            button = DynamicButton(line_buttons_frame, text=buttons, font=bold_font, column=button_col_value, row=button_row_value, grid_options=grid_button_options, width=7, height=2, command=lambda btn=buttons: controller.open_toplevel_window(BusStops, arg=btn))
            if button_col_value == 3:
                button_col_value = 0
                button_row_value += 1
            else:
                button_col_value += 1

        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=2, column=0)
        button_home = tk.Button(buttons_frame, text='Menu', **button_options, command=lambda: controller.show_frame(Menu))
        button_home.grid(column=0, row=0, **grid_button_options)
        exit_button = tk.Button(buttons_frame, text='Wyjdź', **button_options, command=controller.quit_app)
        exit_button.grid(column=1, row=0, **grid_button_options)


class BusStops(tk.Toplevel):
    def __init__(self, parent, controller, arg):
        tk.Toplevel.__init__(self, parent)

        self.title("Przystanki")

        self.item_values = []

        db_connection = sqlite3.connect('database.db')
        db_cursor = db_connection.cursor()
        line_bus_stops = db_cursor.execute('SELECT * FROM bus_stops WHERE bus_line_id=(SELECT id FROM bus_lines WHERE (line_name=?))', (arg,)).fetchall()
        db_connection.close()

        bus_routes = set()
        for j in line_bus_stops:
            bus_routes.add(j[3])
        bus_routes = list(bus_routes)

        route1 = [k for k in line_bus_stops if bus_routes[0] in k]
        route2 = [k for k in line_bus_stops if bus_routes[1] in k]

        button_options = {"height": 2, "width": 60, "pady": 10, "padx": 10}
        grid_button_options = {"pady": 10, "padx": 15}
        label_options = {"pady": 20}
        bold_font = font.Font(family="Verdana", size=10, weight="bold")

        self.func_button_1 = tk.Button(self, text='Pokaż lokalizacje', state=tk.DISABLED, command=lambda: controller.load_web_frame(arg=self.item_values), **button_options)
        self.func_button_1.grid(column=0, row=0, **grid_button_options)
        self.func_button_2 = tk.Button(self, text='Rozkład jazdy', state=tk.DISABLED, command=lambda: controller.open_toplevel_window(BusSchedule, arg=self.item_values), **button_options)
        self.func_button_2.grid(column=1, row=0, **grid_button_options)

        route1_label = tk.Label(self, text=re.sub(r'(\d+|[A-Z])', r' \1', bus_routes[0]).replace("_", ""), font=bold_font, **label_options)
        route1_label.grid(row=1, column=0)
        route2_label = tk.Label(self, text=re.sub(r'(\d+|[A-Z])', r' \1', bus_routes[1]).replace("_", ""), font=bold_font, **label_options)
        route2_label.grid(row=1, column=1)

        #Treeview 1
        treeview_route1_frame = tk.Frame(self)
        treeview_route1_frame.grid(row=2, column=0)

        tree_scroll_bar_route1 = ttk.Scrollbar(treeview_route1_frame)
        tree_scroll_bar_route1.pack(side="right", fill='y')

        self.route1_tree = ttk.Treeview(treeview_route1_frame, yscrollcommand=tree_scroll_bar_route1.set, selectmode="browse")
        self.route1_tree['columns'] = ('Index', 'Nazwa przystanku', 'Mapa', 'Atrybut', 'Busstop id')
        self.route1_tree.column('#0', width=0, stretch=tk.NO)
        self.route1_tree.column('Index', anchor=tk.CENTER, width=50)
        self.route1_tree.column('Nazwa przystanku', anchor=tk.CENTER, width=454)
        self.route1_tree.column('Mapa', width=0, stretch=tk.NO)
        self.route1_tree.column('Atrybut', width=0, stretch=tk.NO)
        self.route1_tree.column('Busstop id', width=0, stretch=tk.NO)

        self.route1_tree.heading('#0', text='', anchor=tk.CENTER)
        self.route1_tree.heading('Index', text='Index', anchor=tk.CENTER)
        self.route1_tree.heading('Nazwa przystanku', text='Nazwa przystanku', anchor=tk.CENTER)
        self.route1_tree.heading('Mapa', text='', anchor=tk.CENTER)
        self.route1_tree.heading('Atrybut', text='', anchor=tk.CENTER)
        self.route1_tree.heading('Busstop id', text='', anchor=tk.CENTER)
        self.route1_tree.pack(side="left")

        for element in route1:
            self.route1_tree.insert('', tk.END, values=(element[2], element[1], element[4], element[5], element[0]))

        #Treeview 2
        treeview_route2_frame = tk.Frame(self)
        treeview_route2_frame.grid(row=2, column=1)

        tree_scroll_bar_route2 = ttk.Scrollbar(treeview_route2_frame)
        tree_scroll_bar_route2.pack(side="right", fill='y')

        self.route2_tree = ttk.Treeview(treeview_route2_frame, yscrollcommand=tree_scroll_bar_route2.set, selectmode="browse")
        self.route2_tree['columns'] = ('Index', 'Nazwa przystanku', 'Mapa', 'Atrybut', 'Busstop id')
        self.route2_tree.column('#0', width=0, stretch=tk.NO)
        self.route2_tree.column('Index', anchor=tk.CENTER, width=50)
        self.route2_tree.column('Nazwa przystanku', anchor=tk.CENTER, width=454)
        self.route2_tree.column('Mapa', width=0, stretch=tk.NO)
        self.route2_tree.column('Atrybut', width=0, stretch=tk.NO)
        self.route2_tree.column('Busstop id', width=0, stretch=tk.NO)

        self.route2_tree.heading('#0', text='', anchor=tk.CENTER)
        self.route2_tree.heading('Index', text='Index', anchor=tk.CENTER)
        self.route2_tree.heading('Nazwa przystanku', text='Nazwa przystanku', anchor=tk.CENTER)
        self.route2_tree.heading('Mapa', text='', anchor=tk.CENTER)
        self.route2_tree.heading('Atrybut', text='', anchor=tk.CENTER)
        self.route2_tree.heading('Busstop id', text='', anchor=tk.CENTER)
        self.route2_tree.pack(side="left")

        self.route1_tree.bind("<<TreeviewSelect>>", self.busstop_select)
        self.route2_tree.bind("<<TreeviewSelect>>", self.busstop_select)

        for element in route2:
            self.route2_tree.insert('', tk.END, values=(element[2], element[1], element[4], element[5], element[0]))

        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=3, column=0, columnspan=2)
        exit_button = tk.Button(buttons_frame, text='Wróć', **button_options, command=self.destroy)
        exit_button.grid(column=0, row=0, **grid_button_options)

    def busstop_select(self, event):

        selected_tree = event.widget

        if selected_tree == self.route1_tree:
            for i in self.route2_tree.selection():
                self.route2_tree.selection_remove(i)
        elif selected_tree == self.route2_tree:
            for i in self.route1_tree.selection():
                self.route1_tree.selection_remove(i)

        for selected_item in selected_tree.selection():
            self.item_values = selected_tree.item(selected_item)['values']

        self.func_button_1.config(state=tk.ACTIVE)
        self.func_button_2.config(state=tk.ACTIVE)


class BusSchedule(tk.Toplevel):
    def __init__(self, parent, controller, arg):
        tk.Toplevel.__init__(self, parent)

        self.title("Rozkład jazdy")

        db_connection = sqlite3.connect('database.db')
        db_cursor = db_connection.cursor()
        schedule = db_cursor.execute(
            'SELECT id, hour, day FROM bus_hours WHERE bus_line_id=(SELECT bus_line_id FROM bus_stops WHERE (attribute=?)) AND (bus_stop_id=?) ORDER BY id',
            (arg[3], arg[4],)).fetchall()
        legend = db_cursor.execute(
            'SELECT legend FROM legends WHERE bus_line_id=(SELECT bus_line_id FROM bus_stops WHERE (attribute=?)) AND (bus_stop_id=?)',
            (arg[3], arg[4],)).fetchall()
        db_connection.close()

        button_options = {"height": 2, "width": 60, "pady": 10, "padx": 10}
        grid_button_options = {"pady": 10, "padx": 15}
        bold_font = font.Font(family="Verdana", size=10, weight="bold")

        treeview_frame_1 = tk.Frame(self)
        treeview_frame_1.grid(row=0, column=0)
        treeview_frame_2 = tk.Frame(self)
        treeview_frame_2.grid(row=0, column=1)
        treeview_frame_3 = tk.Frame(self)
        treeview_frame_3.grid(row=0, column=2)

        tree_scroll_bar_bus_schedule = ttk.Scrollbar(treeview_frame_1)
        tree_scroll_bar_bus_schedule.pack(side="right", fill='y')
        tree_scroll_bar_bus_schedule_2 = ttk.Scrollbar(treeview_frame_2)
        tree_scroll_bar_bus_schedule_2.pack(side="right", fill='y')
        tree_scroll_bar_bus_schedule_3 = ttk.Scrollbar(treeview_frame_3)
        tree_scroll_bar_bus_schedule_3.pack(side="right", fill='y')

        self.bus_schedule_tree = ttk.Treeview(treeview_frame_1, yscrollcommand=tree_scroll_bar_bus_schedule.set,
                                        selectmode="none")
        self.bus_schedule_tree['columns'] = ('Dni Robocze',)
        self.bus_schedule_tree.column('#0', width=0, stretch=tk.NO)
        self.bus_schedule_tree.column('Dni Robocze', anchor=tk.CENTER)
        self.bus_schedule_tree.heading('#0', text='', anchor=tk.CENTER)
        self.bus_schedule_tree.heading('Dni Robocze', text='Dni Robocze', anchor=tk.CENTER)
        self.bus_schedule_tree.pack(side="left")

        self.bus_schedule_tree_2 = ttk.Treeview(treeview_frame_2, yscrollcommand=tree_scroll_bar_bus_schedule_2.set,
                                              selectmode="none")
        self.bus_schedule_tree_2['columns'] = ('Soboty',)
        self.bus_schedule_tree_2.column('#0', width=0, stretch=tk.NO)
        self.bus_schedule_tree_2.column('Soboty', anchor=tk.CENTER)
        self.bus_schedule_tree_2.heading('#0', text='', anchor=tk.CENTER)
        self.bus_schedule_tree_2.heading('Soboty', text='Soboty', anchor=tk.CENTER)
        self.bus_schedule_tree_2.pack(side="left")

        self.bus_schedule_tree_3 = ttk.Treeview(treeview_frame_3, yscrollcommand=tree_scroll_bar_bus_schedule_3.set,
                                              selectmode="none")
        self.bus_schedule_tree_3['columns'] = ('Niedziele i świeta',)
        self.bus_schedule_tree_3.column('#0', width=0, stretch=tk.NO)
        self.bus_schedule_tree_3.column('Niedziele i świeta', anchor=tk.CENTER)
        self.bus_schedule_tree_3.heading('#0', text='', anchor=tk.CENTER)
        self.bus_schedule_tree_3.heading('Niedziele i świeta', text='Niedziele i święta', anchor=tk.CENTER)
        self.bus_schedule_tree_3.pack(side="left")

        for element in schedule:
            if element[2] == "r":
                self.bus_schedule_tree.insert('', tk.END, values=(element[1]))
            elif element[2] == "s":
                self.bus_schedule_tree_2.insert('', tk.END, values=(element[1]))
            elif element[2] == "w":
                self.bus_schedule_tree_3.insert('', tk.END, values=(element[1]))

        legend_frame = tk.Frame(self)
        legend_frame.grid(row=1, column=0, columnspan=3)
        label = tk.Label(legend_frame, text=str(legend[0]), font=bold_font, wraplength=450)
        label.grid(row=0, column=0)

        buttons_frame = tk.Frame(self)
        buttons_frame.grid(row=2, column=0, columnspan=3)
        exit_button = tk.Button(buttons_frame, text='Wróć', **button_options, command=self.destroy)
        exit_button.grid(column=0, row=0, **grid_button_options)


if __name__ == '__main__':
    app = App()
    app.mainloop()







