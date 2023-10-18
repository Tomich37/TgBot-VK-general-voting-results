import requests, json
from openpyxl import load_workbook

class VKBot:
    def __init__(self, logger, vk_token):
        self.logger = logger
        self.vk_token = vk_token

    # Функция для получения результатов голосования по ссылке
    def get_poll_results(self, poll_results_str, vk_token):
        try:
            url = 'https://api.vk.com/method/wall.getById'
            params = {
                'posts': poll_results_str,
                'access_token': vk_token,
                'v': 5.221
            }
            response = requests.get(url, params=params)
            json_response = response.json()
            # json_data = json.dumps(json_response, separators=(',', ':'), ensure_ascii=False)
            # print(json_data)
            results = self.extract_poll_attachments(json_response) 
            return results
        except Exception as e:
            print(f"An error occurred in vk_bot/get_poll_results: {e}")
            self.logger.exception(f"An error occurred in vk_bot/get_poll_results: {e}")

    # Функция для чтения ссылок из Excel файла
    def read_links_from_excel(self, file_path):
        try:
            wb = load_workbook(filename=file_path)
            sheet = wb.active
            links = [cell.value for cell in sheet['A'] if cell.value is not None]
            # print(f'read_links_from_excel: {links}')
            return links
        except Exception as e:
            print(f"An error occurred in vk_bot/read_links_from_excel: {e}")
            self.logger.exception(f"An error occurred in vk_bot/read_links_from_excel: {e}")
        
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

                        existing_question = next((item for item in poll_attachments if item['question'] == question), None)
                        if existing_question:
                            # Если вопрос уже существует, суммируем голоса в ответах
                            for i, answer in enumerate(answers):
                                existing_question['answers'][i]['votes'] += answer['votes']
                        else:
                            # Если вопрос новый, добавляем его в poll_attachments
                            answers_data = [{'text': answer['text'], 'votes': answer['votes']} for answer in answers]
                            poll_attachments.append({'question': question, 'answers': answers_data})            
                            
            return poll_attachments
        except Exception as e:
            print(f"An error occurred in vk_bot/extract_poll_attachments: {e}")
            self.logger.exception(f"An error occurred in vk_bot/extract_poll_attachments: {e}")