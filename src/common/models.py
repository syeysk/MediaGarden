from django.db import models


class Tag(models.Model):
    code = models.PositiveIntegerField('Код модели')
    name = models.CharField('Имя тега', max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='children', null=True)

    class Model:
        verbose_name = 'Теги'
        verbose_name_plural = 'Тег'
