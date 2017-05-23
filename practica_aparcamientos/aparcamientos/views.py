from django.shortcuts import render
from django.template.loader import get_template
from django.template import Context
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseRedirect
from aparcamientos.models import *
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
#Parsear XML
from urllib import request
import xml.etree.ElementTree as ET

# Mostrar solo accesibles
acc = False

XML_URL = "http://datos.munimadrid.es/portal/site/egob/menuitem.ac61933d6ee3c31cae77ae7784f1a5a0/?vgnextoid=00149033f2201410VgnVCM100000171f5a0aRCRD&format=xml&file=0&filename=202584-0-aparcamientos-residentes&mgmtid=e84276ac109d3410VgnVCM2000000c205a0aRCRD&preview=full"

def get_loc(loc):
    direccion = (loc.find('atributo[@nombre="CLASE-VIAL"]').text + " " + loc.find('atributo[@nombre="NOMBRE-VIA"]').text +
                    " Numero: " + loc.find('atributo[@nombre="NUM"]').text + " " + loc.find('atributo[@nombre="CODIGO-POSTAL"]').text +
                    " " + loc.find('atributo[@nombre="LOCALIDAD"]').text)
    barrio = loc.find('atributo[@nombre="BARRIO"]').text
    distrito = loc.find('atributo[@nombre="DISTRITO"]').text
    latitud = float(loc.find('atributo[@nombre="LATITUD"]').text)
    longitud = float(loc.find('atributo[@nombre="LONGITUD"]').text)
    return direccion, barrio, distrito, latitud, longitud

def get_contact(contact):
    contacto = ""
    try:
        telefono = contact.find('atributo[@nombre="TELEFONO"]').text
        contacto += "Telefono: " + telefono + "\n"
    except AttributeError:
        pass
    try:
        mail = contact.find('atributo[@nombre="EMAIL"]').text
        contacto += "Email: " + mail
    except AttributeError:
        pass
    return contacto

def init_database(req):
    page = request.urlopen(XML_URL)
    root = ET.parse(page).getroot()
    for i in root.iter('contenido'):
        try:
            nombre = i.find('atributos/atributo[@nombre="NOMBRE"]').text
            descripcion = i.find('atributos/atributo[@nombre="DESCRIPCION"]').text
            direccion, barrio, distrito, latitud, longitud = get_loc(i.find('atributos/atributo[@nombre="LOCALIZACION"]'))
            if i.find('atributos/atributo[@nombre="ACCESIBILIDAD"]').text == "0":
                accesibilidad = False
            else:
                accesibilidad = True
            contacto = get_contact(i.find('atributos/atributo[@nombre="DATOSCONTACTOS"]'))
            url = i.find('atributos/atributo[@nombre="CONTENT-URL"]').text
        except AttributeError:
            continue
        aparcamiento = Aparcamiento(nombre=nombre,
                                    descripcion=descripcion,
                                    direccion=direccion,
                                    accesibilidad=accesibilidad,
                                    barrio=barrio,
                                    distrito=distrito,
                                    latitud=latitud,
                                    longitud=longitud,
                                    contacto=contacto,
                                    url=url)
        aparcamiento.save()
    return HttpResponseRedirect('/')


def css(request):
    template = get_template("style.css")
    username = request.user.get_username()
    try:
        pag_usuario = PagUsuario.objects.get(usuario__username=username)
        color = pag_usuario.color_css
        tam = pag_usuario.tamano_css
    except ObjectDoesNotExist:
        color = COLOR_CSS_DEFAULT
        tam = TAMANO_CSS_DEFAULT
    context = Context({'tam': str(tam), 'color': color})
    return HttpResponse(template.render(context), content_type="text/css")

def about(request):
    template = get_template("about.html")
    context = Context({'aut': request.user.is_authenticated(), 'name': request.user.username})
    return HttpResponse(template.render(context))

@csrf_exempt
def barra(request):
    global acc
    if len(Aparcamiento.objects.all()) == 0:
        return HttpResponse("Please, click <a href='init'>this link</a> to download the database")
    template = get_template("index.html")
    usuarios = ""
    for usuario in User.objects.all():
        try:
            pag_usuario = PagUsuario.objects.get(usuario=usuario)
            titulo = pag_usuario.titulo
        except ObjectDoesNotExist:
            titulo = "Página de " + usuario.username
        usuarios += "<a href='" + usuario.username + "'>" + titulo + "</a><hr>"

    if request.method == "POST":    #Ver accesibles
        acc = not acc

    aparcs = Aparcamiento.objects.all()
    aparcs = aparcs.exclude(num_comentarios=0)
    aparcs = aparcs.order_by('-num_comentarios')
    if acc:
        aparcs = aparcs.exclude(accesibilidad=False)

    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username,
                        'aparcamientos':aparcs[:5],
                        'usuarios': usuarios})
    return HttpResponse(template.render(context))

@csrf_exempt
def login_view(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/')

@csrf_exempt
def aparcamientos(request):
    global acc
    template = get_template("aparcamientos.html")
    if request.method == "GET":
        ap_list = Aparcamiento.objects.all()
    elif request.method == "POST":
        ap_list = Aparcamiento.objects.filter(distrito=request.POST['distrito'])
    if acc:
        ap_list = ap_list.exclude(accesibilidad=False)
    context = Context({'aut': request.user.is_authenticated(), 'name': request.user.username, 'aparcamientos':ap_list})
    return HttpResponse(template.render(context))

@csrf_exempt
def aparc_id(request, ap_id):
    template = get_template("aparc_id.html")
    aparcamiento = Aparcamiento.objects.get(id=ap_id)
    if request.method == "POST" and request.user.is_authenticated():
        try:
            comment = Comentario(texto=request.POST['comentario'], aparcamiento=aparcamiento)
            comment.save()
            aparcamiento.num_comentarios += 1
            aparcamiento.save()
        except KeyError: #Viene del form de seleccionar
            usuario = User.objects.get(username=request.user.username)
            try:
                seleccion = Seleccion.objects.get(aparcamiento=aparcamiento, usuario=usuario)
            except ObjectDoesNotExist:
                seleccion = Seleccion(aparcamiento=aparcamiento, usuario=usuario)
            seleccion.save()
    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username,
                        'aparcamiento':aparcamiento,
                        'coment_list':Comentario.objects.filter(aparcamiento=aparcamiento)})
    return HttpResponse(template.render(context))

def insertar_atributo(child, atributo, valor):
    atrib = ET.SubElement(child, 'atributo', {'nombre': atributo})
    atrib.text = valor

def insertar_aparcamiento(child, aparc):
    insertar_atributo(child, "NOMBRE", aparc.nombre)
    insertar_atributo(child, "DESCRIPCION", aparc.descripcion)
    insertar_atributo(child, "DIRECCION", aparc.direccion)
    insertar_atributo(child, "ACCESIBILIDAD", str(aparc.accesibilidad))
    insertar_atributo(child, "BARRIO", aparc.barrio)
    insertar_atributo(child, "DISTRITO", aparc.distrito)
    insertar_atributo(child, "LATITUD", str(aparc.latitud))
    insertar_atributo(child, "LONGITUD", str(aparc.longitud))
    insertar_atributo(child, "CONTACTO", aparc.contacto)
    insertar_atributo(child, "URL", aparc.url)

def user_xml(request, username):
    root = ET.Element('data')
    selec = Seleccion.objects.filter(usuario__username=username)
    for i in selec:
        child = ET.SubElement(root, 'aparcamiento')
        insertar_aparcamiento(child, i.aparcamiento)
    return HttpResponse(ET.tostring(root), content_type="text/xml")

def update_pag_usuario(username, titulo, tamano, color):
    try:
        user = User.objects.get(username=username)
        pag_usuario = PagUsuario.objects.get(usuario=user)
        pag_usuario.titulo = titulo
        pag_usuario.color_css = color
        pag_usuario.tamano_css = tamano
    except ObjectDoesNotExist:
        pag_usuario = PagUsuario(titulo=titulo, color_css=color, tamano_css=tamano, usuario=user)
    pag_usuario.save()

@csrf_exempt
def user(request, username):
    global acc
    template = get_template("user.html")
    selec = Seleccion.objects.filter(usuario__username=username)
    if acc:
        selec = selec.exclude(aparcamiento__accesibilidad=False)
    ultima = False
    try:
        pag = int(request.GET['pag'])
        if pag <= 0:
            pag = 1
    except KeyError:
        pag = 1
    inicio = (pag - 1) * 5
    fin = pag * 5
    if fin > len(selec):
        fin = len(selec)
        ultima = True
    if request.method == "POST" and request.user.is_authenticated():
        update_pag_usuario(username, request.POST['titulo'], request.POST['tamano_css'], request.POST['color_css'])
    print(selec[inicio:fin])
    context = Context({'aut': request.user.is_authenticated(),
                        'name': username,
                        'selecciones': selec[inicio:fin],
                        'ultima': ultima,
                        'primera': (pag == 1),
                        'pag_sig': str(pag + 1),
                        'pag_ant': str(pag - 1)})
    return HttpResponse(template.render(context))
