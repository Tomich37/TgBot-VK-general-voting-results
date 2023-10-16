import telebot
from app.set_logs import SetLogs
import configparser
from app.vk_bot import VKBot


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


        # Обработчик команды /get_results
        @self.tg_bot.message_handler(commands=['get_results'])
        def get_results(message):
            links = self.read_links_from_excel('your_excel_file.xlsx')
            total_results = []

            for link in links:
                poll_results = self.get_poll_results(link, self.vk_token)
                # Обработка результатов голосования, например, суммирование
                # Вам нужно подставить свою логику обработки результатов
                
                total_results.append(poll_results)

            # Отправляем результаты в Telegram
            self.tg_bot.reply_to(message, f'Total results: {total_results}')

        # Запуск бота
        self.tg_bot.polling()