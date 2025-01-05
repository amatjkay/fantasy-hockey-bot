# Гайд по проекту Fantasy Hockey Bot

## Описание проекта
Fantasy Hockey Bot - это проект для автоматизации работы с фэнтези-хоккейной лигой ESPN. Бот собирает статистику игроков, формирует ежедневные команды лучших игроков и отправляет результаты в Telegram.

# Настройки сезона
SEASON_ID=2025
SEASON_START=2024-10-04
SEASON_START_SCORING_PERIOD=1

# Доступ к апи
## Авторизация
curl ^"https://registerdisney.go.com/jgc/v8/client/ESPN-ONESITE.WEB-PROD/guest/login?langPref=en-US^&feature=no-password-reuse^" ^
  -H ^"accept: */*^" ^
  -H ^"accept-language: ru-RU,ru;q=0.5^" ^
  -H ^"authorization: APIKEY wP7HWX/+X/Dxx+GtFCb6CKivH8LS1k5YR1rrfiP6cDMagXQA1JybcXOQIwSI2EUjvxSIZ4uM/YXNOmOwx1B8I6I5tpFS^" ^
  -H ^"cache-control: no-cache^" ^
  -H ^"content-type: application/json^" ^
  -H ^"conversation-id: 59056aab-6607-4039-a9bd-b85e2c8419af^" ^
  -H ^"correlation-id: 87db69a9-a854-4fae-9b34-c9dd3f4a9601^" ^
  -H ^"device-id: e63e04f7-311e-4205-962a-94562f7435d1^" ^
  -H ^"expires: -1^" ^
  -H ^"g-recaptcha-token: 03AFcWeA4B2Cw0mgvGFNEEqSPn1JZWSEkw1vhAVO1IIPPLnq9zSGehhZF6t6qu1scss8K3PiRu5RZH6ZT2QC0mKkJxhyPVFcXrwBvNYqGyL6zzMqjzECnC3xTiPJmLptI9EK335borWNHub7pTVFdk00dnUjoJo8dLUMg3ZD_3SpVBhU76K2dE4R5z1rir_lj8jB8omebi15Uk539aQbyuaXz7IBvAlYMuRQCrPqfxZ755g8K9_ky1fIfu2d0VSyrIIV6YQi6pzo5DPInpP9DGw92CmZzCrJdgR8awC8aXkWYjMQ_69XIbhKqXckvQjhU-BDqmOzwl49enCfBwQw3Vs1xpsRs9Z_GG2RmrsJ0tpDQTuu3frKb4xrsPM-L4NbOHcrtC4UNAsEzJsFp6rtWGCEEny-GENyOYAh1F71CDEnAt7qdha0pnudunI3i5NiiKwCkncGrjKqHPK0PKVbRUrgL4i0rpfz9tPgZie-yb2NfyE099ZXA-LgqvsNjNTGRYOEnmBN022CNIPvBcgwW3RuuGt9UXHFXzqwtNGNXApqOSup7kLNmNqOsDd_IgxTcBe6YmKouPvYlozmbZeVsEminXrthz91J9j3c5jDZ9vxAFn-D8eKDzUQescYn0Oy39aw893t7k7WR9hjAvUtF0lkMrUd0MhQXYUvAnYixQN2pHSdhkmYr7wTTVkKInWcUgI8JESGDUnGJzapPqVRkShJ_H5cX5ImZ4To21YJpupgmgp0LZdkxJzGX8SYlSFUGyclQPgL7F5DN5SkcyyyfgL3y-JB_rp45eri2NkHMbzJpHmXRW4t13pFmmiMvEcERcNr3e1KIs9r_p9dQ2DdfgpQGXnvCl6RJWAqqVpSP-j3OwCAAyzSWRQPAc0yTNJmDPwHSHiYIoIFGo_YLIUrrNG4DtE6lAE-CFWSQ34yVGiFxJ5Geuiul1jse2fxx4l5viEmPotZKNjJ9KhxLj5MxY7aKsymLfjAZr4PlepgyrRvS8YQmb-b7EGNufVUH2uslGerGheEUUfxdw6wkpnDGSCiugnVfN6mbJh0z2yxmmCoWyy3rPmjXWbMhC1CoSsfMIahNQ2CI5kcalBoXoieks_PNSF68jX02PZ9zoJ2Tv42CxVqTwJQkpriq4pCuCfHhltuN3DjsK4Km-lq2LHd-ff-umgQr9BXsGM51mjoaUaWPL9Bm2mpFWowJTMv3dOeaotrcHyPadRw15Fgc8UOWFyekI5jIySjA_xFmU7hdbZ4jGDXVGpvjjx2vzmio0gtOzHgudo3BgmxfGanJgwqwyjyCyy3-8v5VMifPFOJtmHnpmtYo6h6YxwBZlpZe5tQFWTwnyqT5-kIe1ZCCZrO8p6W9m05hyR73s8xrrHWWKU3Mx4oZK1uyAGvolDKVB94fN4GnKd3GhennSfMRZ-Rodi4RGqyYQkVrYWghf0KwMV1280OAmEUGsBtZr714CH_bpxg2AzadZ1aD9p_2hCCnnq9ehHMawaJBzTeuy2sOuQfsCdh4xZ93HBE9ywYX7-RnQRqOUQkq8zBQ0zEgkhyifqR9P1RKNlGCyJ3LIc2i4FAqiW2d3YQjXMOblpdU9RwOIzNcM_A0MdpV_EPpKyA9Naq02i-NpXZEZHe0NqpnE-rLUHD2Hpg-sI5Zg14n_xFdxxy9D3xuKzHNIIpq-l4Y7PN9XxN0kpNe0tihe1F3vBrh77bgytrXFK66pPId3pYiVH6V312pLKZsKzj8GGooZMVRI5dybs_EbTBdZSyy8ZmHpIs7xQyjbDTpSUu7Wqkvtq2aUHhDfJaDpQ8o5vjcvrt6-O0Q-KrFWDKBZEc_Ow2K2zsSaXOGC-EZZax6Cp8oLuPRd3QClFgVV-6MS9XACmKWTqoZaqlDeUcH6WHFoYYtf3C1vFgGe_SGpzNHIad1qCaRW9pPZFu8GxAy6x2VqY1ropxu4Q_gyxrEAB-OOK-qrb1LaZDoFmgrMvVV_u5LCCXPaoJrMKPNr^" ^
  -H ^"oneid-reporting: eyJjb252ZXJzYXRpb25JZCI6IjU5MDU2YWFiLTY2MDctNDAzOS1hOWJkLWI4NWUyYzg0MTlhZiJ9^" ^
  -H ^"origin: https://cdn.registerdisney.go.com^" ^
  -H ^"pragma: no-cache^" ^
  -H ^"priority: u=1, i^" ^
  -H ^"referer: https://cdn.registerdisney.go.com/^" ^
  -H ^"sec-ch-ua: ^\^"Brave^\^";v=^\^"131^\^", ^\^"Chromium^\^";v=^\^"131^\^", ^\^"Not_A Brand^\^";v=^\^"24^\^"^" ^
  -H ^"sec-ch-ua-mobile: ?0^" ^
  -H ^"sec-ch-ua-platform: ^\^"Windows^\^"^" ^
  -H ^"sec-fetch-dest: empty^" ^
  -H ^"sec-fetch-mode: cors^" ^
  -H ^"sec-fetch-site: same-site^" ^
  -H ^"sec-gpc: 1^" ^
  -H ^"user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36^" ^
  --data-raw ^"^{^\^"loginValue^\^":^\^"tiikii^@protonmail.com^\^",^\^"password^\^":^\^"Fktirf2021^\^"^}^"

# Доступ к статистике
## Первый игровой день сезона 2024-10-04
curl ^"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/484910394?scoringPeriodId=94^&view=kona_player_info^" ^
  -H ^"accept: application/json^" ^
  -H ^"accept-language: ru-RU,ru;q=0.5^" ^
  -H ^"cache-control: no-cache^" ^
  -H ^"cookie: device_61726d61=e63e04f7-311e-4205-962a-94562f7435d1; AMCVS_5BFD123F5245AECB0A490D45^%^40AdobeOrg=1; s_cc=true; AMCVS_EE0201AC512D2BE80A490D4C^%^40AdobeOrg=1; AMCV_EE0201AC512D2BE80A490D4C^%^40AdobeOrg=-330454231^%^7CMCIDTS^%^7C20091^%^7CMCMID^%^7C84854353163566543326598998417448230989^%^7CMCAID^%^7CNONE^%^7CMCOPTOUT-1735837699s^%^7CNONE^%^7CvVersion^%^7C3.1.2^%^7CMCAAMLH-1736000177^%^7C6^%^7CMCAAMB-1735830498^%^7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI; ESPN-ONESITE.WEB-PROD.api=RxBOyFgTKJmZQpRB1kntXLdIAkjb5F3XvyF7K0LmOVtaKlTI+TVnXB8SlCvBcTcJBIQIKVlRqAtX+QUUH5RpaNHwl0UB; espn_s2=AEB^%^2BNIgxVdJC26LG^%^2FhYNOjFbNzC2BQOe74ghK8OQTJ^%^2B39q3oJr8e^%^2B6tNmrpUwPNM9mwOhZ8yVYihZZD2^%^2Fa2QUG8Av^%^2FQN^%^2BRK4SdknjYyYxHeRYnueGinmp8KuAq9iXb5qItq^%^2BnC3P9Ih8oI8bkA^%^2FoJfh8Rn3rnYUNrN4SCUNABgGpWiH4rjbdCz5CG78BjCKPYLrMbnQ9kFjImZ^%^2B^%^2BVDtiNc2SSi^%^2Fqyml29J50K4SxURnpbIsABFcprnzeHad8Qy^%^2FH2bppBR^%^2BLH4SZybj8DOU2nNMz; SWID=^{42557BE5-EC56-4C18-993F-D6F95F7C7B3A^}; ESPN-ONESITE.WEB-PROD.token=5=eyJhY2Nlc3NfdG9rZW4iOiJleUpyYVdRaU9pSm5kV1Z6ZEdOdmJuUnliMnhzWlhJdExURTJNakF4T1RNMU5EUWlMQ0poYkdjaU9pSkZVekkxTmlKOS5leUpxZEdraU9pSlhMVjh6YUdvdFgyOUJjbXAyYlc5SmJEQjVWWEpuSWl3aWFYTnpJam9pYUhSMGNITTZMeTloZFhSb0xuSmxaMmx6ZEdWeVpHbHpibVY1TG1kdkxtTnZiU0lzSW1GMVpDSTZJblZ5Ympwa2FYTnVaWGs2YjI1bGFXUTZjSEp2WkNJc0ltbGhkQ0k2TVRjek5qQXhOVGN4T0N3aWJtSm1Jam94TnpNMk1ERTFOekU0TENKbGVIQWlPakUzTXpZeE1ESXhNVGdzSW1Oc2FXVnVkRjlwWkNJNklrVlRVRTR0VDA1RlUwbFVSUzVYUlVJdFVGSlBSQ0lzSW1OaGRDSTZJbWQxWlhOMElpd2liR2xrSWpvaVlXUXhNakl4TkRNdFltRXpOaTAwWWpaaExUaG1OMkl0T1RGa09XRTFZVFF3WmpFeElpd2lhV1JsYm5ScGRIbGZhV1FpT2lJd09URTNabUk1WlMwNVptWmhMVFJsTURndE9HRmhNeTB6TnpFMFlUZGpOV1EwT1RJaUxDSnpkV0lpT2lKN05ESTFOVGRDUlRVdFJVTTFOaTAwUXpFNExUazVNMFl0UkRaR09UVkdOME0zUWpOQmZTSjkubEpkc1dHNkJvZjA1aE1ZeGpIcVh1aVE0YjZOcC1xeG1LclBfQkxZdmR2a3V0Umgyc1AybFZGdGdYNDAzS2VReEh3S2xvNzJKQThGb1RCY1JVM2ZvS0EiLCJyZWZyZXNoX3Rva2VuIjoiZXlKcmFXUWlPaUpuZFdWemRHTnZiblJ5YjJ4c1pYSXRMVEUyTWpBeE9UTTFORFFpTENKaGJHY2lPaUpGVXpJMU5pSjkuZXlKcWRHa2lPaUo0TUdZNU1sbEhWMGc0TkZGQlFtUnZSbVpSVDBkUklpd2ljM1ZpSWpvaWV6UXlOVFUzUWtVMUxVVkROVFl0TkVNeE9DMDVPVE5HTFVRMlJqazFSamRETjBJelFYMGlMQ0pwYzNNaU9pSm9kSFJ3Y3pvdkwyRjFkR2d1Y21WbmFYTjBaWEprYVhOdVpYa3VaMjh1WTI5dElpd2lZWFZrSWpvaWRYSnVPbVJwYzI1bGVUcHZibVZwWkRwd2NtOWtJaXdpYVdGMElqb3hOek0yTURFMU56RTRMQ0p1WW1ZaU9qRTNNell3TVRVM01UZ3NJbVY0Y0NJNk1UYzFNVFUyTnpjeE9Dd2lZMnhwWlc1MFgybGtJam9pUlZOUVRpMVBUa1ZUU1ZSRkxsZEZRaTFRVWs5RUlpd2lZMkYwSWpvaWNtVm1jbVZ6YUNJc0lteHBaQ0k2SW1Ga01USXlNVFF6TFdKaE16WXROR0kyWVMwNFpqZGlMVGt4WkRsaE5XRTBNR1l4TVNJc0ltbGtaVzUwYVhSNVgybGtJam9pTURreE4yWmlPV1V0T1dabVlTMDBaVEE0TFRoaFlUTXRNemN4TkdFM1l6VmtORGt5SW4wLmFSdHlaUXo4SXpzZUZYTDl5M3NvMkZyTzJrMHhJUTA1ZnY5b2ZwZWp6LWdTd3lzMS15c1g4d3ByVU1qaWtJUEVjdlhERW1iWlhET09QM0ExOWhVbjlnIiwic3dpZCI6Ins0MjU1N0JFNS1FQzU2LTRDMTgtOTkzRi1ENkY5NUY3QzdCM0F9IiwidHRsIjo4NjM5OSwicmVmcmVzaF90dGwiOjE1NTUxOTk5LCJoaWdoX3RydXN0X2V4cGlyZXNfaW4iOjE3OTksImluaXRpYWxfZ3JhbnRfaW5fY2hhaW5fdGltZSI6MTczNjAxNTcxODAwMCwiaWF0IjoxNzM2MDE1NzE4MDAwLCJleHAiOjE3MzYxMDIxMTgwMDAsInJlZnJlc2hfZXhwIjoxNzUxNTY3NzE4MDAwLCJoaWdoX3RydXN0X2V4cCI6MTczNjAxNzUxODAwMCwic3NvIjpudWxsLCJhdXRoZW50aWNhdG9yIjpudWxsLCJsb2dpblZhbHVlIjpudWxsLCJjbGlja2JhY2tUeXBlIjpudWxsLCJzZXNzaW9uVHJhbnNmZXJLZXkiOiJwODlGU3NJZDZiNXhabFVlU0d4THcycXB0Wkh0VkxQM1liNGlEYVFtTHJqWGRYRFNTeFJHOGRYM3RwUEpUb2F2aEdyZTMtOXM5WlZZTWtQSVNWVi1tWmQ3QzZJTW9tS3NodnJxRXhCZkFIbDYyR0RBSkRZIiwiY3JlYXRlZCI6IjIwMjUtMDEtMDRUMTg6MzU6MjAuMzI4WiIsImxhc3RDaGVja2VkIjoiMjAyNS0wMS0wNFQxODozNToyMC4zMjhaIiwiZXhwaXJlcyI6IjIwMjUtMDEtMDVUMTg6MzU6MTguMDAwWiIsInJlZnJlc2hfZXhwaXJlcyI6IjIwMjUtMDctMDNUMTg6MzU6MTguMDAwWiJ9^|eyJraWQiOiJndWVzdGNvbnRyb2xsZXItLTE2MjAxOTM1NDQiLCJhbGciOiJFUzI1NiJ9.eyJqdGkiOiJlQlFQRXVfb3haeEdoQnVEQjROMW13IiwiaXNzIjoiaHR0cHM6Ly9hdXRoLnJlZ2lzdGVyZGlzbmV5LmdvLmNvbSIsImF1ZCI6IkVTUE4tT05FU0lURS5XRUItUFJPRCIsInN1YiI6Ins0MjU1N0JFNS1FQzU2LTRDMTgtOTkzRi1ENkY5NUY3QzdCM0F9IiwiaWF0IjoxNzM2MDE1NzE4LCJuYmYiOjE3MzYwMTU3MTgsImV4cCI6MTczNjEwMjExOCwiY2F0IjoiaWR0b2tlbiIsImVtYWlsIjoidGlpa2lpQHByb3Rvbm1haWwuY29tIiwiaWRlbnRpdHlfaWQiOiIwOTE3ZmI5ZS05ZmZhLTRlMDgtOGFhMy0zNzE0YTdjNWQ0OTIifQ.uoI2r1oAOEexhr17t97RyFcb_Nen9qR1kfIjyONE_OzGKlMv0RaExK4zhvW0GMRgySz5-8X58rKyEbA-D5ovfQ; ESPN-ONESITE.WEB-PROD-ac=XBY; ESPN-ONESITE.WEB-PROD.idn=00ae3c1b3d; espn-prev-page=fantasy^%^3Ahockey^%^3Aleague^%^3Aplayerleaders; s_ensNR=1736032521405-Repeat; block.check=false^%^7Cfalse; s_sq=^%^5B^%^5BB^%^5D^%^5D; AMCV_5BFD123F5245AECB0A490D45^%^40AdobeOrg=-50417514^%^7CMCMID^%^7C83798874837265572568689452294298221919^%^7CMCAID^%^7CNONE^%^7CMCOPTOUT-1736039723s^%^7CNONE^%^7CvVersion^%^7C5.5.0^" ^
  -H ^"origin: https://fantasy.espn.com^" ^
  -H ^"pragma: no-cache^" ^
  -H ^"priority: u=1, i^" ^
  -H ^"referer: https://fantasy.espn.com/^" ^
  -H ^"sec-ch-ua: ^\^"Brave^\^";v=^\^"131^\^", ^\^"Chromium^\^";v=^\^"131^\^", ^\^"Not_A Brand^\^";v=^\^"24^\^"^" ^
  -H ^"sec-ch-ua-mobile: ?0^" ^
  -H ^"sec-ch-ua-platform: ^\^"Windows^\^"^" ^
  -H ^"sec-fetch-dest: empty^" ^
  -H ^"sec-fetch-mode: cors^" ^
  -H ^"sec-fetch-site: same-site^" ^
  -H ^"sec-gpc: 1^" ^
  -H ^"user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36^" ^
  -H ^"x-fantasy-filter: ^{^\^"players^\^":^{^\^"filterSlotIds^\^":^{^\^"value^\^":^[0^]^},^\^"filterStatsForCurrentSeasonScoringPeriodId^\^":^{^\^"value^\^":^[1^]^},^\^"sortPercOwned^\^":^{^\^"sortPriority^\^":3,^\^"sortAsc^\^":false^},^\^"limit^\^":50,^\^"offset^\^":0,^\^"sortAppliedStatTotalForScoringPeriodId^\^":^{^\^"sortAsc^\^":false,^\^"sortPriority^\^":1,^\^"value^\^":1^},^\^"filterRanksForScoringPeriodIds^\^":^{^\^"value^\^":^[1^]^},^\^"filterRanksForRankTypes^\^":^{^\^"value^\^":^[^\^"STANDARD^\^"^]^}^}^}^" ^
  -H ^"x-fantasy-platform: kona-PROD-12e764fad9fd0892caaf6ac5e9ec6893895afdb8^" ^
  -H ^"x-fantasy-source: kona^"

## Основные компоненты

### 1. Сервисы
- `ESPNService` - работа с API ESPN для получения статистики игроков
- `ImageService` - создание коллажей с изображениями игроков
- `TelegramService` - отправка сообщений и изображений в Telegram

### 2. Скрипты
- `app_day.py` - основной скрипт для формирования команды дня
- `collect_initial_stats.py` - сбор начальной статистики за сезон

### 3. Данные
Проект использует следующие файлы данных в директории `data/processed/`:
- `player_stats.json` - статистика игроков по неделям
- `season_stats.json` - статистика за весь сезон
- `teams_history.json` - история команд
- `weekly_team_stats.json` - статистика команд по неделям

## Основные функции

### Формирование команды дня
1. Получение статистики игроков за день через ESPN API
2. Проверка уникальности и корректности данных:
   - Пропуск существующих корректных данных
   - Перезапись некорректных или неполных данных
3. Выбор лучших игроков по total points:
   - При равном количестве очков выбор случайный
   - Всегда выбирается лучший доступный игрок из списка для каждой позиции
4. Состав команды:
   - 1 центральный нападающий (C)
   - 1 левый нападающий (LW)
   - 1 правый нападающий (RW)
   - 2 защитника (D)
   - 1 вратарь (G)

### Формирование команды недели
1. Анализ статистики игроков из ежедневных данных
2. Приоритеты при выборе игроков:
   - Первый приоритет: количество попаданий в команду дня
   - Второй приоритет: total points
3. Создание отдельного коллажа:
   - Формат аналогичен команде дня
   - Заголовок "Команда недели"
   - Указание дат периода (с-по)

### Формат коллажа команды дня
- Заголовок "Команда дня" и дата
- Для каждого игрока:
  - Качественное фото в формате PNG с прозрачным фоном
  - Стандартный размер изображения: 130x100 пикселей
  - Позиция игрока
  - Имя и фамилия
  - Total points за игровой день

### Система грейдов игроков
- Грейды сбрасываются каждый матчап (неделя с понедельника по воскресенье)
- Грейды присваиваются только при попадании в команду дня:
  - common (1 попадание)
  - uncommon (2 попадания)
  - rare (3 попадания)
  - epic (4 попадания)
  - legend (5+ попаданий)
- Грейды аккумулируются строго по дате в рамках одной недели
- Учитывается только основная позиция игрока
- Если игрок не попадал в команду дня, грейд не присваивается

## Настройка проекта

### Конфигурация
Проект использует многоуровневую систему конфигурации:

1. Базовый URL:
```
https://lm-api-reads.fantasy.espn.com/apis/v3/games/fhl/seasons/2025/segments/0/leagues/484910394?scoringPeriodId=94&view=kona_player_info
```

2. Конфигурационные файлы:
- `config/settings.py` - основные настройки
- `config/api_config.py` - настройки API
- `config/logging_config.py` - настройки логирования

### Режимы запуска
Скрипт `app_day.py` поддерживает следующие режимы:
```bash
# Стандартный запуск
python scripts/app_day.py

# Запуск за конкретную дату
python scripts/app_day.py --date YYYY-MM-DD

# Запуск с очисткой статистики
python scripts/app_day.py --clean

# Запуск с перезаписью данных за дату
python scripts/app_day.py --date YYYY-MM-DD --force

# Запуск в режиме дополнения данных
python scripts/app_day.py --append
```

### Зависимости
Установите необходимые зависимости:
```bash
pip install -r requirements.txt
```

#### Пример x-fantasy-filter (необходим для получения статистики)
```json
{
  "players": {
    "filterSlotIds": {
      "value": [0,1,2,3,4,6]
    },
    "filterStatsForCurrentSeasonScoringPeriodId": {
      "value": [78]
    },
    "sortPercOwned": {
      "sortPriority": 3,
      "sortAsc": false
    },
    "limit": 50,
    "offset": 0,
    "sortAppliedStatTotalForScoringPeriodId": {
      "sortAsc": false,
      "sortPriority": 1,
      "value": 78
    },
    "filterRanksForScoringPeriodIds": {
      "value": [78]
    },
    "filterRanksForRankTypes": {
      "value": ["STANDARD"]
    }
  }
}
```

### Маппинг позиций игроков
```
1: 'C'   # Center
2: 'LW'  # Left Wing
3: 'RW'  # Right Wing
4: 'D'   # Defense
5: 'G'   # Goalie
```

## Текущие проблемы и их решение

1. Проблемы с аутентификацией ESPN API:
   - Необходимо корректно передавать SWID и S2 токены
   - Требуется механизм обновления токенов
   - Нужна обработка ошибок аутентификации

2. Проблемы с форматированием запросов:
   - Некорректное формирование x-fantasy-filter
   - Отсутствие валидации параметров фильтра
   - Необходимость правильной сортировки результатов

3. SSL сертификаты:
   - Временно отключена проверка SSL
   - Необходимо реализовать корректную обработку сертификатов

## Рекомендации для следующего разработчика

### Первые шаги

1. Начните с исправления проблем в ESPNService:
   - Добавьте механизм повторных попыток при сбоях API
   - Реализуйте корректную обработку ошибок
   - Добавьте валидацию ответов от API

2. Реализуйте кэширование:
   - Кэширование запросов к API
   - Сохранение промежуточных результатов
   - Управление временем жизни кэша

3. Улучшите работу с фильтрами:
   - Создайте класс для построения x-fantasy-filter
   - Добавьте валидацию параметров
   - Реализуйте различные стратегии фильтрации

### Дальнейшие улучшения

1. Тестирование:
   - Добавьте модульные тесты для сервисов
   - Реализуйте интеграционные тесты
   - Добавьте мок-объекты для API

2. Мониторинг:
   - Добавьте метрики производительности
   - Реализуйте отслеживание ошибок
   - Настройте алерты при сбоях

3. Оптимизация:
   - Улучшите механизм сохранения данных
   - Оптимизируйте запросы к API
   - Добавьте параллельную обработку

## Текущие задачи

1. Исправление ESPNService:
   ```python
   def _make_request(self, params: Dict, headers: Dict) -> Optional[Dict]:
       # Добавить:
       # - Механизм повторных попыток
       # - Валидацию ответов
       # - Обработку ошибок SSL
   ```

2. Создание класса для фильтров:
   ```python
   class ESPNFantasyFilter:
       def __init__(self):
           self.filter = {"players": {}}
           
       def add_slot_filter(self, slots: List[int]):
           # Добавление фильтра по позициям
           
       def add_scoring_period_filter(self, period_id: int):
           # Добавление фильтра по периоду
   ```

3. Реализация кэширования:
   ```python
   class ESPNCache:
       def __init__(self, ttl: int = 3600):
           self.cache = {}
           self.ttl = ttl
           
       def get(self, key: str) -> Optional[Dict]:
           # Получение данных из кэша
           
       def set(self, key: str, value: Dict):
           # Сохранение данных в кэш
   ```

## Известные особенности API

1. Фильтры:
   - filterSlotIds: определяет позиции игроков
   - filterStatsForCurrentSeasonScoringPeriodId: период статистики
   - sortPercOwned: сортировка по популярности
   - filterRanksForRankTypes: тип рейтинга

### Важные моменты
1. **Структура данных**:
   - В `data/processed/` хранятся JSON файлы с историей команд и статистикой
   - Каждый файл имеет базовую структуру с ключами `weeks`, `players`, `teams`
   - При работе с файлами всегда проверяйте их существование и создавайте базовую структуру

2. **API ESPN**:
   - API требует аутентификации через `SWID` и `S2` токены
   - Используйте правильный `scoring_period_id` для получения статистики
   - Учитывайте часовой пояс лиги при работе с датами

3. **Обработка изображений**:
   - Изображения игроков кэшируются в `data/cache/player_images/`
   - Используйте системные шрифты для текста на коллажах
   - Проверяйте существование директорий перед сохранением

4. **Telegram**:
   - Бот использует длинные токены формата `123456789:AAA-BBB...`
   - ID чата может быть отрицательным для групповых чатов
   - Добавляйте повторные попытки при отправке сообщений

### Известные особенности
1. Сезон НХЛ 2024-25 начинается 4 октября 2024 года
2. День в системе начинается в 4 утра по времени лиги
3. Грейды игроков обновляются каждый понедельник
4. Команда дня формируется по следующим позициям:
   - 1 центральный нападающий (C)
   - 1 левый нападающий (LW)
   - 1 правый нападающий (RW)
   - 2 защитника (D)
   - 1 вратарь (G)

### Рекомендации по улучшению
1. Добавить тесты для критических компонентов
2. Реализовать механизм восстановления после сбоев
3. Добавить мониторинг производительности
4. Улучшить визуальное оформление коллажей
5. Добавить интерактивные команды в Telegram бота
6. Реализовать сравнение команд между разными неделями
7. Добавить статистику по дивизионам и конференциям

### Отладка
1. Используйте флаг `--no-send` для тестирования без отправки в Telegram
2. Проверяйте логи в директории `logs/`
3. При проблемах с API проверьте:
   - Валидность токенов
   - Правильность часового пояса
   - Корректность ID сезона и лиги

### Безопасность
1. Не коммитьте файл `.env` в репозиторий
2. Регулярно обновляйте токены API
3. Проверяйте права доступа к файлам с данными
4. Используйте безопасные методы хранения конфиденциальных данных 

## Обновления системы

### Реализованные улучшения

1. Добавлен надежный механизм работы с ESPN API:
   - Автоматические повторные попытки при сбоях
   - Настраиваемые таймауты и задержки
   - Валидация ответов от API

2. Улучшена конфигурация:
   - Вынесены все константы в отдельные конфиг-файлы
   - Добавлены типы данных для лучшей поддержки IDE
   - Структурированы настройки API

3. Добавлена базовая валидация данных:
   - Проверка обязательных полей в ответах API
   - Логирование ошибок при сбоях
   - Механизм восстановления после временных проблем

### Следующие шаги

1. Реализовать кэширование:
```python
class StatsCache:
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        
    def get_cached_stats(self, date: datetime) -> Optional[Dict]:
        # TODO: Реализовать получение кэшированных данных
        pass
        
    def cache_stats(self, date: datetime, stats: Dict):
        # TODO: Реализовать сохранение данных в кэш
        pass
```

2. Добавить тесты для StatsService:
```python
def test_stats_service_retry_mechanism():
    # TODO: Протестировать механизм повторных попыток
    pass

def test_stats_service_validation():
    # TODO: Протестировать валидацию данных
    pass
```

### Протестированные компоненты

1. Механизм повторных попыток:
   - Успешно обрабатывает временные сбои API
   - Корректно работает с таймаутами
   - Логирует все попытки и ошибки

2. Валидация данных:
   - Проверяет наличие обязательных полей
   - Отфильтровывает некорректные ответы
   - Обеспечивает целостность данных 