from telebot import types
import io
from django.core.files.uploadedfile import UploadedFile

from telebot.apihelper import ApiTelegramException

from tbot_base.bot import tbot
from django.core.files.images import ImageFile
from tbot_base.models import BotConfig
from loguru import logger
from datetime import datetime, timedelta

from .models import User, Post, Proof, BotConf


@tbot.message_handler(commands=['start'])
def start_messages(message: types.Message):
    user, create = User.objects.get_or_create(user_id=message.from_user.id)
    if create:
        user.username = message.from_user.username
        user.name = f'{message.from_user.first_name}'
        if message.from_user.last_name:
            user.name += ' ' + message.from_user.last_name
        user.save()
    if user.status:
        tbot.send_message(message.from_user.id,
                          'Мы против войны! Если ты тоже, то присылай свои фото/видео или мысли сюда')
    else:
        tbot.send_message(message.from_user.id,
                          'Ваш акаунт заблоковано')


@tbot.callback_query_handler(func=lambda call: call.data.startswith('send_chat_'))
def send_chat(call):
    claim = Post.objects.get(pk=call.data.split('_')[-1])
    claim.status = 'done'
    claim.save()


@tbot.message_handler(content_types=['photo', 'video', 'document', 'animation', 'text'])
def text_messages(message: types.Message):
    user, create = User.objects.get_or_create(user_id=message.from_user.id)
    if create:
        user.username = message.from_user.username
        user.name = f'{message.from_user.first_name}'
        if message.from_user.last_name:
            user.name += ' ' + message.from_user.last_name
        user.save()
    if message.chat.id < 0:
        if message.reply_to_message:
            proof = Proof.objects.get(message_id=message.reply_to_message.message_id)
            #
            print(message.reply_to_message.message_id)
            tbot.send_message(proof.user.user_id, message.text)
    else:
        if user.status:
            startdate = datetime.now()
            enddate = startdate - timedelta(hours=1)
            proofs = Proof.objects.filter(date_create__gte=enddate).all()
            conf = BotConf.objects.last()

            if len(proofs) < conf.max_message:
                conf = BotConf.objects.last()
                ms = tbot.forward_message(conf.chat_id, message.chat.id, message.id)
                tbot.send_message(chat_id=message.from_user.id, text='«Спасибо! Пока мы обрабатываем ваше сообщение '
                                                                     'вы можете помочь в распространении информации - '
                                                                     'пересылайте новости с нашего канала своим друзьям, '
                                                                     'поговорите с '
                                                                     'родителями и знакомыми. Помогите остановить эту войну!»')
                if message.content_type == 'document':
                    doc_type = message.document.mime_type
                    if 'image' in doc_type:
                        try:
                            file_info = tbot.get_file(message.document.file_id)
                            downloaded_file = tbot.download_file(file_info.file_path)
                            try:
                                file_name = f'{datetime.now().astimezone().timestamp()}' \
                                            f'_{message.document.file_name}'
                            except Exception:
                                file_name = f'{message.chat.id}' \
                                            f'_{datetime.now().astimezone().timestamp()}' \
                                            f'_p.png'
                            image = ImageFile(io.BytesIO(downloaded_file), name=file_name)
                            proof = Proof.objects.create(user=user, image=image)
                            if message.caption:
                                proof.description = message.caption
                            proof.message_id = ms.message_id
                            proof.save()
                        except Exception as e:
                            logger.error(e)
                            if 'file is too big' in str(e):
                                tbot.send_message(message.chat.id,
                                                  'Упс... Файл слишком большой!')
                    elif 'video' in doc_type:
                        try:
                            ms = tbot.send_message(message.chat.id,
                                                   'Секундочку, уже загружаю'
                                                   ' Ваше видео на сервер...')
                            file_info = tbot.get_file(message.document.file_id)
                            downloaded_file = tbot.download_file(file_info.file_path)
                            try:
                                file_name = f'{datetime.now().astimezone().timestamp()}' \
                                            f'_{message.document.file_name}'
                            except Exception:
                                file_name = f'{message.chat.id}' \
                                            f'_{datetime.now().astimezone().timestamp()}' \
                                            f'_v.mp4'
                            video = UploadedFile(io.BytesIO(downloaded_file),
                                                 name=file_name)
                            proof = Proof.objects.create(user=user, video=video)
                            if message.caption:
                                proof.description = message.caption
                            proof.message_id = ms.message_id
                            proof.save()
                        except Exception as e:
                            logger.error(e)
                            if 'file is too big' in str(e):
                                tbot.send_message(message.chat.id,
                                                  'Упс... Файл слишком большой!')
                    else:
                        tbot.send_message(message.chat.id,
                                          'Упс... Я не смог распознать файл,'
                                          ' проверь это точно видео или фото')
                elif message.content_type == 'photo':
                    try:
                        file_info = tbot.get_file(message.photo[-1].file_id)
                        downloaded_file = tbot.download_file(file_info.file_path)
                        image = ImageFile(io.BytesIO(downloaded_file),
                                          name=f'{datetime.now().astimezone().timestamp()}'
                                               f'.png')
                        proof = Proof.objects.create(user=user, image=image)
                        if message.caption:
                            proof.description = message.caption
                        proof.message_id = ms.message_id
                        proof.save()
                    except Exception as e:
                        logger.error(e)
                        if 'file is too big' in str(e):
                            tbot.send_message(message.chat.id,
                                              'Упс... Файл слишком большой!')
                elif message.content_type == 'video':
                    try:

                        file_info = tbot.get_file(message.video.file_id)
                        downloaded_file = tbot.download_file(file_info.file_path)
                        try:
                            file_name = f'{datetime.now().astimezone().timestamp()}_' + \
                                        message.json['video']['file_name']
                        except Exception:
                            file_name = f'{message.chat.id}' \
                                        f'_{datetime.now().astimezone().timestamp()}' \
                                        f'_v.mp4'
                        video = UploadedFile(io.BytesIO(downloaded_file), name=file_name)
                        proof = Proof.objects.create(user=user, video=video)
                        if message.caption:
                            proof.description = message.caption
                        proof.message_id = ms.message_id
                        proof.save()

                    except Exception as e:
                        logger.error(e)
                        if 'file is too big' in str(e):
                            tbot.send_message(message.chat.id,
                                              'Упс... Файл слишком большой!')
                elif message.content_type == 'animation':
                    if message.document:
                        try:
                            tbot.send_message(message.chat.id,
                                              'Секундочку, уже загружаю'
                                              ' Ваше видео на сервер...')
                            file_info = tbot.get_file(message.document.file_id)
                            downloaded_file = tbot.download_file(file_info.file_path)
                            try:
                                file_name = f'{datetime.now().astimezone().timestamp()}' \
                                            f'_{message.document.file_name}'
                            except Exception:
                                file_name = f'{message.chat.id}' \
                                            f'_{datetime.now().astimezone().timestamp()}' \
                                            f'_v.mp4'
                            video = UploadedFile(io.BytesIO(downloaded_file),
                                                 name=file_name)
                            proof = Proof.objects.create(user=user, video=video)
                            if message.caption:
                                proof.description = message.caption
                            proof.message_id = ms.message_id
                            proof.save()
                        except Exception as e:
                            logger.error(e)
                            if 'file is too big' in str(e):
                                tbot.send_message(message.chat.id,
                                                  'Упс... Файл слишком большой!')
                    else:
                        tbot.send_message(message.chat.id,
                                          'Упс... Я не смог распознать файл,'
                                          ' проверь это точно видео или фото')
                elif message.content_type == 'text':
                    proof = Proof.objects.create(user=user, description=message.text)
                    proof.message_id = ms.message_id
                    proof.save()

                else:
                    tbot.send_message(message.chat.id,
                                      'Упс... Я не смог распознать файл, проверь это точно'
                                      ' видео или фото')
            else:
                tbot.send_message(message.from_user.id,
                                  'Перевищено лимит постов за час')
        else:
            tbot.send_message(message.from_user.id,
                              'Ваш акаунт заблоковано')


def back_and_next_keyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True,
                                         one_time_keyboard=True)
    keyboard.add(types.KeyboardButton('Продолжить'))
    return keyboard


@tbot.my_chat_member_handler(func=lambda message: True)
def add_chat(message: types.Message):
    conf = BotConf.objects.last()
    conf.chat_id = message.chat.id
    conf.save()


@tbot.callback_query_handler(func=lambda call: call.data.startswith('send'))
def start_step_4(call):
    user = User.objects.get(user_id=call.from_user.id)
    if user.status:
        posts = Post.objects.filter(user_id=call.from_user.id, ).all()
        conf = BotConf.objects.last()
        if len(posts) < conf.max_message:
            user.state = 'send_description'
            user.save()
            tbot.send_message(call.from_user.id,
                              'Напишете описания')
        else:
            tbot.send_message(call.from_user.id,
                              'Перевищено лимит постов за час')
    else:
        tbot.send_message(message.from_user.id,
                          'Ваш акаунт заблоковано')
