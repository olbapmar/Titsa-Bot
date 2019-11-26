# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import ConfigParser
from api_handler import ApiHandler
from db_handler import DbHandler
from telegram.ext import CommandHandler, MessageHandler, Updater, Filters, CallbackQueryHandler, ConversationHandler
import telegram as telegram
import logging
import sys
import re

reload(sys)
sys.setdefaultencoding('utf-8')

apiHandler = None

class TitsaBot:
    CUSTOM_OR_DEFAULT, INSERT_CUSTOM, TRANVIA, BROADCAST_TEXT = range(4)
    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read('bot_config.ini')
        
        bot_token = config.get("TELEGRAM", "token")

        titsa_idApp = config.get("TITSA", "idApp")

        self.adminId = config.get("ADMIN", "chatId")

        self.apiHandler = ApiHandler(titsa_idApp)

        self.dbHandler = DbHandler()

        updater = Updater(token=bot_token)
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


        b1 = telegram.KeyboardButton("⭐ Consultar favorito ⭐")
        b2 = telegram.KeyboardButton("✖️ Borrar favorito ✖️")
        b3 = telegram.KeyboardButton("🚊 Tranvia de Tenerife 🚊")
        self.keyboard = telegram.ReplyKeyboardMarkup([[b3], [b1], [b2]], resize_keyboard=True)

        h1 = MessageHandler(Filters.regex(r"^.+Consultar favorito.+$"), self.favKeyBoard)
        h2 = MessageHandler(Filters.regex(u"^\U0001F68F.+(\d{4})"), self.replyToFav)
        h3 = MessageHandler(Filters.regex(r"^.+Borrar favorito.+$"), self.favKeyBoard)
        h4 = MessageHandler(Filters.regex(u"^\u2716.+(\d{4})"), self.eraseFav)

        updater.dispatcher.add_handler(CommandHandler("start", self.start))
        updater.dispatcher.add_handler(MessageHandler(Filters.regex(r"^\d{4}$"), self.responder_a_codigo))
        updater.dispatcher.add_handler(h1)
        updater.dispatcher.add_handler(h2)
        updater.dispatcher.add_handler(h3)
        updater.dispatcher.add_handler(h4)

        updater.dispatcher.add_handler(ConversationHandler(
            entry_points=[MessageHandler(Filters.regex(r"^.+Tranvia de Tenerife.+$"), self.listStops),],
            states = {
                TitsaBot.TRANVIA: [MessageHandler(Filters.all, self.queryTram)]
            },
            fallbacks=[]
        ))

        updater.dispatcher.add_handler(ConversationHandler(
            entry_points=[CommandHandler("broadcast", self.newBroadcast),],
            states = {
                TitsaBot.BROADCAST_TEXT: [MessageHandler(Filters.all, self.broadcast)]
            },
            fallbacks=[]
        ))

        updater.dispatcher.add_handler(ConversationHandler(
            entry_points=[CommandHandler("addFav", self.addFavCommand, pass_args=True, pass_user_data=True),
                         CallbackQueryHandler(self.addFavQuery, pattern=r"^\d{4}$", pass_user_data=True)],
            states = {
                TitsaBot.CUSTOM_OR_DEFAULT: [CallbackQueryHandler(self.setFavNameOption, pass_user_data=True)],
                TitsaBot.INSERT_CUSTOM: [MessageHandler(Filters.text, self.customName, pass_user_data=True)]
            },
            fallbacks= [h1,h2,h3,h4]
        ))

        updater.dispatcher.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self.reloadStationQuery, pattern=r"^Repetir \d{4}$", pass_user_data=True)],
            states = {
                TitsaBot.CUSTOM_OR_DEFAULT: [CallbackQueryHandler(self.reloadStationQuery, pass_user_data=True)]
            },
            fallbacks= [h1,h2,h3,h4]
        ))

        updater.start_polling()
        updater.idle()
        self.dbHandler.save()


    def build_text(self, status, bus=True):
        if status is not None:
            text = "🚏 *" +  status.name + "* 🚏\n\n"
            sorted_lines = sorted(status.minutes.items(), key=lambda line: int(line[1][0]["minutes"]))
            print(sorted_lines)
            for linea, data in sorted_lines:
                for entry in data:
                    emoji = "🚊*"if not bus else "🚍*" 
                    text += emoji + linea + "* (" + entry["dest"] + \
                            "): "+ entry["minutes"] + " minutos \n"
            
            return text, 1
        else:
            text = "⚠ Parada no encontrada o sin pasos registrados ⚠"
            return text, 0

    def start(self, bot,update):
        bot.send_message(chat_id=update.message.chat_id, text="Hola! Gracias por usarme! \nEnvíame el código de una parada :)", reply_markup=self.keyboard)

    def addFavCommand(self, bot,update, args, user_data):
        return self.newFavMethod(update.message.from_user.id, args[0], bot, update.message.chat.id, user_data)

    def addFavQuery(self, bot,update, user_data):
        return self.newFavMethod(update.callback_query.from_user.id, update.callback_query.data, bot, update.callback_query.message.chat.id, user_data)

    def reloadStationQuery(self, bot, update, user_data):
        codeText = update.callback_query.data.replace("Repetir ", "")
        self.stationQuery(bot, update.callback_query.message.chat_id, update.callback_query.from_user.id, codeText)

    def newFavMethod(self, user, station, bot, chat, user_data):
        if self.dbHandler.check_duplicate(user, station):
            bot.send_message(chat_id=chat, text="Ya está en favoritos", reply_markup=None)
            return -1
        else:
            logging.info(msg="New fav required user:%s id:%s" %(user, station))
            stationName = self.apiHandler.station_name(station)
            text = "Nombre: " + stationName + "\n¿Quiere usar otro?"
            b1 = telegram.InlineKeyboardButton(text="Sí", callback_data="si")
            b2 = telegram.InlineKeyboardButton(text="No", callback_data="no")
            b3 = telegram.InlineKeyboardButton(text="❌Cancelar", callback_data="cancel")
            bot.send_message(chat_id=chat, text=text, reply_markup=telegram.InlineKeyboardMarkup([[b1,b2,b3]]))
            user_data["currentFavStationId"] = station
            user_data["currentFavStationName"] = stationName
            return TitsaBot.CUSTOM_OR_DEFAULT

    def responder_a_codigo(self, bot,update):
        self.stationQuery(bot, update.message.chat_id, update.message.from_user.id, update.message.text)

    def stationQuery(self, bot, chat_id, user_id, text):
        if not self.dbHandler.check_duplicate_user(chat_id):
            self.dbHandler.addUser(chat_id)
        logging.info(msg="Message %s" %(text))
        if text.isdigit() and len(text) == 4:
            texto = self.build_text(self.apiHandler.new_request(text), True)[0]
            button = telegram.InlineKeyboardButton(text="⭐ Añadir a favoritos ⭐", callback_data=text)
            buttonReload = telegram.InlineKeyboardButton(text="🔃 Repetir consulta 🔃", callback_data="Repetir "+text)
            if not self.dbHandler.check_duplicate(user_id, text):
                keyboard = telegram.InlineKeyboardMarkup([[button],[buttonReload]])
            else:
                keyboard = telegram.InlineKeyboardMarkup([[buttonReload]])
            bot.send_message(chat_id=chat_id, text=texto,parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=keyboard)
        else:
            bot.send_message(chat_id=chat_id, text="Código inválido")

        bot.send_message(chat_id=chat_id, text="Escribe el número de parada", reply_markup=self.keyboard)

    def setFavNameOption(self, bot, update, user_data):
        logging.info(msg="Answer for the fav question: user:%s reply:%s" %(update.callback_query.from_user.id, update.callback_query.data))
        if update.callback_query.data == "no":
            self.dbHandler.addUserFav(update.callback_query.from_user.id,
                                    user_data["currentFavStationId"],
                                    user_data["currentFavStationName"])
            text = "*Favorito añadido*\n" + user_data["currentFavStationName"] + "(" + user_data["currentFavStationId"] + ")"
            bot.edit_message_text(text, update.callback_query.message.chat.id, update.callback_query.message.message_id, reply_markup=None, parse_mode=telegram.ParseMode.MARKDOWN)
            bot.send_message(chat_id=update.callback_query.message.chat.id, text="Escribe el número de parada", reply_markup=self.keyboard)
            return -1
        elif update.callback_query.data == "si":
            bot.edit_message_text("¿Qué nombre?", update.callback_query.message.chat.id, update.callback_query.message.message_id, reply_markup=None)
            return TitsaBot.INSERT_CUSTOM
        else:
            bot.delete_message(update.callback_query.message.chat.id, update.callback_query.message.message_id, None)
            user_data.pop("currentFavStationId", None)
            user_data.pop("currentFavStationName", None)
            bot.send_message(chat_id=update.callback_query.message.chat.id, text="Escribe el número de parada", reply_markup=self.keyboard)
            return -1

    def customName(self, bot, update, user_data):
        logging.info(msg="Custom name: user:%s reply:%s" %(update.message.from_user.id, update.message.text))
        self.dbHandler.addUserFav(update.message.from_user.id,
                                    user_data["currentFavStationId"],
                                    update.message.text)
        text = "*Favorito añadido*\n" + update.message.text + "(" + user_data["currentFavStationId"] + ")"
        bot.send_message(update.message.chat.id, text=text, reply_markup=self.keyboard, parse_mode=telegram.ParseMode.MARKDOWN)
        return -1

    def listStops(self, bot, update):
        if not self.dbHandler.check_duplicate_user(update.message.chat_id):
            self.dbHandler.addUser(update.message.chat_id)
        logging.info(msg="Listing tram stations")
        stations = self.apiHandler.tranvia_stations()
        if stations is not None and len(stations) > 0:
            buttons = []
            for station in stations.iteritems():
                buttons.append([telegram.KeyboardButton(u"🚋" + station[0] + " (" + station[1] + ")")])
            bot.send_message(update.message.chat.id, text="Elige estación", reply_markup=telegram.ReplyKeyboardMarkup(buttons), resize_keyboard=True)
            return TitsaBot.TRANVIA
        return -1 

    def queryTram(self, bot, update):
        p = re.compile(u"^\U0001F68B.+(\w{3})")
        stop = p.search(update.message.text).group(1)
        status = self.apiHandler.tranvia_request(stop)
        texto = self.build_text(status, False)[0]
        bot.send_message(chat_id=update.message.chat_id, text=texto,parse_mode=telegram.ParseMode.MARKDOWN,
                                                 reply_markup=self.keyboard)
        return -1

    def favKeyBoard(self, bot, update):
        logging.info(msg="Fav request from user %s" %(update.message.from_user.id))

        stations = self.dbHandler.getUserFavs(update.message.from_user.id)
        if len(stations) > 0:
            buttons = []
            emoji = u"🚏" if not "Borrar" in update.message.text else u"✖️"
            for station in stations:
                buttons.append([telegram.KeyboardButton(emoji + station[1] + " (" + station[0] + ")")])
            bot.send_message(update.message.chat.id, text="Elige estación", reply_markup=telegram.ReplyKeyboardMarkup(buttons), resize_keyboard=True)
        else:
            bot.send_message(update.message.chat.id, text="No tienes favoritos", reply_markup=self.keyboard, resize_keyboard=True)

    def replyToFav(self, bot, update):
        p = re.compile(u"^\U0001F68F.+(\d{4})")
        code = p.search(update.message.text).group(1)
        update.message.text = code
        self.responder_a_codigo(bot, update)

    def eraseFav(self, bot, update):
        p = re.compile(u"^\u2716.+(\d{4})")
        code = p.search(update.message.text).group(1)
        self.dbHandler.deleteUserFav(update.message.from_user.id, code)
        bot.send_message(update.message.chat.id, text="Favorito eliminado", reply_markup=self.keyboard, resize_keyboard=True)

    def broadcast(self, bot, update):
        logging.info(msg="Broadcasting message %s")
        if (update.message.chat.id == int(self.adminId)):
            for user in self.dbHandler.getAllUsers():
                logging.info(msg="Broadcasted to %s" %(user))
                bot.send_message(str(user), text=update.message.text, reply_markup=self.keyboard, resize_keyboard=True)

        return -1 

    def newBroadcast(self, bot, update):
        return TitsaBot.BROADCAST_TEXT
                

def main():
    botTitsa = TitsaBot()

if __name__ == "__main__":
    main()
