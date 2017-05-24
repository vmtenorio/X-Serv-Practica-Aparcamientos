# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Aparcamiento',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('nombre', models.CharField(max_length=32)),
                ('descripcion', models.TextField()),
                ('direccion', models.TextField()),
                ('accesibilidad', models.BooleanField()),
                ('barrio', models.CharField(max_length=32)),
                ('distrito', models.CharField(max_length=32)),
                ('latitud', models.FloatField()),
                ('longitud', models.FloatField()),
                ('contacto', models.TextField()),
                ('url', models.URLField()),
                ('num_comentarios', models.IntegerField(default=0)),
                ('votos', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Comentario',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('texto', models.TextField()),
                ('aparcamiento', models.ForeignKey(to='aparcamientos.Aparcamiento')),
            ],
        ),
        migrations.CreateModel(
            name='PagUsuario',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('titulo', models.CharField(max_length=32)),
                ('color_css', models.CharField(max_length=32, default='white')),
                ('tamano_css', models.IntegerField(default=14)),
                ('usuario', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Seleccion',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('fecha', models.DateField(auto_now_add=True)),
                ('aparcamiento', models.ForeignKey(to='aparcamientos.Aparcamiento')),
                ('usuario', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
