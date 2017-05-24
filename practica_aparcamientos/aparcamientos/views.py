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
#JSON
import json

# Mostrar solo accesibles
acc = False

XML_URL = "http://datos.munimadrid.es/portal/site/egob/menuitem.ac61933d6ee3c31cae77ae7784f1a5a0/?vgnextoid=00149033f2201410VgnVCM100000171f5a0aRCRD&format=xml&file=0&filename=202584-0-aparcamientos-residentes&mgmtid=e84276ac109d3410VgnVCM2000000c205a0aRCRD&preview=full"

REGISTRY_MSGS_ESP = {'crea': "Crea un nuevo usuario",
                        'problema_attr': "Ha habido un problema con los datos",
                        'problema_passwd': "Las contraseñas tienen que coincidir",
                        'username_used': "Existe un usuario con ese nombre. Por favor elige otro"}

REGISTRY_MSGS_ENG = {'crea': "Create a new user",
                        'problema_attr': "There has been a problem with the data",
                        'problema_passwd': "Password must coincide",
                        'username_used': "It already exists an user with that username. Please, select any other"}

LANGUAGE_FIELD = 'HTTP_ACCEPT_LANGUAGE'

def get_lang(lang):
    """ Obtiene el idioma a partir de la cabecera de la peticion """
    if "es" in lang:    #Si hay opcion de darsela en español, la damos en español
        return "es"
    elif "en" in lang:
        return "en"
    else:   #Si piden otro idioma, se sirve en español
        return "es"

def get_titulo(username, lan):
    """Obtiene el titulo de la página del usuario"""
    try:
        pagusuario = PagUsuario.objects.get(usuario__username=username)
        return pagusuario.titulo
    except ObjectDoesNotExist:
        if lan == "en":
            return username + "\'s page"
        else:
            return "Pagina de " + username

def get_loc(loc):
    """Obtiene la direccion, barrio, distrito, latitud y longitud a partir del atributo localizacion"""
    direccion = (loc.find('atributo[@nombre="CLASE-VIAL"]').text + " " + loc.find('atributo[@nombre="NOMBRE-VIA"]').text +
                    " Numero: " + loc.find('atributo[@nombre="NUM"]').text + " " + loc.find('atributo[@nombre="CODIGO-POSTAL"]').text +
                    " " + loc.find('atributo[@nombre="LOCALIDAD"]').text)
    barrio = loc.find('atributo[@nombre="BARRIO"]').text
    distrito = loc.find('atributo[@nombre="DISTRITO"]').text
    latitud = float(loc.find('atributo[@nombre="LATITUD"]').text)
    longitud = float(loc.find('atributo[@nombre="LONGITUD"]').text)
    return direccion, barrio, distrito, latitud, longitud

def get_contact(contact):
    """Obtiene el telefono y el email a partir del atributo contacto"""
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

def get_lista_usuarios(lang):
    """Obtiene la lista de los usuarios para la tabla de la pagina principal"""
    usuarios = ""
    for usuario in User.objects.all():
        titulo = get_titulo(usuario.username, lang)
        usuarios += "<p><a href='" + usuario.username + "'>" + titulo + "</a> - " + usuario.username + "</p><hr>"
    return usuarios

def get_aparcs_barra(acc):
    """Obtiene la lista de aparcamientos para mostrar en la pagina principal"""
    aparcs = Aparcamiento.objects.all()
    aparcs = aparcs.exclude(num_comentarios=0)
    aparcs = aparcs.order_by('-num_comentarios')
    if acc:
        aparcs = aparcs.exclude(accesibilidad=False)
    return aparcs[:5]

def insertar_atributo_xml(child, atributo, valor):
    """Inserta un atributo en el arbol XML"""
    atrib = ET.SubElement(child, 'atributo', {'nombre': atributo})
    atrib.text = valor

def insertar_aparcamiento_xml(child, aparc):
    """Inserta un aparcamiento en el arbol XML"""
    insertar_atributo_xml(child, "NOMBRE", aparc.nombre)
    insertar_atributo_xml(child, "DESCRIPCION", aparc.descripcion)
    insertar_atributo_xml(child, "DIRECCION", aparc.direccion)
    insertar_atributo_xml(child, "ACCESIBILIDAD", str(aparc.accesibilidad))
    insertar_atributo_xml(child, "BARRIO", aparc.barrio)
    insertar_atributo_xml(child, "DISTRITO", aparc.distrito)
    insertar_atributo_xml(child, "LATITUD", str(aparc.latitud))
    insertar_atributo_xml(child, "LONGITUD", str(aparc.longitud))
    insertar_atributo_xml(child, "CONTACTO", aparc.contacto)
    insertar_atributo_xml(child, "URL", aparc.url)

def insertar_aparcamiento_json(lista, aparcamiento):
    """Inserta un aparcamiento en el diccionario para el JSON"""
    element = {}
    element['nombre'] = aparcamiento.nombre
    element['descripcion'] = aparcamiento.descripcion
    element['accesibilidad'] = aparcamiento.accesibilidad
    element['direccion'] = aparcamiento.direccion
    element['barrio'] = aparcamiento.barrio
    element['distrito'] = aparcamiento.distrito
    element['latitud'] = aparcamiento.latitud
    element['longitud'] = aparcamiento.longitud
    element['contacto'] = aparcamiento.contacto
    element['url'] = aparcamiento.url
    lista.append(element)

def get_lista_distritos():
    """Obtiene la lista de distritos para el menu desplegable"""
    distritos = []
    for i in Aparcamiento.objects.all():
        if not i.distrito in distritos:
            distritos.append(i.distrito)
    return distritos

def añadir_seleccion(username, aparcamiento):
    """Selecciona o quita la seleccion de un aparcamiento para un usuario"""
    usuario = User.objects.get(username=username)
    try:
        seleccion = Seleccion.objects.get(aparcamiento=aparcamiento, usuario=usuario)    # Como ya estaba seleccionado, ahora lo borramos
        seleccion.delete()
    except ObjectDoesNotExist:
        seleccion = Seleccion(aparcamiento=aparcamiento, usuario=usuario)
        seleccion.save()

def añadir_comentario(texto, aparcamiento):
    """Añade un comentario a la base de datos"""
    comment = Comentario(texto=texto, aparcamiento=aparcamiento)
    comment.save()
    aparcamiento.num_comentarios += 1
    aparcamiento.save()

def update_pag_usuario(username, titulo, tamano, color):
    """Actualiza la pagina de usuario con los datos del formulario"""
    try:
        user = User.objects.get(username=username)
        pag_usuario = PagUsuario.objects.get(usuario=user)
        pag_usuario.titulo = titulo
        pag_usuario.color_css = color
        pag_usuario.tamano_css = tamano
    except ObjectDoesNotExist:
        pag_usuario = PagUsuario(titulo=titulo, color_css=color, tamano_css=tamano, usuario=user)
    pag_usuario.save()

## Procedimientos de views

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
    lan = get_lang(request.META[LANGUAGE_FIELD])
    template = get_template(lan + "/about.html")
    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username})
    return HttpResponse(template.render(context))

@csrf_exempt
def barra(request):
    global acc
    en = False
    lan = get_lang(request.META[LANGUAGE_FIELD])
    if len(Aparcamiento.objects.all()) == 0:
        template = get_template(lan + "/init.html")
        context = Context({'aut': request.user.is_authenticated(),
                            'name': request.user.username})
        return HttpResponse(template.render(context))
    template = get_template(lan + "/index.html")
    usuarios = get_lista_usuarios(lan)

    if request.method == "POST":    #Ver accesibles
        acc = not acc

    aparcs = get_aparcs_barra(acc)

    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username,
                        'aparcamientos':aparcs,
                        'usuarios': usuarios})
    return HttpResponse(template.render(context))

def xml(request):
    global acc
    root = ET.Element('data')
    aparcs = get_aparcs_barra(acc)
    for i in aparcs:
        child = ET.SubElement(root, 'aparcamiento')
        insertar_aparcamiento_xml(child, i)
    return HttpResponse(ET.tostring(root), content_type="text/xml")

def json_view(request):
    global acc
    aparcs = get_aparcs_barra(acc)
    dic = {}
    dic['aparcamientos'] = []
    for i in aparcs:
        insertar_aparcamiento_json(dic['aparcamientos'], i)
    data = json.dumps(dic, indent=4)
    return HttpResponse(data, content_type="application/json")

@csrf_exempt
def registro(request):
    lan = get_lang(request.META[LANGUAGE_FIELD])
    template = get_template(lan + "/registro.html")
    if lan == "en":
        use_dict = REGISTRY_MSGS_ENG
    else:
        use_dict = REGISTRY_MSGS_ESP
    if request.method == "GET":
        created = False
        init_message = use_dict['crea']
    elif request.method == "POST":
        try:
            username = request.POST['username']
            password = request.POST['password']
            password2 = request.POST['password2']
        except KeyError:
            created = False
            init_message = use_dict['problema_attr']
        if password != password2:
            created = False
            init_message = use_dict['problema_passwd']
        else:
            try:
                user = User.objects.get(username=username)
                created = False
                init_message = use_dict['username_used']
            except ObjectDoesNotExist:
                user = User.objects.create_user(username=username, password=password)
                created = True
                init_message = ""
    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username,
                        'created': created,
                        'init_message': init_message})
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
    lan = get_lang(request.META[LANGUAGE_FIELD])
    template = get_template(lan + "/aparcamientos.html")
    try:
        ap_list = Aparcamiento.objects.filter(distrito=request.GET['distrito'])
    except KeyError:
        ap_list = Aparcamiento.objects.all()
    if acc:
        ap_list = ap_list.exclude(accesibilidad=False)
    distritos = get_lista_distritos()
    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username,
                        'distritos': distritos,
                        'aparcamientos':ap_list})
    return HttpResponse(template.render(context))

@csrf_exempt
def aparc_id(request, ap_id):
    lan = get_lang(request.META[LANGUAGE_FIELD])
    template = get_template(lan + "/aparc_id.html")
    aparcamiento = Aparcamiento.objects.get(id=ap_id)
    if request.method == "POST":
        try:
            aux = request.POST['voto'] #Si no da excepcion es que viene de voto
            aparcamiento.votos += 1
            aparcamiento.save()
        except KeyError:    #No viene del form de voto
            pass
    if request.method == "POST" and request.user.is_authenticated():
        try:
            añadir_comentario(request.POST['comentario'], aparcamiento)
        except KeyError:    #No viene del form de comentario
            pass
        try:
            aux = request.POST['seleccion'] #Si no da excepcion es que viene del form de seleccionar
            añadir_seleccion(request.user.username, aparcamiento)
        except KeyError: #No viene del form de seleccion
            pass
    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username,
                        'aparcamiento':aparcamiento,
                        'coment_list':Comentario.objects.filter(aparcamiento=aparcamiento)})
    return HttpResponse(template.render(context))

def user_xml(request, username):
    root = ET.Element('data')
    selec = Seleccion.objects.filter(usuario__username=username)
    for i in selec:
        child = ET.SubElement(root, 'aparcamiento')
        insertar_aparcamiento_xml(child, i.aparcamiento)
    return HttpResponse(ET.tostring(root), content_type="text/xml")

def user_json(request, username):
    dic = {}
    dic['aparcamientos'] = []
    selec = Seleccion.objects.filter(usuario__username=username)
    for i in selec:
        insertar_aparcamiento_json(dic['aparcamientos'], i.aparcamiento)
    data = json.dumps(dic, indent=4)
    return HttpResponse(data, content_type="application/json")

@csrf_exempt
def user(request, username):
    global acc
    lan = get_lang(request.META[LANGUAGE_FIELD])
    template = get_template(lan + "/user.html")
    selec = Seleccion.objects.filter(usuario__username=username)
    titulo = get_titulo(username, lan)
    try:
        user = User.objects.get(username=username)
        found = True
    except ObjectDoesNotExist:
        found = False
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
    if fin >= len(selec):
        fin = len(selec)
        ultima = True
    if request.method == "POST" and request.user.is_authenticated():
        update_pag_usuario(username, request.POST['titulo'], request.POST['tamano_css'], request.POST['color_css'])

    my_page = request.user.is_authenticated() and (username == request.user.username)

    context = Context({'aut': request.user.is_authenticated(),
                        'name': request.user.username,
                        'titulo': titulo,
                        'found': found,
                        'selecciones': selec[inicio:fin],
                        'ultima': ultima,
                        'primera': (pag == 1),
                        'pag_sig': str(pag + 1),
                        'pag_ant': str(pag - 1),
                        'my_page': my_page,
                        'username': username})
    return HttpResponse(template.render(context))
