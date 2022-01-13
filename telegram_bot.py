# From python
import os
from urllib import parse, request
import re
import random

# Dotenv
from dotenv import load_dotenv

# Telegram
from telegram.ext.updater import Updater  # Contiene la el token de la API creado por BotFather
from telegram.update import Update  #  Se llama cada vez que el bot recibe un mensaje o comando y enviará al usuario un mensaje.
from telegram.ext.callbackcontext import CallbackContext  # Trabaja internamente, no la usamos directamente
from telegram.ext.commandhandler import CommandHandler  # Maneja los comandos del usuario
from telegram.ext.messagehandler import MessageHandler  # Controla los mensajes que envia el usuario
from telegram.ext.filters import Filters  # Esto filtrará el texto normal, comandos, imágenes, etc. de un mensaje enviado.

# Pytube
from pytube import YouTube, Playlist

load_dotenv()

class TelegramBot():

    def __init__(self):
        self.updater = Updater(os.getenv('TOKEN'),use_context=True)
        self.PATH = f'{os.getcwd()}/downloads'  # Path del archivo
        
    # Esta funcion se ejecuta cuando el usuario hace click en "iniciar" desde Telegram, o con /start
    def start(self,update:Update,contetx:CallbackContext):
        update.message.reply_text('¡Hola soy el Michi! Yo te voy a ayudar a escuchar la cancion que vos quieras. Para mas ayuda escribi "/help"')

    # Esta funcion devuelve un mensaje de ayuda, con informacion sobre el uso del bot y sus comandos. Inicia con /help
    def help(self,update:Update,context:CallbackContext):
        update.message.reply_text('Escribi "/buscar + el nombre de la cancion" y te voy a enviar la cancion por el chat!')
        update.message.reply_text('Si queres obtener una cancion/audio especifico, escribi "/link + un link de youtube" y listo!')
        update.message.reply_text('Si te intereza descargar una lista de reproduccion, pone /lista + el link de la lista de youtube!')
        update.message.reply_text('Los temas/audios/videos los obtengo desde youtube, y los convierto a formato mp3 para enviarlos por este chat!')
        update.message.reply_text('Tene en cuenta que telegram tiene un limite de 50mb para enviar, si descargas algo muy pesado no lo voy a poder mandar!.')

    # Esta funcion se ejecuta cuando se ingresa un comando no valido / que no existe.
    def unknown(self,update:Update,context:CallbackContext):
        update.message.reply_text("Perdona, pero '%s' no es un comando valido." % update.message.text)

    # Crea url de busqueda en base a lo que escribe el usuario
    def get_url(self,string):
        search = string.replace('/buscar','')
        url = None
        if len(string) <= 8:
            return url
        query_string = parse.urlencode({"search_query": search})
        html_content = request.urlopen("http://www.youtube.com/results?" + query_string)
        search_results = re.findall( r"watch\?v=(\S{11})", html_content.read().decode())
        url = "https://www.youtube.com/watch?v=" + search_results[0]  # url de respuesta
        return url
    
    # Verifica que el url sea correcto
    def verification_url(self,url,update,context):

        if url == None or len(url) < 10:
            update.message.reply_text('Por favor escribi un nombre para buscar!')
            return False
        else:
            update.message.reply_text(self.send_ramdom_message())
            return True
    
    # Envia un mensaje aleatorio al buscar una cancion
    def send_ramdom_message(self):
        message_1 = 'Estoy buscando tu cancion!'
        message_2 = 'Buena eleccion!, ya la estoy buscando'
        message_3 = '¿Eso queres escuchar? mmm bueno, si a vos te gusta.., ya la busco!'
        message_4 = '¡Ay, me encanta esa cancion!'
        message_5 = 'Uh, justo estaba comiendo Whiskas, espera un segundo'
        message_6 = 'Fua que mal gusto tenes.. quise decir meow'
        messages = [message_1,message_2,message_3,message_4,message_5,message_6]
        return random.choice(messages)

    # Elimina los caracteres especiales y deja solo letras y numeros
    def replace_characters(self,old_title):
        new_title = ''.join(char for char in old_title if char.isalnum())  # Crea una nueva cadena solo con caracteres alfanumericos
        new_title = f'{new_title}.mp3'  # Agrega la extencion del archivo
        new_title = new_title.lower()
        return new_title

    # Renombra el archivo descargado
    def rename(self,old_title):
        new_title = self.replace_characters(old_title)
        ls = os.listdir('./downloads')
        for dir in ls:
            if dir.endswith('.mp4'):
                os.rename(f'{self.PATH}/{dir}',f'{self.PATH}/{new_title}')
                return f'{self.PATH}/{new_title}'

    # Envia el archivo
    def send_song(self,song_path,update,context):
        
        try:
            update.message.reply_audio(audio=open(song_path,'rb'))
        except:
            update.message.reply_text('No pude descargar la cancion. Puede que sea muy pesada (mayor a 50mb) o que sea una transmicion en vivo.')
        finally:
            if song_path:
                os.remove(song_path)

    # Descarga el archivo
    def download(self,instance):
        try:
            song_file = instance.streams.filter(only_audio=True).get_audio_only('mp4')
            song_file.download(self.PATH) 
            song_path = self.rename(instance.title)
            if not song_path:
                return f'{self.PATH}\{instance.title}.mp4'
            return song_path
        except:
            print('[-] Error al descargar')
            return None

    # Obtiene la cancion que busca el usuario
    def buscar(self,update:Update,context:CallbackContext):
        url = self.get_url(update.message.text)
        if self.verification_url(url,update,context):
            yt = YouTube(url)
            song_path = self.download(yt)
            self.send_song(song_path,update,context)
    
    # Obtiene la cancion por medio de un link de youtube
    def youtube_link(self,update:Update,context:CallbackContext):
        url = update.message.text
        url = url.replace('/link','')

        if self.verification_url(url,update,context):
            yt = YouTube(url)
            song_path = self.download(yt)
            self.send_song(song_path,update,context)

    # Obtiene varias canciones desde una playlist de Youtube
    def playlist(self,update:Update,context:CallbackContext):
        url = update.message.text
        url = url.replace('/lista','')

        if self.verification_url(url,update,context):
            p = Playlist(url)
            for video in p.videos:
                song_path = self.download(video)
                self.send_song(song_path,update,context)

    # Creacion de comandos y filtros
    def set_commands(self):
        # Comandos
        """Cada comando retorna una funcion"""
        self.updater.dispatcher.add_handler(CommandHandler('start',self.start))  # /start
        self.updater.dispatcher.add_handler(CommandHandler('help',self.help))  # /help
        self.updater.dispatcher.add_handler(CommandHandler('buscar', self.buscar))  # /buscar
        self.updater.dispatcher.add_handler(CommandHandler('link', self.youtube_link))  # /link
        self.updater.dispatcher.add_handler(CommandHandler('lista', self.playlist))  # /lista
        # Filtros
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.unknown))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.command, self.unknown))
    
    # Inicia el bot
    def start_bot(self):
        self.set_commands()
        self.updater.start_polling()

bot = TelegramBot()
bot.start_bot()
