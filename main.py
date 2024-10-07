import csv
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from datetime import datetime
import calendar


class CalendarWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(CalendarWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.current_date = datetime.now()

        # Etykieta z nazwą miesiąca
        self.month_label = Label(text=self.current_date.strftime('%B %Y'), font_size=18, size_hint=(1, None), height=40)
        self.add_widget(self.month_label)

        # Siatka na dni miesiąca
        self.calendar_grid = GridLayout(cols=7, size_hint_y=None)
        self.calendar_grid.bind(minimum_height=self.calendar_grid.setter('height'))
        self.populate_calendar()
        
        # ScrollView dla kalendarza
        scroll_view = ScrollView(size_hint=(1, 5.7), size=(400, 400)) # Zwiększona wysokość scrolla
        scroll_view.add_widget(self.calendar_grid)
        self.add_widget(scroll_view)

        # Przyciski do zmiany miesiąca
        btn_box = BoxLayout(size_hint_y=None, height=40)
        prev_button = Button(text="Poprzedni miesiąc")
        prev_button.bind(on_release=self.show_prev_month)
        next_button = Button(text="Następny miesiąc")
        next_button.bind(on_release=self.show_next_month)
        btn_box.add_widget(prev_button)
        btn_box.add_widget(next_button)
        self.add_widget(btn_box)

    def populate_calendar(self):
        self.calendar_grid.clear_widgets()

        # Dodaj dni tygodnia
        days = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek", "Sobota", "Niedziela"]
        for day in days:
            self.calendar_grid.add_widget(Label(text=day, bold=True ,font_size=18, size_hint=(1, None), height=40))

        # Pobierz dni w miesiącu
        month_days = calendar.monthcalendar(self.current_date.year, self.current_date.month)

        for week in month_days:
            for day in week:
                if day == 0:
                    btn = Button(text="", disabled=True, size_hint=(None, None), width=100, height=80)  # Pusty przycisk
                else:
                    data = self.current_date.replace(day=day).strftime('%Y-%m-%d')
                    godziny = self.check_hours(data)
                    btn = Button(text=str(day), size_hint=(None, None), width=100, height=80)

                    if godziny > 0:  # Jeśli są zapisane godziny, zmień kolor
                        btn.background_color = (0, 1, 0, 1)  # Zielony
                    btn.bind(on_release=self.select_day)
                self.calendar_grid.add_widget(btn)

        # Aktualizuj etykietę miesiąca
        self.month_label.text = self.current_date.strftime('%B %Y')

    def check_hours(self, date):
        if os.path.isfile('godziny_pracy.csv'):
            with open('godziny_pracy.csv', mode='r') as plik:
                reader = csv.reader(plik)
                for row in reader:
                    if row[0] == date:
                        return float(row[1])  # Zwraca liczbę godzin dla danego dnia
        return 0.0  # Jeśli nie ma godzin, zwraca 0

    def show_prev_month(self, instance):
        if self.current_date.month == 1:
            new_month = 12
            new_year = self.current_date.year - 1
        else:
            new_month = self.current_date.month - 1
            new_year = self.current_date.year
        self.current_date = datetime(new_year, new_month, 1)
        self.populate_calendar()

    def show_next_month(self, instance):
        if self.current_date.month == 12:
            new_month = 1
            new_year = self.current_date.year + 1
        else:
            new_month = self.current_date.month + 1
            new_year = self.current_date.year
        self.current_date = datetime(new_year, new_month, 1)
        self.populate_calendar()

    def select_day(self, instance):
        day = instance.text
        selected_date = self.current_date.replace(day=int(day))
        popup = Popup(title="Wybrany dzień",
                      content=Label(text=f"Wybrano: {selected_date.strftime('%d %B %Y')}"),
                      size_hint=(0.8, 0.5))
        popup.open()


class WorkHoursApp(App):
    def build(self):
        self.title = 'Kalendarz Pracy'

        # Główny layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Etykieta i pole do wpisania liczby godzin
        self.hours_input = TextInput(hint_text="Wprowadź liczbę godzin", multiline=False,  size_hint=(1, None), height=40)
        layout.add_widget(self.hours_input)

        # Kalendarz
        self.calendar = CalendarWidget()
        layout.add_widget(self.calendar)

        # Przycisk do dodania godzin
        add_hours_button = Button(text="Dodaj/Edytuj godziny", size_hint=(1, None), height=40)
        add_hours_button.bind(on_press=self.add_hours)
        layout.add_widget(add_hours_button)

        # Przycisk do wyświetlenia sumy godzin w miesiącu
        sum_hours_button = Button(text="Sumuj godziny w miesiącu", size_hint=(1, None), height=40)
        sum_hours_button.bind(on_press=self.sum_month_hours)
        layout.add_widget(sum_hours_button)

        # Etykieta do wyświetlenia sumy godzin
        self.sum_label = Label(text="Suma godzin: 0.0" , size_hint=(1, None), height=40)
        layout.add_widget(self.sum_label)

        # Ładowanie wcześniejszych danych
        self.load_data()

        return layout

    def add_hours(self, instance):
        data = self.calendar.current_date.strftime('%Y-%m-%d')  # Pobierz datę z kalendarza
        try:
            godziny = float(self.hours_input.text)  # Pobierz liczbę godzin
            dane = []
            istnieje_dzien = False

            if os.path.isfile('godziny_pracy.csv'):
                with open('godziny_pracy.csv', mode='r') as plik:
                    reader = csv.reader(plik)
                    for row in reader:
                        if row[0] == data:
                            row[1] = str(godziny)
                            istnieje_dzien = True
                        dane.append(row)

            if not istnieje_dzien:
                dane.append([data, str(godziny)])

            with open('godziny_pracy.csv', mode='w', newline='') as plik:
                writer = csv.writer(plik)
                writer.writerows(dane)

            self.load_data()
            self.hours_input.text = ""
            self.show_popup("Sukces", f"Liczba godzin na dzień {data} została zaktualizowana.")

        except ValueError:
            self.show_popup("Błąd", "Wprowadź prawidłową liczbę godzin!")

    def sum_month_hours(self, instance):
        suma_miesieczna = 0.0
        wybrany_miesiac = self.calendar.current_date.strftime('%Y-%m')  # Pobierz "yyyy-mm" z daty
        if os.path.isfile('godziny_pracy.csv'):
            with open('godziny_pracy.csv', mode='r') as plik:
                reader = csv.reader(plik)
                for row in reader:
                    if len(row) >= 2:  # Upewnij się, że wiersz ma co najmniej 2 elementy
                        data_wiersz = row[0][:7]
                        if data_wiersz == wybrany_miesiac:  # Poprawna zmienna
                            try:
                                suma_miesieczna += float(row[1])  # Próbuj konwertować tylko liczby
                            except ValueError:
                                continue  # Pomiń wiersz, jeśli konwersja się nie uda

        self.sum_label.text = f"Suma godzin w {wybrany_miesiac}: {suma_miesieczna:.2f}"

    def load_data(self):
        suma_godzin = 0.0
        if os.path.isfile('godziny_pracy.csv'):
            with open('godziny_pracy.csv', mode='r') as plik:
                reader = csv.reader(plik)
                for row in reader:
                    if len(row) >= 2:  # Upewnij się, że wiersz ma co najmniej 2 elementy
                        try:
                            suma_godzin += float(row[1])  # Próbuj konwertować tylko liczby
                        except ValueError:
                            continue  # Pomiń wiersz, jeśli konwersja się nie uda

        self.sum_label.text = f"Suma godzin: {suma_godzin:.2f}"

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(None, None), size=(400, 400))
        popup.open()


if __name__ == "__main__":
    WorkHoursApp().run()
