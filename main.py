import asyncio
from tortoise import Tortoise
from aiohttp_requests import requests
from bs4 import BeautifulSoup
from stock_checker.models import Stock
from stock_checker.db import init_db

async def get_html(url):
    r = await requests.get(url)
    text = await r.text()
    return text


def get_total_pages(html):
    soup = BeautifulSoup(html, 'html.parser')
    total_pages = soup.find('div', class_='col').find_all('li', class_='pagination-item')[-2].text
    # print(total_pages)
    return int(total_pages)


def get_page_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    ads = soup.find('div', class_='mb-4 catalog-section').find_all('div', class_='product-item-small-card')
    # print(len(ads))
    stock_row_data_list = []

    for ad in ads:
        try:
            title = ad.find('div', class_='card-title').text.strip()
            # print(title)
        except:
            title = ''

        try:
            if ad.find('div', class_='card-price').find('small', class_='small').text is not None:
                in_stock = ad.find('div', class_='card-price').find('small', class_='small').text.split('\ ')[1]
                # print(in_stock)
            else:
                in_stock = ''
        except:
            in_stock = ''

        try:
            url = 'https://sigil.me' + ad.find('div', class_='card-title').find('a').get('href')
            # print(url)
        except:
            url = ''

        row_data = {'title': title,
                'in_stock': in_stock,
                'url': url}

        stock_row_data_list.append(row_data)
    return stock_row_data_list

#сохранение в пустую бд
async def save_stock(list_of_raw_stocks):
    await Tortoise.init(
        db_url='postgres://admin:admin@localhost:5432/tammytanuka',
        modules={'models': ['models']}
    )
    stocks = [Stock(
        title=stock['title'],
        in_stock=False if stock['in_stock'] else True,
        url=stock['url']) for stock in list_of_raw_stocks]
    await Stock.bulk_create(stocks)
    Stock.bulk_create([

    ])
    #stocks = await Stock.all()
    print("Наличие пустой БД")
    #print(stocks)

#находит новые товары, которых нет в БД
async def update_stock(list_of_raw_stocks):
    stocks = {Stock(
        title=stock['title'],
        in_stock=False if stock['in_stock'] else True,
        url=stock['url']) for stock in list_of_raw_stocks}
    stocks_from_db = {stock for stock in await Stock.all()}
    new_stocks = stocks - stocks_from_db
    products_removed_from_shop = stocks_from_db - stocks
    print("Новые товары")
    print(new_stocks)

    print("Удаленные из магазина товары")
    print(products_removed_from_shop)


async def main():
    await init_db()
    url = 'https://sigil.me/collection/all'
    page_part = '?PAGEN_1='

    full_row_data_list = []
    total_pages = get_total_pages(await get_html(url))

    for i in range(1, total_pages + 1):
        url_gen = url + page_part + str(i)
        stock_row_data_list = get_page_data(await get_html(url_gen))
        # print(full_row_data_list)
        full_row_data_list += stock_row_data_list
    # print(full_row_data_list)

    # сохранение в пустую БД
    # await save_stock(full_row_data_list)
    #обновление БД
    await update_stock(full_row_data_list)


if __name__ == '__main__':
    asyncio.run(main())
   # asyncio.run(update_stock())
