from django.contrib import admin

# Register your models here.

from aparcamientos.models import Aparcamiento, Seleccion, PagUsuario

admin.site.register(Aparcamiento)
admin.site.register(Seleccion)
admin.site.register(PagUsuario)
