import requests
from openpyxl import load_workbook

class VKBot:
    def __init__(self, logger, vk_token):
        self.logger = logger
        self.vk_token = vk_token

    # Функция для получения результатов голосования по ссылке
    def get_poll_results(self, poll_url, vk_token):
        poll_id = poll_url.split('/')[-1]
        url = 'https://api.vk.com/method/polls.getById'
        params = {
            'owner_id': -1,
            'poll_id': poll_id,
            'access_token': vk_token,
            'v': 5.221
        }
        response = requests.get(url, params=params)
        poll_results = response.json()
        return poll_results

    # Функция для чтения ссылок из Excel файла
    def read_links_from_excel(self, file_path):
        wb = load_workbook(filename=file_path)
        sheet = wb.active
        links = [cell.value for cell in sheet['A'] if cell.value is not None]
        return links
    