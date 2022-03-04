from django.db import models

# Create your models here.
from tbot_base.bot import tbot
from django.utils.timezone import now


class User (models.Model):
    user_id = models.CharField(verbose_name='Телеграм id', max_length=20)
    username = models.CharField(max_length=30)
    name = models.CharField(max_length=100, verbose_name='имя користувача')
    state = models.CharField(max_length=100, default=True, null=True)
    status = models.BooleanField(default=True)
    administrator = models.BooleanField(default=False)


class Post (models.Model):
    status_option = [
        ('wait', 'На рассмотрении'),
        ('done', 'Отправлена')
    ]

    user = models.ForeignKey(User, verbose_name='Пользователь', null=True,
                             on_delete=models.SET_NULL)
    date_create = models.DateTimeField(verbose_name='Дата Добавления',
                                       auto_now_add=True)
    description = models.TextField(verbose_name='Описание')

    status = models.TextField(verbose_name='Статус', max_length=100,
                              choices=status_option, default='wait')

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self.__status = self.status

    def save(self, *args, **kwargs):
        if self.status == 'done' and self.__status != self.status:
            super().save(*args, **kwargs)
            try:
                from .dispatcher import send_save
                send_save(self)
            except Exception:
                pass
        else:
            super().save(*args, **kwargs)


class Proof(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользоветель',
                              on_delete=models.CASCADE, blank=True, null=True)
    image = models.ImageField(verbose_name='Фото',
                              upload_to='proof/image/', blank=True)
    video = models.FileField(verbose_name='Видео',
                             upload_to='proof/video/', blank=True)
    # description = models.Model
    date_create = models.DateTimeField(verbose_name='Дата Загрузки',
                                       default=now)
    description = models.CharField(max_length=2500, verbose_name='Описания', blank=True, null=True)
    message_id = models.CharField(max_length=20, blank=True, null=True)

    # def __str__(self):
    #     return self.claim.login

    class Meta:
        verbose_name = 'Файли'
        verbose_name_plural = 'Файли'


class BotConf(models.Model):
    max_message = models.SmallIntegerField(default=1)
    chat_id = models.CharField(max_length=20)


