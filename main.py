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
from kivy.uix.recyclelayout import RecycleLayout
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, ScreenManager

from os import path
from webbrowser import open as browser_open
from datetime import datetime
from urllib.parse import quote

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
        self.goal = None
        self.diet = None
        self.first_day = None  # TODO implement this
        self.setup_complete = False
        self.day = 1
        self.activities_today = []
        self.kcal = 0
        self.message = None
        self.hunger_marks = []
        self.displayed_nutrients = nutrient_dictionary.default_nutrients
        self.nutrients_today = dict()

        self.sex = None
        self.mass = None
        self.height = None
        self.age = None
        self.bmi = None
        self.bmi_color = (0, 1, 0, .5)
        Clock.schedule_interval(self.auto_save_user_info, 1)

    def auto_save_user_info(self, dt):
        with open("user.txt", "w") as save_file:
            print(self.__dict__, file=save_file)

    def add_meal(self, meal, calories):
        self.activities_today.append(f"{get_current_time()} Posiłek: {meal} +{calories}kcal")
        self.kcal += calories

    def add_water(self, amount):
        self.message = f"Wypito {amount}ml wody"
        self.activities_today.append(f"{get_current_time()} Woda: {amount}ml")

    def add_exercise(self, activity, duration):
        duration = int(duration)
        print("Adding..")
        duration_hours = duration // 60
        duration_minutes = duration % 60
        # if duration_hours < 1: TODO
        kcal = int(PhysicalActivities.activities[activity]) * duration / 60
        self.kcal -= kcal
        self.message = f"Dodano {activity}, trwająca {duration} minut"
        self.activities_today.append(f"{get_current_time()} {activity} -{round(kcal)}kcal")

    def add_hunger_mark(self):
        self.hunger_marks.append(get_current_time())

    def calculate_bmi(self):
        self.bmi = round(self.mass / (self.height / 100) ** 2, 1)
        if self.bmi < 18.5:
            self.bmi_color = (0, .1, 1, .5)
        elif 18.5 <= self.bmi < 25:
            self.bmi_color = (0, 1, 0, .5)
        elif 25 <= self.bmi < 30:
            self.bmi_color = (.9, .5, 0, .5)
        else:
            self.bmi_color = (1, 0, 0, .5)

user = UserProfile() # before app loads

class UserInfoScreen(Screen):
    popup = None
    _height = ObjectProperty()
    mass = ObjectProperty()
    age = ObjectProperty()

    def __init__(self, **kwargs):
        super(UserInfoScreen, self).__init__(**kwargs)
        self.is_male = False
        self.is_female = False

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
    root_layout = BoxLayout(orientation="vertical")
    # TODO transition this to KV file and add ObjectProperties
    layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
    layout.bind(minimum_height=layout.setter('height'))
    heading1 = Label(text="Statystyki Użytkowinika", font_size="20dp")
    body1 = Label(text=f"Dzień: {user.day}\nDzień rozpoczęcia: {user.first_day if user.first_day is not None else 'Brak danych'}\n")
    body1a = Label(text=f"Cel: {user.goal}\nWybrana dieta: {user.diet}\n")
    heading2 = Label(text="O aplikacji", font_size="20dp")
    body2 = Label(text="Wersja: 0.0.8\n\n")
    heading3 = Label(text="Autorzy", font_size="18dp")
    body3 = Label(text="Architekt/Programista: Dawid Lachowicz\n\nGrafik: Marcel Jarosik")
    for item in [heading1, body1, body1a, heading2, body2, heading3, body3]:
        item.size_hint = (1, None)
        item.height = 120
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
    day = 1
    day_text = f"Dzień {day}"

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
        root_layout = BoxLayout(orientation="vertical")
        layout = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        for item in labels_text:
            label = Label(text=item)
            label.size_hint = (1, None)
            label.height = 80
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
        browser_open("https://www.poradnikzdrowie.pl/diety-i-zywienie/odchudzanie/jaka-jest-zbilansowana-dieta-optymalna-dla-ciebie-aa-cJ56-67oc-F24F.html")


class NutrientSelector(BoxLayout):
    def __init__(self, **kwargs):
        super(NutrientSelector, self).__init__(**kwargs)
        self.selected_nutrients = user.displayed_nutrients
    def check_box(self, nutrient):
        if nutrient in user.displayed_nutrients:
            user.displayed_nutrients.remove(nutrient)
        else:
            user.displayed_nutrients.append(nutrient)
        print(user.displayed_nutrients)



class NutrientScreen(Screen):

    @classmethod
    def display_info(cls):
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
    print(activities)


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
        user.add_exercise(self.activity, self.duration.text)
        ActivityPopupWidgets.close_duration()

class WaterPopup():
    def __init__(self):
        box_layout = BoxLayout(orientation="horizontal", spacing=10)
        self.amount = TextInput(multiline=False, size_hint_y=0.9)
        box_layout.add_widget(self.amount)
        box_layout.add_widget(Button(text="Dodaj", size_hint_y=0.9, on_release=lambda *args: self.btn()))
        self.water_popup = Popup(title="Wprowadz ilość wypitej wody (w ml)", content=box_layout,
                                    size_hint=(0.8, 0.2))

    def btn(self):
        user.add_water(self.amount.text)
        ActivityPopupWidgets.close_water_popup()

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
        """Workout Screen"""  # TODO check if order is ok
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
        secondary_layout.add_widget(Label(text="Wybierz rodzaj wysiłku sposród poniższych, lub wprowadź własny:", size_hint_y=None, height="40dp"))
        workouts = WorkoutRecycleView()
        workouts.show_workouts()
        secondary_layout.add_widget(workouts)
        return secondary_layout

    @classmethod
    def hunger(cls):
        UserHub.close_info()
        user.add_hunger_mark()
        cls.popup = HubPopupWidgets("Dodano Pomyślnie", ("Odnotowaliśmy twój głód. Jeśli możesz, zjdedz coś, śmiało :)",), ActivityPopupWidgets)
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
    def workout_duration_open(cls, activity):
        cls.duration_popup = DurationPopup(activity)
        cls.duration_popup.duration_popup.open()

    @classmethod
    def close_duration(cls):
        cls.duration_popup.duration_popup.dismiss()
        UserHub.close_info()
        cls.popup = HubPopupWidgets("Dodano Pomyślnie", (user.message,), ActivityPopupWidgets)
        cls.popup.popup.open()
        # TODO MAKE SUCCESS DIALOG CLOSE PROPERLY AND MAKE IT TAKE Y SIZE AS ARGUMENT

    @classmethod
    def close_info(cls):
        cls.popup.popup.dismiss()

class MealScreen(BoxLayout):
    popup = None
    food_item = ObjectProperty()
    search_results = ObjectProperty()

    def meal_search(self):
        search_url = "https://api.edamam.com/api/nutrition-details"

        translation = language_translator.translate(
            text=self.food_item.text,
            model_id='pl-en').get_result()
        print(translation)
        translated_food = translation.get("translations")[0].get("translation")
        food = quote(translated_food)
        kivy_request = UrlRequest("https://api.edamam.com/api/nutrition-data?app_id={}&app_key={}&ingr={}".format(config.api_headers["app_id"], config.api_headers["app_key"], food), self.print_results)

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
    activities = ObjectProperty()
    status = ObjectProperty()
    water_status = ObjectProperty
    bmi_button = ObjectProperty()

    def __init__(self, **kwargs):
        super(UserHub, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_activities, 2)

    def update_activities(self, td):
        # print(user.bmi)
        self.bmi_button.text = f"BMI: {user.bmi}"
        self.bmi_button.background_color = user.bmi_color
        if len(user.activities_today) == 0:
            self.activities.data = [{"text": "Nic nie dodano jescze."}]
        else:
            self.activities.data = [{"text": str(activity)} for activity in user.activities_today]
            self.status.text = "Bilans kaloryczny: " + str(round(user.kcal)) + "kcal"
            self.water_status.text = "Nawodnienie organizmu: 50%"

    @classmethod
    def home_activity_display(cls):
        cls.popup = ActivityPopupWidgets("Dodaj Czynność", ("Wybierz spośród poniższych:",))
        cls.popup.popup.open()

    @classmethod
    def close_info(cls):
        cls.popup.popup.dismiss()


class WindowManager(ScreenManager):
    def __init__(self, **kwargs):
        super(WindowManager, self).__init__(**kwargs)
        if not path.isfile("user_not.txt"): # TODO CHANGE file name to be correct
            user = UserProfile()
            self.add_widget(InfoScreen())
            with open("user.txt", "w") as user_file:
                pass
        else:
            with open("user.txt") as user_file:
                if len(user_file.readlines()) != 5:
                    user = UserProfile()
                else:
                    user = UserProfile()
            self.add_widget(UserHub())


class MainApp(App):
    def build(self):
        return MyRootBoxLayout()


if __name__ == "__main__":
    MainApp().run()
