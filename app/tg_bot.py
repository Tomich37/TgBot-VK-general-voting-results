import telebot
from app.set_logs import SetLogs
import configparser
from app.vk_bot import VKBot
import requests, re


class TgBot:
    def __init__(self):
        # Чтение файла конфигурации
        config = configparser.ConfigParser()
        config.read('./config.ini')

        self.logger = SetLogs().logger
        self.tg_token = config.get('tokens', 'tg_token')
        self.vk_token = config.get('tokens', 'vk_token')

        self.vk_bot = VKBot(self.logger, self.vk_token)

        # Инициализация бота
        self.tg_bot = telebot.TeleBot(self.tg_token)    

    def run(self):
        @self.tg_bot.message_handler(commands=['start'])
        def start(message):
            self.tg_bot.send_message(message.chat.id, 'Добрый день, для получения суммарных результатов голосований прошу отправить эксель файл с ссылками на записи с голосованями')

        @self.tg_bot.message_handler(content_types=['document'])
        def handle_document(message):
            user_id = message.from_user.id
            self.tg_bot.send_message(message.chat.id, 'Идет обработка документа, ожидайте ее завершения')
            # Проверяем расширение файла
            if message.document.file_name.endswith('.xlsx'):
                try:
                    # Получаем информацию о загруженном документе
                    file_info = self.tg_bot.get_file(message.document.file_id)
                    file_path = f"https://api.telegram.org/file/bot{self.tg_token}/{file_info.file_path}"

                    # Создаем временный файл для сохранения документа
                    temp_file_path = 'temp.xlsx'

                    # Загружаем документ
                    response = requests.get(file_path)
                    with open(temp_file_path, 'wb') as temp_file:
                        temp_file.write(response.content)

                    # Читаем ссылки из загруженного эксель-файла
                    links = self.vk_bot.read_links_from_excel(temp_file_path)
                    number_of_links = len(links)
                    links = [link for link in links if 'vk.com' in link and 'wall' in link]
                    number_of_good_links = len(links)
                    n_links = 0
                    process_messge = self.tg_bot.send_message(message.chat.id, f'Обработано: {n_links} из {number_of_good_links}')

                    chunk_size = 100
                    link_chunks = [links[i:i+chunk_size] for i in range(0, len(links), chunk_size)]

                    total_results = {}

                    for link_chunk in link_chunks:
                        poll_results = []

                        for link in link_chunk:
                            link_id = re.search(r'wall-(\d+_\d+)', link).group(1)
                            link_id = f'-{link_id}'  # добавляем "-" перед id
                            poll_results.append(link_id)  # Используем append для добавления id
                                
                        poll_results_str = ', '.join(poll_results)
                        results = self.vk_bot.get_poll_results(poll_results_str, self.vk_token)
                        n_links += 100
                        self.tg_bot.edit_message_text(f"Процесс обработки опросов: {n_links}/{number_of_good_links}", chat_id=message.chat.id, message_id=process_messge.message_id)
                        if results:
                            if not total_results:
                                # Если total_results пуст, записываем вопросы и ответы из первого чанка
                                total_results = {result['question']: result['answers'] for result in results}
                            else:
                                # В противном случае обновляем голоса для уже существующих вопросов и ответов
                                for result in results:
                                    question = result['question']
                                    for answer in result['answers']:
                                        for existing_answer in total_results.get(question, []):
                                            if answer['text'] == existing_answer['text']:
                                                existing_answer['votes'] += answer['votes']

                    total_results = [{'question': question, 'answers': answers} for question, answers in total_results.items()]

                    formatted_results = {}

                    for result in total_results:
                        question = result['question']
                        answers = result['answers']
                        if question not in formatted_results:
                            formatted_results[question] = {'answers': []}
                        formatted_results[question]['answers'].extend(answers)

                    for question, data in formatted_results.items():
                        votes = [answer['votes'] for answer in data['answers']]
                        total_votes = sum(votes)
                        data['total_votes'] = total_votes

                    # Создаем список для хранения результатов
                    combined_results = []

                    # Создаем список для хранения результатов
                    for result in total_results:
                        question = result['question']
                        answers = result['answers']
                        for i, answer in enumerate(answers):
                            existing_answer = next((item for item in combined_results if item['index'] == i), None)
                            if existing_answer:
                                # Если ответ уже существует, суммируем голоса
                                existing_answer['votes'] += answer['votes']
                            else:
                                # Если ответ новый, добавляем его в combined_results
                                combined_results.append({'index': i, 'text': answer['text'], 'votes': answer['votes']})

                    # Форматируем результаты для вывода в телеграм
                    formatted_message = ''
                    formatted_message += f'Вопрос:\n{question}\n\nОтветы:\n'

                    for data in combined_results:                    
                        formatted_message += f'{data["text"]} | {data["votes"]} | {round((100 * data["votes"])/total_votes, 2)}%\n'

                    formatted_message += f'\n\nВсего голосов: {total_votes}'

                    # Отправляем результаты в Telegram
                    self.tg_bot.reply_to(message, f'Общие результаты:\nПолучено ссылок: {number_of_links}\nРабочие ссылки: {number_of_good_links}\n\n{formatted_message}')
                except Exception as e:
                    print(f"An error occurred in tg_bot/handle_document: {e}")
                    self.logger.exception(f"An error occurred in tg_bot/handle_document: {e}")
                    self.tg_bot.send_message(user_id, "Произошла ошибка при загрузке документа. Пожалуйста, повторите попытку позже.")
            else:
                self.tg_bot.send_message(message.chat.id, 'Пожалуйста, загрузите файл в формате Excel (xlsx)')

        # Запуск бота
        self.tg_bot.polling()