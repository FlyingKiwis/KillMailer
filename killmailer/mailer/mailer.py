from taskWorkers.worker import Worker
from util.esi import Esi
import asyncio
import time
import re
import logging
import pytz
import json
from datetime import datetime
from .models import Message


class Mailer(object):

    log = logging.getLogger(__name__)

    def __init__(self, request, kills, batch):
        self.request = request
        self.kills = kills
        self.batch = batch
        self.worker = Worker(self.__send)
        self.loop = None
        self.esi = None

        self.worker.start()

    def __send(self):
        self.loop = asyncio.new_event_loop()
        self.esi = Esi(self.request, self.loop)
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.__send_async())
        self.esi.close()
        self.loop.close()
        self.worker.finish()

    async def __send_async(self):
        prog = 0
        prog_step = 1 / len(self.kills)
        my_id = await self.esi.get_char_id()
        my_name = await self.esi.get_char_name()
        spam_re = re.compile(r"'remainingTime': (\d+)L")
        self.batch.sent_by = my_name
        self.batch.sent_by_id = my_id
        self.batch.save()
        for kill in self.kills:
            body_p = self.replace_placeholders(self.batch.body, kill)
            subject_p = self.replace_placeholders(self.batch.subject, kill)
            recip = None
            recip_id = kill.get("victim_id")
            if self.batch.fake:
                recip = my_id
            else:
                recip = recip_id
            recip_name = kill.get("victim_name")
            msg = Message(batch=self.batch, subject=subject_p, body=body_p, sent_to=recip_name, sent_to_id=recip_id)
            msg.save()
            while not msg.sent:
                result = await self.esi.send_mail(recip, recip_name, body_p, subject_p)
                msg.sent_at = datetime.utcnow().replace(tzinfo=pytz.utc)
                if result.get("sent", False):
                    msg.sent = True
                    msg.save()
                else:
                    error = str(result.get("error", ""))
                    match = spam_re.search(error)
                    self.log.error("Match: {} on string \"{}\"".format(match, error))
                    if match:
                        wait = int(match.group(1)) / 10000000
                        self.log.error("Waiting for {}s".format(wait))
                        time.sleep(wait) #Wait for spam cooldown
                    else:
                        msg.error = str(error)
                        msg.save()
                        break
            prog += prog_step
            self.worker.set_progress(prog)

    def replace_placeholders(self, text, kill_info):
        name = kill_info.get("victim_name")
        ship = kill_info.get("victim_ship")
        kill_id = kill_info.get("id")
        kill_hash = kill_info.get("hash")
        killmail = "<url=killReport:{id}:{hash}>Kill: {name} - {ship}</url>".format(id=kill_id, hash=kill_hash, name=name, ship=ship)

        replaced = re.sub(r'%name%', name, text)
        replaced = re.sub(r'%ship%', ship, replaced)
        replaced = re.sub(r'%killmail%', killmail, replaced)

        return replaced
