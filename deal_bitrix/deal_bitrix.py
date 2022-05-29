import json
from fast_bitrix24 import Bitrix
import re

WEBHOOK_BITRIX = 'https://b24-ih5nxs.bitrix24.ru/rest/1/lizn9w1w3ey3we9f/'
bx24 = Bitrix(WEBHOOK_BITRIX)


# открытие json файла
def open_file():
    with open('data_file.json') as file:
        data = json.load(file)
        return data


# проверка создан ли контакт по номеру телефона и адресу
def check_contact(data):
    phone_number = data['client']['phone']
    address = data['client']['adress']

    contact = bx24.get_all('crm.contact.list',
                           {'filter': {"PHONE": f"{phone_number}", "ADDRESS": f'{address}'}, }
                           )
    return contact  # возвращает список, пустой если контакта нет(False), с данными, если контакт есть(True)


# создание контакта
def create_contact(data):
    contact = [
        {
            'fields': {
                "NAME": f"{data['client']['name']}",
                "LAST_NAME": f"{data['client']['surname']}",
                "TYPE_ID": "CLIENT",
                "PHONE": [{"VALUE": f"{data['client']['phone']}", "VALUE_TYPE": "WORK"}],
                "ADDRESS": f"{data['client']['adress']}",

            }
        }
    ]
    bx24.call('crm.contact.add', contact)


# создание сделки
def create_deal(data):
    deal = [
        {
            'fields': {
                "TITLE": f"{data['title']}",
                "COMMENTS": f"{data['delivery_adress']}",
                "CLOSEDATE": f"{data['delivery_date'][:10]}T{data['delivery_date'][11:]}",
                "ADDITIONAL_INFO": f"{data['delivery_code']}",
            }
        }
    ]
    bx24.call('crm.deal.add', deal)
    # проверка сделки по "delivery_code"
    info_deal = bx24.get_all('crm.deal.list',
                             {'filter': {"ADDITIONAL_INFO": f"{data['delivery_code']}"}})
    products = str(data['products'])
    pattern = "[](')[]"
    products = re.sub(pattern, "", products)
    bx24.call('crm.deal.productrows.set',
              [{'id': info_deal[0]['ID'], 'rows': [{'PRODUCT_NAME': f'{products}'}]}])


# связь контакта и сделки
def connect_contact_and_deal(data):
    # проверка сделки по "delivery_code"
    info_deal = bx24.get_all('crm.deal.list',
                             {'filter': {"ADDITIONAL_INFO": f"{data['delivery_code']}"}})
    contact = check_contact(data)
    contact_id = [
        {
            'id': info_deal[0]['ID'],
            'fields': {
                "CONTACT_ID": f"{contact[0]['ID']}"
            }
        }
    ]
    bx24.call('crm.deal.contact.add', contact_id)


# проверка создана ли сделка
def check_deal(data):
    info_deal = bx24.get_all('crm.deal.list',
                             {'filter': {"COMMENTS": f"{data['delivery_adress']}",
                                         "CLOSEDATE": f"{data['delivery_date'][:10]}T{data['delivery_date'][11:]}",
                                         }})

    products_deal = bx24.get_all('crm.deal.productrows.get', {'id': info_deal[0]['ID']})
    if info_deal:
        products_deal = products_deal[0]['PRODUCT_NAME']
        pattern = "[](')[]"
        products_application = re.sub(pattern, '', str(data['products']))

        if products_deal == products_application:
            return True
        else:
            return False
    else:
        return False


# обновление сделки
def update_deal(data):
    info_deal = bx24.get_all('crm.deal.list',
                             {'filter': {"ADDITIONAL_INFO": f"#232nkF3fAdn"}})

    bx24.call('crm.deal.update', {'id': info_deal[0]["ID"],
                                  'fields': {
                                      "TITLE": f"{data['title']}",
                                      "COMMENTS": f"{data['delivery_adress']}",
                                      "CLOSEDATE": f"{data['delivery_date'][:10]}T{data['delivery_date'][11:]}",
                                      "ADDITIONAL_INFO": f"{data['delivery_code']}",
                                            }
                                  }
              )
    products = str(data['products'])
    pattern = "[](')[]"
    products = re.sub(pattern, "", products)
    bx24.call('crm.deal.productrows.set',
              [{'id': info_deal[0]['ID'], 'rows': [{'PRODUCT_NAME': f'{products}'}]}])


def main():
    try:
        data_from_json = open_file()
        contact = check_contact(data_from_json)
        # Контакта нет(check_contact()) в Bitrix24 (далее b24) → создаем и контакт и сделку и связываем их между собой
        if not contact:
            create_contact(data_from_json)
            create_deal(data_from_json)
            connect_contact_and_deal(data_from_json)
        # Контакт есть в b24 → Проверяем есть ли уже такая заявка по delivery_code
        else:
            info_deal = check_deal(data_from_json)
            # Заявки нет в b24 → Создаем заявку и связываем ее с контактом
            if  not info_deal:
                create_deal(data_from_json)
                connect_contact_and_deal(data_from_json)
            # Заявка есть в b24 → Сравниваем заявку из b24 с ключевыми полями (delivery_adress, delivery_date, products)
            # из пришедшей заявки
            else:
                # Поля совпадают → Ничего не делаем
                if check_deal(data_from_json):
                    pass
                else:
                    update_deal(data_from_json)
    except Exception as exc:
        print(f'Не удалось обработать заявку - {exc}')


if __name__ == '__main__':
    main()
