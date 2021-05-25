from django.db import models
from django.contrib.auth.models import User


class Dialog(models.Model):
    owners = models.ManyToManyField(User, related_name='dialogs', blank=False,
                                    verbose_name='Участники диалога')

    last_message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, related_name='dialogs',
                                     verbose_name='Последнее сообщение')

    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
        ordering = ['-last_message__id']

    def __str__(self):
        return str(self.id)


class Message(models.Model):
    dialog = models.ForeignKey(Dialog, related_name='messages', on_delete=models.CASCADE, verbose_name='Диалог')
    owner = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE, verbose_name='Автор сообщения')
    text = models.TextField(verbose_name='Текст сообщения')
    date_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['-id']

    def __str__(self):
        return str(self.id)


class Event(models.Model):
    owners = models.ManyToManyField(User, related_name='events', blank=False,
                                    verbose_name='События')
    type = models.TextField(verbose_name='Тип события')
    object_id = models.IntegerField(verbose_name='id объекта')

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['-id']

    def __str__(self):
        return str(self.id)
