from app.tg_bot import TgBot


def main() -> None:
    bot: TgBot = TgBot()
    bot.run()


if __name__ == '__main__':
    main()
