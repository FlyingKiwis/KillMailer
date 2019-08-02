from django.shortcuts import render, redirect
from django.http import HttpResponse
from util.esi import Esi
import asyncio
import requests
from datetime import datetime, timedelta
import json
import re
    

def home(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    esi = Esi(request, loop)
    info = loop.run_until_complete(load_info(esi))
    esi.close()
    loop.close()
    if info is None:
        return redirect('login')
    request.session['kill-info'] = info
    return render(request, 'home.html', {'kills':info})

def compose(request):
    chosen_ids = request.POST.getlist('send-mail')
    if len(chosen_ids) < 1:
        return redirect('home')
    kill_info = request.session.get('kill-info')
    if kill_info is None:
        return redirect('home')
    chosen_kills = []
    for kill in kill_info:
        if str(kill.get("id")) in chosen_ids:
            chosen_kills.append(kill)
    request.session['chosen-kills'] = chosen_kills
    return render(request, 'compose.html', {'mail_count':len(chosen_kills)})

def send(request):
    body = request.POST.get("mail-body")
    subject = request.POST.get("mail-subject")
    dryrun = request.POST.get("dryrun")
    kills = request.session.get("chosen-kills")
    if body is None:
        print("no body")
        return redirect('compose')
    if subject is None:
        print("no subject")
        return redirect('compose')

    fake = False
    if dryrun is not None:
        fake = True
    loop = asyncio.new_event_loop()
    esi = Esi(request, loop)
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(send_mail(esi, kills, subject, body, True))
    esi.close()
    loop.close()
    return HttpResponse("Done: {}".format(results))

async def load_info(esi):
    hr = await esi.is_hr()
    if not hr:
        return None
    in_alliance = await esi.is_in_alliance()
    info = {}
    if in_alliance:
        info["org_type"] = "alliance"
        info["org_id"] = await esi.get_alliance_id()
    else:
        info["org_type"] = "corporation"
        info["org_id"] = await esi.get_corp_id()
    yesterday = datetime.utcnow() - timedelta(days=1)
    time_str = yesterday.strftime("%Y%m%d%H00")
    template_url = "https://zkillboard.com/api/kills/{org_type}ID/{org_id}/startTime/{time}/"
    zkurl = template_url.format(org_type=info.get("org_type"), org_id=info.get("org_id"), time=time_str)
    r = requests.get(zkurl)
    kills = r.json()
    kill_futures = []
    for kill in kills:
        kill_id = kill.get("killmail_id")
        kill_hash = kill.get("zkb", {}).get("hash")
        if kill_id is None:
            print("id is none")
            continue
        if kill_hash is None:
            print("hash is none")
            continue
        kill_futures.append(esi.get_kill_info(kill_id,kill_hash))
    results = await asyncio.gather(*kill_futures)
    kill_info = []
    org_futures = []
    for result in results:
        if result is not None:
            kill_info.append(result)
        else:
            print("result is none")
    return kill_info

async def send_mail(esi, kills, subject, body, fake=False):
    mail_futures = []
    my_id = None
    if fake:
        my_id = await esi.get_char_id()
    for kill in kills:
        body_p = replace_placeholders(body, kill)
        subject_p = replace_placeholders(subject, kill)
        recip = None
        if fake:
            recip = my_id
        else:
            recip = kill.get("victim_id")
        mail_futures.append(esi.send_mail(recip, body_p, subject_p))
    return await asyncio.gather(*mail_futures)


def replace_placeholders(text, kill_info):
    name = kill_info.get("victim_name")
    ship = kill_info.get("victim_ship")
    kill_id = kill_info.get("id")
    kill_hash = kill_info.get("hash")
    killmail = "<url=killReport:{id}:{hash}>Kill: {name} - {ship}</url>".format(id=kill_id, hash=kill_hash, name=name, ship=ship)

    replaced = re.sub(r'%name%', name, text)
    replaced = re.sub(r'%ship%', ship, replaced)
    replaced = re.sub(r'%killmail%', killmail, replaced)

    return replaced




    

    


