from django.shortcuts import render, redirect
from django.conf import settings
from urllib import parse
from django.http import HttpResponse
import uuid
import requests
from requests.auth import HTTPBasicAuth
import base64


# Create your views here.
def login(request):
    #Form login url
    template_url = "https://{base_url}/oauth/authorize?response_type=code&redirect_uri={redirect}&client_id={client_id}&scope={scopes}&state={state}"
    url_vars = {}
    url_vars['base_url'] = settings.ESI_LOGIN_SERVER
    url_vars['redirect'] = parse.quote(settings.ESI_CALLBACK, safe='')
    url_vars['client_id'] = parse.quote(settings.ESI_CLIENT, safe='')
    url_vars['scopes'] = 'esi-mail.send_mail.v1 esi-characters.read_corporation_roles.v1'
    state = str(uuid.uuid4().hex)
    request.session['sso-state'] = state
    url_vars['state'] = state
    url = template_url.format_map(url_vars)
    return render(request, 'login.html', {'login_url':url})

def callback(request):
    for key, value in request.session.items():
        print('{} => {}'.format(key, value))
    saved_state = request.session.get('sso-state')
    state = request.GET.get('state')
    if saved_state is None:
        return HttpResponse('No State', status=401)
    if state != saved_state:
        return HttpResponse('State Mismatch', status=401)
    code = request.GET.get('code')
    if code is None:
        return HttpResponse('No Code', status=401)
    url = "https://{}/oauth/token".format(settings.ESI_LOGIN_SERVER)
    data = {"grant_type":"authorization_code", "code":code}
    r = requests.post(url, data=data, auth=HTTPBasicAuth(settings.ESI_CLIENT, settings.ESI_SECRET))
    results = r.json()
    request.session['access-token'] = results.get("access_token")
    request.session['refresh-token'] = results.get("refresh_token")
    return redirect('home')

