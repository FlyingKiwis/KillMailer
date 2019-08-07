from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from util.esi import Esi
import asyncio
import requests
from datetime import datetime, timedelta
from taskWorkers.worker import Worker
import json
import re
from .mailer import Mailer
from .models import Batch, Message
    

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

    fake = True
    if dryrun is None:
        fake = False
    
    batch = Batch(subject=subject, body=body, fake=fake)
    batch.save()

    mailer = Mailer(request, kills, batch)

    return render(request, 'sending.html', {'task':mailer.worker, 'batch':batch})

def sent(request, batch):
    batch_obj = get_object_or_404(Batch, pk=batch)
    return render(request, 'sent.html', {'batch':batch_obj})

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
    start = datetime.utcnow() - timedelta(days=settings.N_DAYS_BACKLOG)
    time_str = start.strftime("%Y%m%d%H00")
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
    for result in results:
        if result is not None:
            kill_info.append(result)
        else:
            print("result is none")
    return kill_info









    

    


