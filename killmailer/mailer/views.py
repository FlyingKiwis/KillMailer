from django.shortcuts import render, redirect
from django.http import HttpResponse
from util.esi import Esi
import asyncio
import requests
from datetime import datetime, timedelta
    

def home(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    esi = Esi(request)
    info = loop.run_until_complete(load_info(esi))
    if info is None:
        return redirect('login')

    return HttpResponse(info)
    
    

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
        yesterday = datetime.utcnow() - timedelta(days=2)
    time_str = yesterday.strftime("%Y%m%d%H00")
    template_url = "https://zkillboard.com/api/kills/{org_type}ID/{org_id}/startTime/{time}/"
    zkurl = template_url.format(org_type=info.get("org_type"), org_id=info.get("org_id"), time=time_str)
    r = requests.get(zkurl)




    

    


