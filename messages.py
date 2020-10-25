instructions = ["Uwaga! Wszystkie statystyki i podpowiedzi są tylko przybliżeniem.", "Zalecamy kierować się zdrowym"
                " rozsądkiem korzytsając z aplikacji :)", "Jak Korzystć z aplikacji?", "1. Wskaźnik BMI",
                "Na górze ekranu widnieje barwny wskaźnik BMI z twoją wartością BMI", "Niebieski kolor: Niedowaga",
                "Zielony kolor: Prawidłowa waga", "Pomarańczowy kolor: Lekka nadwaga", "Czerwony kolor: Nadwaga",
                "Jeśli twoim celem jest zbudowanie dużej muskulatury, nie przejmuj się tym wskaźnikiem", "",
                "2. Aktualizacja wagi bądź wzrostu oraz ustawienie", "Możesz w każdej chwili zaktualizować informacje wagi i wzrostu",
                "Możesz tu zmienić wyświetlone składniki odżywcze w pokarmie", "Ponadto, jeśli chcesz wyświetlić ten kominikat ponownie "
                "taka możliwość też tutaj się znajduje", "Aby usunąć dane i/lub rozpocząć od nowa:",
                "Kliknij odpowiedni przycisk w \"Ustawieniach\"", "", "3. Bilans Kaloryczny",
                "UWAGA! Jest to tylko wskaźnik orientacyjny",  "Nie bierze on pod uwagę prędkości twojego metabolizmu, który jest różny u każdego człowieka!",
                "Bilans aktualizuje się po treningu, po posiłku, oraz w stanie spoczynku.", "", "4. Wskaźnik nawodnienia organizmu",
                "Idealnie wskaźnik powinien wynosić około 100%, choć powyżej też oczywiście jest w porządku",
                "Jeśli wynosi poniżej 20%, organizm może wkrótce ulec odwodnieniu", "Wskaźnik zmienia swoją barwę w przypadku odwodnienia bądź stanu temu bliskiemu",
                "Wodę można uzupełnić po prostu pijąc wodę, bądź spożwywając pokarm ją zawierający.", "Woda jest niustannie tracona przez organizm dlatego należy ją regularnie uzupełniać",
                "Szczególnie podczas oraz po wysiłku fizycznym!", "", "5. Pełne statystyki dnia", "Tutaj znajdziesz sumaryczne podsumowanie swojego dnia",
                "Wyświetlane są statystyki dotyczące wysiłku fizycznego, spożytej wody", "A także każdego poszczególnego składnika spożywczego spożytego w ciągu dnia.",
                "", "6. Sprawdź produkt", "Tutaj możesz wyszukać praktycznie dowolny produkt spożywczy, stosując się do podanej składni wyszukania",
                "Ważne jest by koniecznie podać ilość produktu, czy to w sztukach, gramach, czy nawet miskach.",
                "Po wyszukaniu, wyświetlają się te wartości odżywcze produktu, które wybrałeś wcześniej.",
                "Jeśli spożyłeś ten produkt, możesz śmiało dodać do \"spożytych dzisiaj posiłków\"", "",
                "7. Główny ekran", "Na środku ekranu będą się wyświetlały wszystkie aktywności które dodasz w ciągu dnia.", "",
                "8. Dodawanie Aktywności", "Możesz dodawać aktywności takie jak wysiłek fizyczny, posiłek, oraz wypicie wody.",
                "W aplikacji jest kilkanaście aktywności fizycznych wbudowanych, lecz zawsze możesz dodać i zapisać własną", "",
                "9. Powiadomienia o samopoczuciu", "Po południu oraz wieczorem będą wyświetlały się kominukaty pytające Cię o samopoczucie",
                "Po wybraniu samopoczucia, wyświetlamy Ci podpowiedzi na popołudnie lub na następny dzień"
                ]


def min_options():
    instructions.insert(13, "Ustaliłeś sobie za cel zrzucenie kilogramów.")
    instructions.insert(14, "Warto w tym przypadku regularnie ważyć się, aby zmierzyć swój progres")
    instructions.insert(23, "Aby zrzucić wagę, bilans orientacyjnie powinień wynosić poniżej 0")


def stay_options():
    instructions.insert(21, "Aby utrzymać swoją wagę, bilans orientacyjnie powinień wynosić około 0")


def max_options():
    instructions.insert(13, "Ustaliłeś sobie za cel nabranaie masy.")
    instructions.insert(14, "Warto w tym przypadku ważyć się od czasu do czasu, aby zmierzyć swój progres")
    instructions.insert(23, "Aby nabrać masę, bilans orientacyjnie powinien wynosić powyżej 0")
    instructions.insert(24, "Nie oznacza to jednak, że nie należy ćwiczyć.. wręcz przeciwnie!")
    instructions.insert(25, "Chodzi o to by po treningu w nadmiarze uzupełniać zużytą energii.")


if __name__ == "__main__":
    max_options()
    for count, item in enumerate(instructions):
        print(str(count) + ".", item)