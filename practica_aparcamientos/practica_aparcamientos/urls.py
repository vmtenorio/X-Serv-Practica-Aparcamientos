"""practica_aparcamientos URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import logout
from aparcamientos import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^.*style\.css$', views.css, name="Servir el css"),
    url(r'^about$', views.about, name="Pagina de about"),
    url(r'^$', views.barra, name="Pagina principal"),
    url(r'^xml$', views.xml, name="XML de la pagina principal"),
    url(r'^json$', views.json_view, name="JSON de la pagina principal"),
    url(r'^init$', views.init_database, name="Pagina para cargar la base de datos"),
    url(r'^.*login$', views.login_view, name="Pagina de login"),
    url(r'^.*registro$', views.registro, name="Pagina para registrar nuevos usuarios"),
    url(r'^.*logout$', logout, {'next_page': '/'}, name="Pagina de logout"),
    url(r'^aparcamientos$', views.aparcamientos, name="Pagina de todos los aparcamientos"),
    url(r'aparcamientos/(\d+)', views.aparc_id, name="Pagina de un aparcamiento"),
    url(r'^(.*)/xml$', views.user_xml, name="XML de la pagina del usuario"),
    url(r'^(.*)/json$', views.user_json, name="JSON de la pagina del usuario"),
    url(r'^(.*)$', views.user, name="Pagina del usuario"),
]
