# Xiaomi Mijia Whale Smart Toilet Cover

[![HACS validation](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hacs.yaml/badge.svg)](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hacs.yaml)
[![Hassfest](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/actions/workflows/hassfest.yaml)

Nowoczesna integracja Home Assistant dla deski sedesowej **Xiaomi Mijia Whale Smart Toilet Cover** (`xjx.toilet.pro`). Komunikuje się lokalnie przez protokół Xiaomi miIO — po skonfigurowaniu nie wymaga chmury Xiaomi.

Projekt jest rozwinięciem integracji [tykarol/home-assistant-xjx-toilet-pro](https://github.com/tykarol/home-assistant-xjx-toilet-pro), dostosowanym do Home Assistant 2026.9+. Nie wymaga starego, osobnego komponentu `toiletlid` ani konfiguracji YAML.

## Funkcje

- konfiguracja z interfejsu Home Assistant,
- lokalne odpytywanie urządzenia co 30 sekund,
- czujnik zajęcia deski,
- czujnik działania filtra powietrza,
- przełącznik oświetlenia nocnego LED,
- przełącznik samooczyszczania,
- akcja `xjx_toilet_pro.send_command` do zaawansowanych automatyzacji,
- możliwość zmiany adresu IP i tokenu przez opcję **Konfiguruj ponownie**.

## Instalacja przez HACS

1. W HACS otwórz menu i wybierz **Niestandardowe repozytoria**.
2. Dodaj `https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet` jako typ **Integracja**.
3. Wyszukaj **Xiaomi Mijia Whale Smart Toilet Cover** i wybierz **Pobierz**.
4. Uruchom ponownie Home Assistant.
5. Przejdź do **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
6. Wyszukaj nazwę integracji, a następnie podaj lokalny adres IP i 32-znakowy token miIO.

## Instalacja ręczna

Skopiuj katalog `custom_components/xjx_toilet_pro` do `/config/custom_components/xjx_toilet_pro` w Home Assistant, uruchom Home Assistant ponownie i dodaj integrację z poziomu interfejsu.

## Migracja ze starej wersji

1. Usuń lub wyłącz `custom_components/toiletlid` oraz wcześniejszą wersję `custom_components/xjx_toilet_pro`.
2. Usuń starą sekcję YAML, np.:

   ```yaml
   toiletlid:
     - platform: xjx_toilet_pro
       host: 192.168.1.50
       token: !secret xjx_toilet_pro_token
   ```

3. Zainstaluj tę wersję, uruchom Home Assistant ponownie i skonfiguruj urządzenie w interfejsie.

## Akcja surowej komendy

Akcja `xjx_toilet_pro.send_command` przyjmuje:

- `config_entry_id` — identyfikator wpisu integracji (wybierany w edytorze akcji),
- `command` — nazwa komendy miIO,
- `params` — opcjonalna lista lub mapa parametrów.

Przykład:

```yaml
action: xjx_toilet_pro.send_command
data:
  config_entry_id: 01JEXAMPLE123456789
  command: func_off
  params:
    - night_led
```

Surowe komendy omijają zabezpieczenia encji. Korzystaj z nich tylko wtedy, gdy znasz zachowanie danej komendy urządzenia.

## Ważne informacje

- Urządzenie powinno mieć stały lub zarezerwowany adres IP.
- Token miIO ma dokładnie 32 znaki i nie jest wypisywany w logach.
- Integracja obsługuje model `xjx.toilet.pro`.
- Autor modernizacji nie miał fizycznego urządzenia do końcowego testu sprzętowego; zgłoszenia z logami diagnostycznymi są mile widziane w [Issues](https://github.com/g1n10l/Xiaomi-Whale-Smart-Toilet/issues).

## Licencja i autorzy

Kod jest udostępniany na licencji MIT. Podziękowania dla [tykarol](https://github.com/tykarol) za pierwotną integrację i rozpoznanie komend urządzenia.
