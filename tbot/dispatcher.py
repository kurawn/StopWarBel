from telebot import types
import io
from datetime import datetime

from telebot.apihelper import ApiTelegramException

from tbot_base.bot import tbot
from django.core.files.images import ImageFile
from tbot_base.models import BotConfig
from loguru import logger

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
    markup = types.InlineKeyboardMarkup(row_width=1)
    if user.status:
        send = types.InlineKeyboardButton("Отправить", callback_data='send')
        markup.add(send)
        tbot.send_message(message.from_user.id,
                          'Мы против войны! Если ты тоже, то присылай свои фото/видео или мысли сюда',
                          reply_markup=markup)
    else:
        tbot.send_message(message.from_user.id,
                          'Ваш акаунт заблоковано')


@tbot.callback_query_handler(func=lambda call: call.data.startswith('block_'))
def block_user(call):
    user = User.objects.get(user_id=call.data.split('_')[1])
    user.state = False
    user.save()


def send_save(claim):
    proofs = Proof.objects.filter(claim=claim).all()
    media_group = []
    conf = BotConf.objects.last()
    server_url = BotConfig.objects.filter(is_active=True).first()
    if len(proofs) == 0:
        tbot.send_message(conf.chat_id, claim.description)
    elif len(proofs) == 1:
        if proofs[0].image:
            tbot.send_photo(conf.chat_id, (server_url.server_url + proofs[0].image.url), claim.description)
        else:
            tbot.send_video(conf.chat_id, (server_url.server_url + proofs[0].video.url), claim.description)
    else:

        for idx, proof in enumerate(proofs):
            if idx == 0:
                print(1212)

                if proof.image:
                    media_group.append(types.InputMediaPhoto((server_url.server_url + proof.image.url),
                                                             caption=claim.description))
                else:
                    media_group.append(types.InputMediaVideo((server_url.server_url + proof.image.url),
                                                             caption=claim.description))
            else:
                print(1212)

                if proof.image:
                    media_group.append(types.InputMediaPhoto(server_url.server_url + proof.image.url))
                else:
                    media_group.append(types.InputMediaVideo(server_url.server_url + proof.image.url))
        print(111)
        tbot.send_media_group(chat_id=conf.chat_id, media=media_group)


@tbot.callback_query_handler(func=lambda call: call.data.startswith('send_chat_'))
def send_chat(call):
    claim = Post.objects.get(pk=call.data.split('_')[-1])
    claim.status = 'done'
    claim.save()


@tbot.message_handler(content_types=['text'])
def text_messages(message: types.Message):
    user = User.objects.get(user_id=message.from_user.id)
    if user.state == 'send_description':
        post = Post.objects.create(user=user, description=message.text)
        user.state = f'get_proof_{post.pk}'
        user.save()
        tbot.send_message(message.chat.id,
                          'Отлично! Тепер отправте матереали',
                          parse_mode='HTML')
    if message.text == 'Продолжить':
        claim = Post.objects.get(pk=user.state.split('_')[2])
        markup = types.InlineKeyboardMarkup(row_width=1)
        send = types.InlineKeyboardButton("Отправить", callback_data='send')
        markup.add(send)
        tbot.send_message(message.from_user.id,
                          ' Мы обязательно опубликуем в нашем канале, а пока вы можете помочь в распространении'
                          'информации - перешлите этого бога друзья,поговорите с родителями и знакомыми.',
                          reply_markup=markup)
        users = User.objects.filter(administrator=True).all()
        proofs = Proof.objects.filter(claim=claim).all()
        server_url = BotConfig.objects.filter(is_active=True).first()
        markup_admin = types.InlineKeyboardMarkup(row_width=1)
        send_admin = types.InlineKeyboardButton("Отправить", callback_data=f'send_chat_{claim.pk}')
        block_user = types.InlineKeyboardButton("Блокирувать пользоветеля", callback_data=f'block_{user.pk}')
        edit_post = types.InlineKeyboardButton("Изменить пост", url=server_url.server_url+f'/admin/tbot/post/{claim.pk}')
        markup_admin.add(send_admin, block_user, edit_post)
        media_group = []
        user.state = ''
        user.save()
        for user in users:
            if len(proofs) == 0:
                tbot.send_message(user.user_id, claim.description)
            elif len(proofs) == 1:
                if proofs[0].image:
                    tbot.send_photo(user.user_id, (server_url.server_url + proofs[0].image.url), claim.description)
                else:
                    tbot.send_video(user.user_id, (server_url.server_url + proofs[0].video.url), claim.description)
            else:
                for idx, proof in enumerate(proofs):
                    if idx == 0:
                        if proof.image:
                            media_group.append(types.InputMediaPhoto((server_url.server_url + proof.image.url),
                                                                     caption=claim.description))
                        else:
                            media_group.append(types.InputMediaVideo((server_url.server_url + proof.image.url),
                                                                     caption=claim.description))
                    else:
                        if proof.image:
                            media_group.append(types.InputMediaPhoto(server_url.server_url + proof.image.url))
                        else:
                            media_group.append(types.InputMediaVideo(server_url.server_url + proof.image.url))
                tbot.send_media_group(chat_id=user.user_id, media=media_group)
            tbot.send_message(chat_id=user.user_id, text='дейсвия', reply_markup=markup_admin)


@tbot.message_handler(content_types=['photo', 'video', 'document', 'animation'])
def add_proof(message):
    user = User.objects.get(user_id=message.from_user.id)
    claim = Post.objects.get(pk=user.state.split('_')[2])
    len_proof = len(Proof.objects.filter(claim=claim)) + 1
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
                Proof.objects.create(claim=claim, image=image)
                tbot.send_message(message.chat.id,
                                 f'\n\nЗагружено файлов: {len_proof}'
                                 '\n\nОтлично! Если у Вас есть еще материалы,'
                                 ' отправляйте ниже!'
                                 '\n\nЕсли больше материалов нет,'
                                 ' тогда нажмите "Продолжить"',
                                 parse_mode='HTML',
                                 reply_markup=back_and_next_keyboard())
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
                Proof.objects.create(claim=claim, video=video)
                tbot.send_message(message.chat.id,
                                 f'\n\nЗагружено файлов: {len_proof}'
                                 '\n\nОтлично! Если у Вас есть еще материалы,'
                                 ' отправляйте ниже!'
                                 '\n\nЕсли больше материалов нет,'
                                 ' тогда нажмите "Продолжить"',
                                 parse_mode='HTML',
                                 reply_markup=back_and_next_keyboard())
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
            Proof.objects.create(claim=claim, image=image)
            ms = tbot.send_message(message.chat.id,
                                  f'\n\nЗагружено файлов: {len_proof}'
                                  '\n\nОтлично! Если у Вас есть еще материалы,'
                                  ' отправляйте ниже!'
                                  '\n\nЕсли больше материалов нет,'
                                  ' тогда нажмите "Продолжить"',
                                  parse_mode='HTML',
                                  reply_markup=back_and_next_keyboard())
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
            Proof.objects.create(claim=claim, video=video)
            tbot.send_message(message.chat.id,
                             f'\n\nЗагружено файлов: {len_proof}'
                             '\n\nОтлично! Если у Вас есть еще материалы,'
                             ' отправляйте ниже!'
                             '\n\nЕсли больше материалов нет, тогда нажмите'
                             ' "Продолжить"',
                             parse_mode='HTML',
                             reply_markup=back_and_next_keyboard())
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
                Proof.objects.create(claim=claim, video=video)
                tbot.send_message(message.chat.id,
                                 f'\n\nЗагружено файлов: {len_proof}'
                                 '\n\nОтлично! Если у Вас есть еще материалы,'
                                 ' отправляйте ниже!'
                                 '\n\nЕсли больше материалов нет,'
                                 ' тогда нажмите "Продолжить"',
                                 parse_mode='HTML',
                                 reply_markup=back_and_next_keyboard())
            except Exception as e:
                logger.error(e)
                if 'file is too big' in str(e):
                    tbot.send_message(message.chat.id,
                                     'Упс... Файл слишком большой!')
        else:
            tbot.send_message(message.chat.id,
                             'Упс... Я не смог распознать файл,'
                             ' проверь это точно видео или фото')
    elif message.content_type == 'text' and message.text == 'Продолжить':
        tbot.send_message(message.chat.id, f'Осталась ли переписка с негодяем?',
                         reply_markup=message_save_keyboard())
    else:
        tbot.send_message(message.chat.id,
                         'Упс... Я не смог распознать файл, проверь это точно'
                         ' видео или фото')


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