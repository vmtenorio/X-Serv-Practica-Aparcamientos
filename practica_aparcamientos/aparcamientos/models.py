from django.db import models
from django.contrib.auth.models import User

COLOR_CSS_DEFAULT = 'white'
TAMANO_CSS_DEFAULT = 14

# Create your models here.
class Aparcamiento(models.Model):
    nombre = models.CharField(max_length=32)
    descripcion = models.TextField()
    direccion = models.TextField()
    accesibilidad = models.BooleanField()
    barrio = models.CharField(max_length=32)
    distrito = models.CharField(max_length=32)
    latitud = models.FloatField()
    longitud = models.FloatField()
    contacto = models.TextField()
    url = models.URLField()
    num_comentarios = models.IntegerField(default=0)


class PagUsuario(models.Model):
    titulo = models.CharField(max_length=32)
    color_css = models.CharField(max_length=32, default=COLOR_CSS_DEFAULT)
    tamano_css = models.IntegerField(default=TAMANO_CSS_DEFAULT)
    usuario = models.ForeignKey(User)


class Seleccion(models.Model):
    aparcamiento = models.ForeignKey(Aparcamiento)
    fecha = models.DateField(auto_now_add=True)
    usuario = models.ForeignKey(User)


class Comentario(models.Model):
    texto = models.TextField()
    aparcamiento = models.ForeignKey(Aparcamiento)
