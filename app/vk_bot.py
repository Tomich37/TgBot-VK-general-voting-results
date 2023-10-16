import requests, re
from openpyxl import load_workbook

class VKBot:
    def __init__(self, logger, vk_token):
        self.logger = logger
        self.vk_token = vk_token

    # Функция для получения результатов голосования по ссылке
    def get_poll_results(self, poll_url, vk_token):
        try:
            post_id = self.get_post_id(poll_url)
            owner_id, post_id = post_id.split('_')
            url = 'https://api.vk.com/method/wall.getById'
            params = {
                'posts': f'-{owner_id}_{post_id}',
                'access_token': vk_token,
                'v': 5.221
            }
            response = requests.get(url, params=params)
            post_results = response.json()
            self.extract_poll_attachments(post_results) 
        except Exception as e:
            print(f"An error occurred in vk_bot/get_poll_results: {e}")
            self.logger.exception(f"An error occurred in vk_bot/get_poll_results: {e}")

    # Функция для чтения ссылок из Excel файла
    def read_links_from_excel(self, file_path):
        try:
            wb = load_workbook(filename=file_path)
            sheet = wb.active
            links = [cell.value for cell in sheet['A'] if cell.value is not None]
            print(f'read_links_from_excel: {links}')
            return links
        except Exception as e:
            print(f"An error occurred in vk_bot/read_links_from_excel: {e}")
            self.logger.exception(f"An error occurred in vk_bot/read_links_from_excel: {e}")
        
    def get_post_id(self, url):
        match = re.search(r'wall-(\d+_\d+)', url)
        if match:
            return match.group(1)
        else:
            return None
        
    def extract_poll_attachments(self, json_response):
        try:
            poll_attachments = []

            items = json_response.get('response', {}).get('items', [])
            for item in items:
                attachments = item.get('attachments', [])
                for attachment in attachments:
                    if 'poll' in attachment:
                        poll = attachment.get('poll', {})
                        question = poll.get('question', '')
                        answers = poll.get('answers', [])

                        poll_attachments.append({'question': question, 'answers': answers})
            
            print(poll_attachments)

        except Exception as e:
            print(f"An error occurred in vk_bot/extract_poll_attachments: {e}")
            self.logger.exception(f"An error occurred in vk_bot/extract_poll_attachments: {e}")