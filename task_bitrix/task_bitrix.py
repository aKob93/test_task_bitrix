import requests
import datetime
from fast_bitrix24 import Bitrix
import schedule

DATE_VERIFICATION_SITE = 'https://isdayoff.ru/'
DAYS_BEFORE_HOLIDAY = 3
WEBHOOK_BITRIX = 'https://b24-ih5nxs.bitrix24.ru/rest/1/lizn9w1w3ey3we9f/'

# получение даты через два дня, чтобы получить предпраздничный день
def get_date():
    date = f'{datetime.datetime.today() + datetime.timedelta(days=DAYS_BEFORE_HOLIDAY - 1)}'
    return date

# проверка даты на предпраздничный ден
def check_date():
    date = get_date()
    formatted_date = date[:11].replace('-', '')
    date_information = requests.get(f'{DATE_VERIFICATION_SITE}{formatted_date}?pre=1')
    try:
        if date_information.text == '2':# предпраздничный день(сокращенный)
            return True
        else:
            return False
    except Exception as exc:
        print(f'Не удалось выполнить проверку дня {exc}')

# создание задачи в битриксе
def create_task():
    date = get_date()
    formatted_date = date[:11]
    bx24 = Bitrix(WEBHOOK_BITRIX)
    task = [
        {
            'fields': {
                'TITLE': f'Предпраздничные дни c {formatted_date}',
                'DESCRIPTION': f'Осталось {DAYS_BEFORE_HOLIDAY} дня до праздничных выходных',
                'RESPONSIBLE_ID': '1',
                'START_DATE_PLAN': f'{formatted_date}'
            }
        }
    ]
    bx24.call('tasks.task.add', task)


def run():
    check = check_date()
    if check:
        create_task()

# постановка расписания - каждый день в 02:00 проверяется нужный день
def main():
    schedule.every().day.at('02:00').do(run)
    while True:
        schedule.run_pending()


if __name__ == '__main__':
    main()
