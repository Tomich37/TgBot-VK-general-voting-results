import telebot
from app.set_logs import SetLogs
import configparser
from app.vk_bot import VKBot
import requests


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
                total_results = []

                for link in links:
                    poll_results = self.vk_bot.get_poll_results(link, self.vk_token)
                    # Обработка результатов голосования, например, суммирование
                    # Вам нужно подставить свою логику обработки результатов

                    total_results.append(poll_results)

                # Отправляем результаты в Telegram
                self.tg_bot.reply_to(message, f'Общие результаты: {total_results}')
            except Exception as e:
                print(f"An error occurred in tg_bot/handle_document: {e}")
                self.logger.exception(f"An error occurred in tg_bot/handle_document: {e}")
                self.tg_bot.send_message(user_id, "Произошла ошибка при загрузке документа. Пожалуйста, повторите попытку позже.")

        # Запуск бота
        self.tg_bot.polling()