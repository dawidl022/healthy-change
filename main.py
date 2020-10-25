from kivy import require
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.network.urlrequest import UrlRequest
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button, ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.dropdown import DropDown
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.recyclelayout import RecycleLayout
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition

from os import path
from webbrowser import open as browser_open
from datetime import datetime
import time
from urllib.parse import quote
import json
import requests

import config
import nutrient_dictionary
import messages

from ibm_watson.language_translator_v3 import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

authenticator = IAMAuthenticator(f'{config.ibm_api["key"]}')
language_translator = LanguageTranslatorV3(
    version='2018-05-01',
    authenticator=authenticator
)

language_translator.set_service_url(f'{config.ibm_api["url"]}')

require("2.0.0")


def get_current_time():
    return str(datetime.now()).split()[1][:5]


class UserProfile:
    def __init__(self, **kwargs):
        self.goal = kwargs.get("goal", None)
        self.diet = kwargs.get("diet", None)
        self.first_day = kwargs.get("first_day", None)
        self.current_day = kwargs.get("current_day", None)
        self.setup_complete = kwargs.get("setup_complete", False)
        self.activities_today = kwargs.get("activities_today", [])
        self.hunger_marks = kwargs.get("hunger_marks", [])
        self.kcal = kwargs.get("kcal", 0)
        self.message = kwargs.get("message", None)
        self.hunger_marks = kwargs.get("hunger_marks", [])
        self.displayed_nutrients = kwargs.get("displayed_nutrients", nutrient_dictionary.default_nutrients)
        self.nutrients_today = kwargs.get("nutrients_today", dict())
        self.sex = kwargs.get("sex", None)
        self.mass = kwargs.get("mass", None)
        self.height = kwargs.get("height", None)
        self.age = kwargs.get("age", None)
        self.bmi = kwargs.get("bmi", None)
        self.bmi_color = kwargs.get("bmi_color", (0, 1, 0, .5))
        self.bed_time = kwargs.get("bed_time", None)
        self.wake_time = kwargs.get("wake_time", None)
        self.afternoon_check_time = kwargs.get("afternoon_check_time", None)
        self.evening_check_time = kwargs.get("evening_check_time", None)
        self.mood_checks_left = kwargs.get("mood_checks_left", 2)

        self.water_needed = kwargs.get("water_needed", None)
        self.water_per_second = kwargs.get("water_per_second", None)
        self.water_balance = kwargs.get("water_balance", None)
        self.hydration = kwargs.get("hydration", None)
        self.save_time = kwargs.get("save_datetime", time.time())
        self.save_date = kwargs.get("save_date", str(datetime.now())[:10])
        Clock.schedule_interval(self.auto_save_user_info, 2)

    def auto_save_user_info(self, td):
        display_dict = {"min": "Chcę zrzucić wagę", "stay": "Chcę utrzymać swoją wagę ale lepiej się czuć",
                        "max": "Chcę nabrać wagę", "vegan": "Wegańska", "all_allowed": "Bez ograniczeń"}
        self.save_time = time.time()
        self.save_date = str(datetime.now())[:10]
        self.current_day = (datetime.now() - datetime.strptime(self.first_day, "%Y-%m-%d")).days + 1 if self.first_day else None
        if self.first_day and self.current_day:
            MainPopupWidgets.body1.text = f"Dzień: {self.current_day}\nDzień rozpoczęcia: {self.first_day}\n"
        if self.goal and self.diet:
            MainPopupWidgets.body1a.text = f"Cel: {display_dict[self.goal]}\nWybrana dieta: {display_dict[self.diet]}\n"
        with open("user.json", "w") as save_file:
            output_json = json.dumps(self.__dict__, indent=4)
            save_file.write(output_json)

    def add_meal(self, meal, calories):
        self.activities_today.append(f"{get_current_time()} Posiłek: {meal} +{calories}kcal")
        self.kcal += calories

    def add_water(self, amount):
        self.message = f"Wypito {amount}ml wody"
        self.activities_today.append(f"{get_current_time()} Woda: {amount}ml")
        self.water_balance += int(amount)

    def add_exercise(self, activity, duration):
        duration = int(duration)
        print("Adding..")
        duration_hours = duration // 60
        duration_minutes = duration % 60
        # if duration_hours < 1: TODO przeliczyć na godziny i minuty, dodać 2 okna, jedno na godziny, drugien na minuty
        kcal = int(PhysicalActivities.activities[activity]) * duration / 60
        self.kcal -= kcal
        self.message = f"Dodano {activity}, trwająca {duration} minut. Spaliłeś przy tym około {round(kcal)}kcal"
        self.activities_today.append(f"{get_current_time()} {activity} -{round(kcal)}kcal")

    def add_custom_exercise(self, activity, duration, kcal):
        self.message = f"Dodano {activity}, trwająca {duration} minut. Spaliłeś przy tym około {round(kcal)}kcal"
        self.activities_today.append(f"{get_current_time()} {activity} -{round(kcal)}kcal")

    def add_hunger_mark(self):
        self.hunger_marks.append(get_current_time())

    def calculate_bmi(self):
        try:
            self.bmi = round(self.mass / (self.height / 100) ** 2, 1)
        except TypeError:
            pass
        else:
            if self.bmi < 18.5:
                self.bmi_color = (0, .1, 1, .5)
            elif 18.5 <= self.bmi < 25:
                self.bmi_color = (0, 1, 0, .5)
            elif 25 <= self.bmi < 30:
                self.bmi_color = (.9, .5, 0, .5)
            else:
                self.bmi_color = (1, 0, 0, .5)

    def calculate_water(self):
        try:
            if self.age <= 30:
                self.water_needed = self.mass * 40
            elif 30 < self.age <= 54:
                self.water_needed = self.mass * 35
            elif 54 < self.age <= 65:
                self.water_needed = self.mass * 30
            else:
                self.water_needed = self.mass * 25

            self.water_per_second = self.water_needed / 86400
            if not self.water_balance:
                self.water_balance = self.water_needed
        except TypeError:
            pass

    def calculate_hydration(self):
        try:
            self.hydration = round((self.water_balance * 100) / self.water_needed)
        except TypeError:
            pass



user = UserProfile()  # before app loads


class WakeTimeDropDown(DropDown):
    def __init__(self, **kwargs):
        super(WakeTimeDropDown, self).__init__(**kwargs)
        for index in range(38):
            hour = index // 2 + 5
            if index % 2 == 0:
                minutes = "00"
            else:
                minutes = "30"
            btn = Button(text=f"{hour}:{minutes}", size_hint_y=None, height="40dp")
            btn.bind(on_release=lambda btn: self.select(btn.text))
            self.add_widget(btn)
        for index in range(10):
            hour = index // 2
            if index % 2 == 0:
                minutes = "00"
            else:
                minutes = "30"
            btn = Button(text=f"{hour}:{minutes}", size_hint_y=None, height="40dp")
            btn.bind(on_release=lambda btn: self.select(btn.text))
            self.add_widget(btn)

    def on_select(self, hour):
        user.wake_time = hour


class BedTimeDropDown(DropDown):
    def __init__(self, **kwargs):
        super(BedTimeDropDown, self).__init__(**kwargs)
        for index in range(10):
            hour = index // 2 + 19
            if index % 2 == 0:
                minutes = "00"
            else:
                minutes = "30"
            btn = Button(text=f"{hour}:{minutes}", size_hint_y=None, height="40dp")
            btn.bind(on_release=lambda btn: self.select(btn.text))
            self.add_widget(btn)
        for index in range(38):
            hour = index // 2
            if index % 2 == 0:
                minutes = "00"
            else:
                minutes = "30"
            btn = Button(text=f"{hour}:{minutes}", size_hint_y=None, height="40dp")
            btn.bind(on_release=lambda btn: self.select(btn.text))
            self.add_widget(btn)

    def on_select(self, hour):
        user.bed_time = hour
        user.afternoon_check_time = int(hour.split(":")[0]) - 9
        user.evening_check_time = int(hour.split(":")[0]) - 1


class UserInfoScreen(Screen):
    popup = None
    _height = ObjectProperty()
    mass = ObjectProperty()
    age = ObjectProperty()
    dropdown_button_sleep = ObjectProperty()
    dropdown_button_wake = ObjectProperty()

    def __init__(self, **kwargs):
        super(UserInfoScreen, self).__init__(**kwargs)
        self.is_male = False
        self.is_female = False
        Clock.schedule_interval(self.update_button, 0.1)

    def update_button(self, td):
        if not user.wake_time:
            pass
        else:
            self.dropdown_button_wake.text = user.wake_time
        if not user.bed_time:
            pass
        else:
            self.dropdown_button_sleep.text = user.bed_time

    def male_check(self):
        self.is_male = True
        self.is_female = False

    def female_check(self):
        self.is_male = False
        self.is_female = True

    def check_details(self):
        errors = []
        details = {"wzrost": self._height.text, "wiek": self.age.text, "masa": self.mass.text}
        for label, value in details.items():
            if len(value) < 1:
                errors.append("Proszę uzupełnić pole \"{}\"".format(label))
            else:
                try:
                    int(value)
                except ValueError:
                    errors.append("Proszę wpisać w pole \"{}\" tylko liczby".format(label))
        if not self.is_male and not self.is_female:
            errors.append("Proszę wybrać płeć")
        if self.dropdown_button_sleep.text == "Wybór godziny":
            errors.append("Wybierz godzinę, o której za zwyczaj kładziesz się spać.")
        if self.dropdown_button_wake.text == "Wybór godziny":
            errors.append("Wybierz godzinę, o której za zwyczaj wstajesz rano.")
        if self.dropdown_button_sleep.text == "Wybór godziny" or self.dropdown_button_wake.text == "Wybór godziny":
            errors.append("Stała godzina wstawiania i zasypiania dobrze wpływa na zdrowie i samopoczucie")
            errors.append("Nawet jeśli nie masz aktualnie takich godzin, ustal sobie teraz taki cel.")
        if len(errors) == 0:
            user.age = int(self.age.text)
            user.height = int(self._height.text)
            user.mass = int(self.mass.text)
            user.calculate_bmi()
            if self.is_male:
                user.sex = "M"
            elif self.is_female:
                user.sex = "F"
            return True
        else:
            self.error_popup_open(errors)
            return False

    def open_wake_time(self, widget):
        dropdown = WakeTimeDropDown()
        dropdown.open(widget)

    def open_bed_time(self, widget):
        dropdown = BedTimeDropDown()
        dropdown.open(widget)

    @classmethod
    def error_popup_open(cls, errors):
        cls.popup = HubPopupWidgets("Błąd: Niepoprawne bądź brakujące dane", errors, UserInfoScreen)
        cls.popup.popup.open()

    @classmethod
    def close_info(cls):
        cls.popup.popup.dismiss()


class BmiButton(Button):
    background_normal = ""
    background_down = ""


class MainPopupWidgets:
    default = "Brak Danych"
    root_layout = BoxLayout(orientation="vertical")
    # TODO transition this to KV file and add ObjectProperties
    layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
    layout.bind(minimum_height=layout.setter('height'))
    heading1 = Label(text="Statystyki Użytkowinika", font_size="20dp")
    body1 = Label(text=f"Dzień: {default}\nDzień rozpoczęcia: {default}\n")
    body1a = Label(text=f"Cel: {default}\nWybrana dieta: {default}\n")
    heading2 = Label(text="O aplikacji", font_size="20dp")
    body2 = Label(text="Wersja: 0.0.12\n\n")
    heading3 = Label(text="Autorzy", font_size="18dp")
    body3 = Label(text="Architekt/Programista: Dawid Lachowicz\n\nGrafik: Marcel Jarosik")
    for item in [heading1, body1, body1a, heading2, body2, heading3, body3]:
        item.size_hint = (1, None)
        item.height = "50dp"
        layout.add_widget(item)
    root = ScrollView(size_hint=(1, 1), size=(Window.width, Window.height))
    root.add_widget(layout)
    root_layout.add_widget(root)
    root_layout.add_widget(Button(text="Zamknij okno", size_hint_y=0.1,
                                  on_release=lambda *args: MyRootBoxLayout.close_info()))

    popup = Popup(title="Statystyki i Informacje o Aplikacji",
                  content=root_layout,
                  size_hint=(0.9, 0.9))


class MyRootBoxLayout(FloatLayout):
    day = user.current_day if user.current_day else 1
    day_label = ObjectProperty()

    def __init__(self, **kwargs):
        super(MyRootBoxLayout, self).__init__()
        self.day_label.text = f"Dzień {self.day}"
        Clock.schedule_interval(self.update_day, 1)

    def update_day(self, td):
        self.day = user.current_day if user.current_day else 1
        self.day_label.text = f"Dzień {self.day}"

    @staticmethod
    def display_info():
        MainPopupWidgets.popup.open()

    @staticmethod
    def close_info():
        MainPopupWidgets.popup.dismiss()


class InfoScreen(Screen):
    pass


class GoalScreen(Screen):
    @staticmethod
    def chose_goal(goal):
        user.goal = goal


class HubPopupWidgets:
    def __init__(self, title, labels_text, parent):
        root_layout = BoxLayout(orientation="vertical", padding="10dp")
        layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        for item in labels_text:
            label = Label(text=item)
            label.size_hint = (1, None)
            label.height = "50dp"
            layout.add_widget(label)
        root = ScrollView(size_hint=(1, 1), size=(Window.width, Window.height))
        root.add_widget(layout)
        root_layout.add_widget(root)
        root_layout.add_widget(Button(text="Zamknij okno", size_hint_y=0.1,
                                      on_release=lambda *args: parent.close_info()))

        self.popup = Popup(title=title,
                           content=root_layout, size_hint=(0.9, 0.7))


class DietScreen(Screen):
    popup = None

    @staticmethod
    def chose_diet(diet):
        user.diet = diet

    @staticmethod
    def read_vegan():
        browser_open("http://veganworkout.org.pl/co-jesc/")

    @staticmethod
    def read_normal():
        browser_open(
            "https://www.poradnikzdrowie.pl/diety-i-zywienie/odchudzanie/jaka-jest-zbilansowana-dieta-optymalna-dla-ciebie-aa-cJ56-67oc-F24F.html")


class ClickableImage(ButtonBehavior, Image):
    pass


class NutrientSelector(BoxLayout):
    def check_box(self, nutrient):
        if nutrient in user.displayed_nutrients:
            user.displayed_nutrients.remove(nutrient)
        else:
            user.displayed_nutrients.append(nutrient)
        print(user.displayed_nutrients)


class NutrientScreen(Screen):

    @classmethod
    def display_info(cls):
        user.setup_complete = True
        user.first_day = str(datetime.now())[:10]
        cls.popup = HubPopupWidgets("Witaj w Aplikacji!", messages.instructions, NutrientScreen)
        cls.popup.popup.open()

    @classmethod
    def close_info(cls):
        cls.popup.popup.dismiss()


class PhysicalActivities:
    activities = {}
    with open("activities.txt") as activities_file:
        for count, line in enumerate(activities_file):
            line = line.strip()
            if len(line) < 1:
                continue
            if count % 2 == 0:
                activities[line] = None
                last_line = line
            else:
                activities[last_line] = line

    @classmethod
    def update(cls):
        with open("activities.txt") as activities_file:
            for count, line in enumerate(activities_file):
                line = line.strip()
                if len(line) < 1:
                    continue
                if count % 2 == 0:
                    cls.activities[line] = None
                    last_line = line
                else:
                    cls.activities[last_line] = line
        print(cls.activities)


class DurationPopup:
    def __init__(self, activity):
        self.activity = activity
        box_layout = BoxLayout(orientation="horizontal", spacing=10)
        self.duration = TextInput(multiline=False, size_hint_y=0.9)
        box_layout.add_widget(self.duration)
        box_layout.add_widget(Button(text="Dodaj Aktywność", size_hint_y=0.9, on_release=lambda *args: self.btn()))
        self.duration_popup = Popup(title="Wprowadz czas trwania aktywności (w minutach)", content=box_layout,
                                    size_hint=(0.8, 0.2))

    def btn(self):
        try:
            int(self.duration.text)
        except ValueError:
            self.duration.text = "Wprowadź jedynie wartość cyfrową\nw minutach (bez jednostki)"
        else:
            user.add_exercise(self.activity, self.duration.text)
            ActivityPopupWidgets.close_duration()


class WaterPopup:
    def __init__(self):
        box_layout = BoxLayout(orientation="horizontal", spacing=10)
        water_icon = Image(source="grafika/Szklanka wody.png")
        self.amount = TextInput(multiline=False, size_hint_y=0.9)
        box_layout.add_widget(water_icon)
        box_layout.add_widget(self.amount)
        box_layout.add_widget(Button(text="Dodaj", size_hint_y=0.9, on_release=lambda *args: self.btn()))
        self.water_popup = Popup(title="Wprowadz ilość wypitej wody (w ml)", content=box_layout,
                                 size_hint=(0.8, 0.2))

    def btn(self):
        user.add_water(self.amount.text)
        ActivityPopupWidgets.close_water_popup()


class CustomActivityBoxLayout(BoxLayout):
    pass


class CustomActivityPopup:
    def __init__(self):
        root_layout = BoxLayout(orientation="vertical")
        box_layout1 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.28)
        box_layout2 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.28)
        box_layout3 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.28)
        box_layout4 = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.16)
        hint = Label(text="W przyszłości będziesz mógł szybko wybrać tą aktywność z listy aktywności", size_hint_y=0.4)
        self.activity = TextInput(multiline=False, size_hint_y=0.9, size_hint_x=0.75)
        self.activity_kcalh = TextInput(multiline=False, size_hint_y=0.9, size_hint_x=0.2)
        self.activity_duration = TextInput(multiline=False, size_hint_y=0.9, size_hint_x=0.2)
        activity_label = Label(text="Nazwa:", size_hint_x=0.25)
        per_hour_label = Label(text="Ile średnio spalasz kalorii na godzinę przy tej aktywnośći", size_hint_y=0.8)
        my_time_label = Label(text="Czas trwanie dzisiejszego treningu (w min)", size_hint_y=0.8)
        box_layout1.add_widget(activity_label)
        box_layout1.add_widget(self.activity)
        box_layout2.add_widget(per_hour_label)
        box_layout2.add_widget(self.activity_kcalh)
        box_layout3.add_widget(my_time_label)
        box_layout3.add_widget(self.activity_duration)
        box_layout4.add_widget(Button(text="Dodaj", size_hint_y=0.9, on_release=lambda *args: self.btn()))
        for item in [box_layout1, box_layout2, box_layout3, box_layout4, hint]:
            root_layout.add_widget(item)
        self.popup = Popup(title="Dodaj nową aktywność", content=root_layout,
                           size_hint=(0.9, 0.6))

    def btn(self):
        error = False
        try:
            int(self.activity_kcalh.text)
        except ValueError:
            self.activity_kcalh.text = "Tylko\ncyfry"
            error = True
        try:
            int(self.activity_duration.text)
        except ValueError:
            self.activity_duration.text = "Tylko\ncyfry"
            error = True
        if not self.activity.text:
            self.activity.text = "Nazwa nie może być pusta"
            error = True
        if not error:
            kcal = round((int(self.activity_kcalh.text) / 60) * int(self.activity_duration.text))
            user.add_custom_exercise(self.activity.text, self.activity_duration.text, kcal)
            with open("activities.txt", "a") as activities_file:
                activities_file.write(self.activity.text + "\n")
                activities_file.write(self.activity_kcalh.text + "\n")
            PhysicalActivities.update()
            ActivityPopupWidgets.close_activity_popup()


class WorkoutRecycleView(BoxLayout):
    workout_list = ObjectProperty()

    def show_workouts(self):
        acts = PhysicalActivities.activities.keys()
        self.workout_list.data = [{"text": str(act)} for act in acts]


class ActivityButton(Button):
    def select_activity(self, activity):
        ActivityPopupWidgets.workout_duration_open(activity)


class ActivityPopupWidgets:
    popup = None
    duration_popup = None
    water_popup = None
    custom_activity_popup = None

    def __init__(self, title, labels_text, buttons=()):
        self.screen_names = ["workout", "meal", "water", "hunger", "home"]
        root_layout = BoxLayout(orientation="vertical")
        self.screen_manager = ScreenManager()
        """Home Popup Screen"""
        home_screen = Screen(name=self.screen_names[-1])
        secondary_layout = BoxLayout(orientation="vertical")
        layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        for item in labels_text:
            label = Label(text=item)
            label.size_hint = (1, None)
            label.height = 80
            layout.add_widget(label)
        buttons = ("Wysiłek fizyczny", "Posiłek", "Woda", "Głód")
        button0 = Button(text=buttons[0], on_release=lambda *args: self.change_screen(self.screen_names[0]))
        button1 = Button(text=buttons[1], on_release=lambda *args: self.change_screen(self.screen_names[1]))
        button2 = Button(text=buttons[2], on_release=lambda *args: self.open_water_popup())
        button3 = Button(text=buttons[3], on_release=lambda *args: self.hunger())
        for button in [button0, button1, button2, button3]:
            button.size_hint_y = None
            button.height = "60dp"
            layout.add_widget(button)
        root = ScrollView(size_hint=(1, 1), size=(Window.width, Window.height))
        root.add_widget(layout)
        secondary_layout.add_widget(root)
        home_screen.add_widget(secondary_layout)
        self.screen_manager.add_widget(home_screen)
        root_layout.add_widget(self.screen_manager)
        root_layout.add_widget(Button(text="Zamknij okno", size_hint_y=0.1,
                                      on_release=lambda *args: UserHub.close_info()))
        """Workout Screen"""
        workout_screen = Screen(name=self.screen_names[0])
        workout_screen.add_widget(self.workout_screen_init())
        self.screen_manager.add_widget(workout_screen)

        meal_screen = Screen(name=self.screen_names[1])
        meal_screen.add_widget(MealScreen())
        self.screen_manager.add_widget(meal_screen)

        self.popup = Popup(title=title,
                           content=root_layout, size_hint=(0.9, 0.9))

    def change_screen(self, screen_name):
        self.screen_manager.current = screen_name

    def workout_screen_init(self):
        secondary_layout = BoxLayout(orientation="vertical")
        layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=3)
        layout.bind(minimum_height=layout.setter('height'))
        secondary_layout.add_widget(
            Label(text="Wybierz rodzaj wysiłku sposród poniższych, lub wprowadź własny:", size_hint_y=None,
                  height="40dp"))
        workouts = WorkoutRecycleView()
        workouts.show_workouts()
        secondary_layout.add_widget(workouts)
        secondary_layout.add_widget(
            Button(text="Dodaj własny", size_hint_y=None, height="40dp", on_release=self.add_activity))
        return secondary_layout

    @classmethod
    def hunger(cls):
        UserHub.close_info()
        user.add_hunger_mark()
        cls.popup = HubPopupWidgets("Dodano Pomyślnie",
                                    ("Odnotowaliśmy twój głód. Jeśli możesz, zjdedz coś, śmiało :)",),
                                    ActivityPopupWidgets)
        cls.popup.popup.open()

    @classmethod
    def open_water_popup(cls):
        cls.water_popup = WaterPopup()
        cls.water_popup.water_popup.open()

    @classmethod
    def close_water_popup(cls):
        cls.water_popup.water_popup.dismiss()
        UserHub.close_info()
        cls.popup = HubPopupWidgets("Dodano Pomyślnie", (user.message,), ActivityPopupWidgets)
        cls.popup.popup.open()

    @classmethod
    def close_activity_popup(cls):
        cls.custom_activity_popup.popup.dismiss()
        UserHub.close_info()
        cls.popup = HubPopupWidgets("Dodano Pomyślnie", (user.message,), ActivityPopupWidgets)
        cls.popup.popup.open()

    @classmethod
    def workout_duration_open(cls, activity):
        cls.duration_popup = DurationPopup(activity)
        cls.duration_popup.duration_popup.open()

    @classmethod
    def close_duration(cls):
        cls.duration_popup.duration_popup.dismiss()
        UserHub.close_info()
        cls.popup = HubPopupWidgets("Dodano Pomyślnie", (user.message,), ActivityPopupWidgets)
        cls.popup.popup.open()

    @classmethod
    def add_activity(cls, instance):
        cls.custom_activity_popup = CustomActivityPopup()
        cls.custom_activity_popup.popup.open()

    @classmethod
    def close_info(cls):
        cls.popup.popup.dismiss()


class MealScreen(BoxLayout):
    popup = None
    food_item = ObjectProperty()
    search_results = ObjectProperty()
    search_button = ObjectProperty()

    def meal_search(self):
        search_url = "https://api.edamam.com/api/nutrition-details"

        try:
            translation = language_translator.translate(
                text=self.food_item.text,
                model_id='pl-en').get_result()
        except requests.exceptions.ConnectionError:
            self.search_button.disabled = True
            self.search_results.data = [{"text": "Brak połączenia internetowego"}]
        else:
            print(translation)
            translated_food = translation.get("translations")[0].get("translation")
            food = quote(translated_food)
            kivy_request = UrlRequest("https://api.edamam.com/api/nutrition-data?app_id={}&app_key={}&ingr={}".format(
                config.api_headers["app_id"], config.api_headers["app_key"], food), self.print_results)

    def print_results(self, request, data):
        print(data)
        if data["calories"] != 0:
            my_data = {"Kalorie": str(round(data["calories"])) + "kcal", "Masa (g)": round(data["totalWeight"])}
            try:
                d = data["totalNutrients"]
            except KeyError:
                my_data["Brak więcej danych"] = ""
            else:
                for nutrient in d:
                    if nutrient == "ENERC_KCAL":
                        continue
                    label_ang = data["totalNutrients"][nutrient]["label"]
                    label = nutrient_dictionary.nutrients[label_ang]
                    if not label:
                        continue
                    quantity = data["totalNutrients"][nutrient]["quantity"]
                    unit = data["totalNutrients"][nutrient]["unit"]
                    if label in user.displayed_nutrients:
                        my_data[label] = str(round(quantity, 2)) + unit
            self.calories = data["calories"]
            self.search_results.data = [{'text': str(categ) + ": " + str(value)} for categ, value in my_data.items()]
            AddButton.disabled = False
        else:
            self.search_results.data = [{'text': "Nie znaleziono"}]

    def add_food_to_user(self):
        AddButton.disabled = True
        user.add_meal(self.food_item.text, self.calories)
        UserHub.close_info()
        self.open_popup(self.food_item.text, self.calories)

    @classmethod
    def open_popup(cls, item, kcal):
        cls.popup = HubPopupWidgets("Dodano Pomyślnie", (f"Posiłek: {item} który zawierał {kcal}kcal",), MealScreen)
        cls.popup.popup.open()

    @classmethod
    def close_info(cls):
        cls.popup.popup.dismiss()


class AddButton(Button):
    disabled = True


class UserHub(Screen):
    popup = None
    mood_popup = None
    message_popup = None
    activities = ObjectProperty()
    status = ObjectProperty()
    water_status = ObjectProperty
    bmi_button = ObjectProperty()

    def __init__(self, **kwargs):
        super(UserHub, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_activities, 2)
        Clock.schedule_interval(self.check_time_popup, 2)

    def update_activities(self, td):
        user.calculate_bmi()
        user.calculate_water()
        user.calculate_hydration()
        try:
            user.water_balance -= user.water_per_second
        except TypeError:
            pass
        self.bmi_button.text = f"BMI: {user.bmi}"
        self.bmi_button.background_color = user.bmi_color
        if len(user.activities_today) == 0:
            self.activities.data = [{"text": "Nic nie dodano jescze dzisiaj."}]
        else:
            self.activities.data = [{"text": str(activity)} for activity in user.activities_today]
            self.status.text = "Bilans kaloryczny: " + str(round(user.kcal)) + "kcal"
        self.water_status.text = f"Nawodnienie organizmu: {user.hydration}%"

    @classmethod
    def home_activity_display(cls):
        cls.popup = ActivityPopupWidgets("Dodaj Czynność", ("Wybierz spośród poniższych:",))
        cls.popup.popup.open()

    @classmethod
    def close_info(cls):
        AddButton.disabled = True
        try:
            cls.popup.popup.dismiss()
        except AttributeError:
            pass
        try:
            cls.message_popup.popup.dismiss()
        except AttributeError:
            pass

    @classmethod
    def check_time_popup(cls, td):
        if user.setup_complete:
            if user.afternoon_check_time is not None and user.evening_check_time is not None:
                time = get_current_time().split(":")
                if int(time[0]) >= user.evening_check_time and user.mood_checks_left >= 1:
                    cls.popup = MoodCheckPopup()
                    cls.popup.popup.open()
                    user.mood_checks_left = 0
                elif int(time[0]) >= user.afternoon_check_time and user.mood_checks_left == 2:
                    cls.popup = MoodCheckPopup()
                    cls.popup.popup.open()
                    user.mood_checks_left -= 1

    @classmethod
    def close_mood_popup(cls):
        cls.popup.popup.dismiss()

    @classmethod
    def open_message_popup(cls, title, contents):
        cls.message_popup = HubPopupWidgets(title, contents, UserHub)
        cls.message_popup.popup.open()

    @classmethod
    def meal_search(cls):
        cls.popup = ActivityPopupWidgets("Sprawdź produkt", "")
        cls.popup.change_screen("meal")
        cls.popup.popup.open()


class MoodCheckPopup:
    def __init__(self):
        self.popup = Popup(title="Jakie jest twoje sampoczucie w tej chwili?",
                           content=MoodCheckLayout(),
                           size_hint=(0.9, 0.6))


class MoodCheckLayout(BoxLayout):
    def analyze_mood(self, state):  # TODO Here analyze nutrients, exercise etc. and display hints for the remainder
        # of the day / next day. Many if else statements. SPLIT INTO DAY AND EVENING
        UserHub.close_mood_popup()
        if user.mood_checks_left == 1:  # Afternoon messages
            if state == "great":
                UserHub.open_message_popup("Świetnie!",
                                           ("Cieszymy się że się dobrze czujesz.",
                                            "Działaj dalej a będziesz nie do powsztymania!"))
            elif state == "tried":
                UserHub.open_message_popup("Podpowiedź: Zalecamy odpocząć",
                                           ("Postaraj się położyć wcześniej spać dzisiaj jeśli możesz.",
                                            "Rześkie i zregenerowane ciało i umysł działają najlepiej.",
                                            "Jeśli nie jesteś w stanie funkcjonować, zrób sobie 45minutową drzemke zad dnia."))
            else:
                UserHub.open_message_popup("Podpowiedź: Znajdź przyczynę",
                                           (
                                           "Jeśli za mało spałeś w nocy, spróbuj wziąc nie więcej jak 45min drzemkę jeszcze za dnia",
                                           "Jeśli wydaje Ci się że spałeś odpowiednio długo, daj ciału się trochę poruszać",
                                           "Nawet pół godzinny trening może cię rozbudzić :)"))
        else:  # Evening messages
            if state == "great":
                UserHub.open_message_popup("Świetnie!",
                                           ("Cieszymy się że się dobrze czujesz.",
                                            "Tak dalej trzymaj w kolejnych dniach!"))
            elif state == "tried":
                UserHub.open_message_popup("Podpowiedź: Zalecamy odpocząć",
                                           ("Postaraj się położyć spać za niedługo.",
                                            "Jeśli masz problemy z zasypianien mimo zmęczenią, spróbuj odłożyc wszystkie ekrany elektroniczne,",
                                            "Znajź jakąś książkę, lub spokojną muzykę, lampkę o ciepłej barwie, i odpręż ciałó",
                                            "Pomocne może być także włączenie trybu niskiego poziomu świateł niebieskich",
                                            "w wyświetlaczach elektronicznych po zachodzie słońca"))
            else:
                UserHub.open_message_popup("Podpowiedź: Pozwój organizmowi odpocząć",
                                           ("Odłóź wszystkie urządzenia elektroniczne, odpręź się, i śpij.",))

class ConfirmationPopup(Popup):
    def __init__(self, parent, **kwargs):
        super(ConfirmationPopup, self).__init__(**kwargs)
        self.title = "Potwierdzenie"
        root_layout = BoxLayout(orientation="vertical")
        root_layout.add_widget(Label(text="Czy napewno?"))
        layout = BoxLayout()
        layout.add_widget(Button(text="Tak", on_release=parent.confirmed))  # try removing parenthesis
        layout.add_widget(Button(text="Nie", on_release=self.dismiss))
        root_layout.add_widget(layout)
        self.content = root_layout
        self.size_hint = (0.9, 0.3)

class SettingsScreen(Screen):
    new_weight = ObjectProperty()
    new_height = ObjectProperty()
    confirmation_popup = None

    def check_changes(self):
        if self.new_weight.text == "":
            pass
        else:
            try:
                int(self.new_weight.text)
            except ValueError:
                self.new_weight.text = "Wpisz tylko cyfry"
            else:
                user.mass = int(self.new_weight.text)
                self.new_weight.text = "Zapisano zmiany: " + self.new_weight.text
        if self.new_height.text == "":
            pass
        else:
            try:
                int(self.new_height.text)
            except ValueError:
                self.new_height.text = "Wpisz tylko cyfry"
            else:
                user.height = int(self.new_height.text)
                self.new_height.text = "Zapisano zmiany: " + self.new_height.text

    def clear_input(self):
        self.new_height.text = ""
        self.new_weight.text = ""

    @classmethod
    def confirmation_box(cls):
        global user
        user = UserProfile()
        confirmation_popup = ConfirmationPopup(SettingsScreen)
        confirmation_popup.open()

    @staticmethod
    def confirmed(instance):
        with open("user.json", "w") as clear_file_contents:
            pass
        exit()


class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        global user
        super(WindowManager, self).__init__(**kwargs)
        if not path.isfile("user.json"):
            user = UserProfile()
            self.add_widget(InfoScreen())

        else:
            with open("user.json") as user_file:
                file_contents = user_file.read()
                if len(file_contents) > 10:
                    user_stats = json.loads(file_contents)
                    print(user_stats)
                    seconds_past_midnight = datetime.now() - datetime.today().replace(hour=0, minute=0, second=0)
                    print(seconds_past_midnight.seconds)
                    if not user_stats["setup_complete"]:
                        user = UserProfile()
                        self.add_widget(InfoScreen())
                    else:
                        if (datetime.now() - datetime.strptime(user_stats["first_day"], "%Y-%m-%d")).days != 0:
                            for item in ["activities_today", "hunger_marks", "nutrients_today"]:
                                del user_stats[item]
                        user = UserProfile(**user_stats)
                        if str(datetime.now())[:10] == user_stats["save_date"]:
                            water_balance = (user_stats["water_needed"] / 86400) * (time.time() - user_stats["save_time"])
                        else:
                            water_balance = (user_stats["water_needed"] / 86400) * seconds_past_midnight.seconds
                        print(water_balance)
                        user.water_balance -= water_balance
                        self.add_widget(UserHub())
                else:
                    user = UserProfile()
                    self.add_widget(InfoScreen())


class MainApp(App):
    def build(self):
        return MyRootBoxLayout()


if __name__ == "__main__":
    MainApp().run()
