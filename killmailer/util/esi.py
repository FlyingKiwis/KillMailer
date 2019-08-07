from esipysi import EsiPysi, EsiAuth
from django.conf import settings
from urllib.error import HTTPError
import logging
import json

class Esi():
    log = logging.getLogger(__name__)

    def __init__(self, request, loop):
        access = request.session.get("access-token")
        refresh = request.session.get("refresh-token")
        self.auth = EsiAuth(settings.ESI_CLIENT, settings.ESI_SECRET, access, refresh, None)
        self.esi = EsiPysi("https://esi.evetech.net/_latest/swagger.json", loop=loop)
        self.char_id = None
        self.char_name = None
        self.corp_id = None
        self.alliance_id = None
        self.in_alliance = None

    def close(self):
        self.esi.close()

    async def __do_request(self, op, parameters={}):
        if op is None:
            self.log.error("No operation provided, did the ESI spec change?")
            return None
        if self.auth is not None:
            op.set_auth(self.auth)
        try:
            self.log.debug("Executing op \"{}\" with parameters: {}".format(op, parameters))
            result = await op.execute(**parameters)
        except HTTPError as e:
            self.log.exception("An error occured with the ESI call \"{}\" with parameters: {}".format(op, parameters))
            self.last_error = e
        except Exception:
            self.log.exception("An exception occured with a ESI call")
            pass
        else:
            self.log.debug("op \"{}\" with parameters: {} complete, result: {}".format(op, parameters, result.text))
            return result.json()
        return None

    async def get_char_id(self):
        if self.char_id is not None:
            return self.char_id
        verify = await self.auth.verify()
        self.char_id = verify.get("CharacterID")
        self.char_name = verify.get("CharacterName")
        return self.char_id

    async def get_char_name(self):
        if self.char_name is not None:
            return self.char_name
        verify = await self.auth.verify()
        self.char_id = verify.get("CharacterID")
        self.char_name = verify.get("CharacterName")
        return self.char_id


    async def is_hr(self):
        char_id = await self.get_char_id()
        op = self.esi.get_operation("get_characters_character_id_roles")
        results = await self.__do_request(op, {"character_id":char_id})
        if results is None:
            return False
        roles = results.get("roles", [])
        if "Personnel_Manager" in roles:
            return True
        return False
    
    async def get_corp_id(self):
        if self.corp_id is not None:
            return self.corp_id
        await self.load_affiliations()
        return self.corp_id

    async def get_alliance_id(self):
        if self.in_alliance is not None:
            return self.alliance_id
        await self.load_affiliations()
        return self.alliance_id

    async def is_in_alliance(self):
        if self.in_alliance is not None:
            return self.in_alliance
        await self.load_affiliations()
        return self.in_alliance

    async def load_affiliations(self):
        char_id = await self.get_char_id()
        op = self.esi.get_operation("post_characters_affiliation")
        results = await self.__do_request(op, {"characters":[char_id]})
        if len(results) != 1:
            return
        result = results[0]
        self.alliance_id = result.get("alliance_id")
        self.corp_id = result.get("corporation_id")
        if self.corp_id is not None:
            if self.alliance_id is None:
                self.in_alliance = False
            else:
                self.in_alliance = True
    
    async def get_kill_info(self, kill_id, kill_hash):
        op = self.esi.get_operation("get_killmails_killmail_id_killmail_hash")
        results = await self.__do_request(op, {"killmail_id":kill_id,"killmail_hash":kill_hash})
        if results is None:
            print("{} - {} is none".format(kill_id, kill_hash))
            return None
        vic = results.get("victim", {})
        char_id = vic.get("character_id")
        if char_id is None:
            print("char_id is none")
            return None
        ship_id = vic.get("ship_type_id")
        if ship_id is None:
            print("ship name is none")
            return None
        kill_time = results.get("killmail_time","")
        char_name = await self.get_character_name(char_id)
        ship_name = await self.get_type_name(ship_id)
        org_info = await self.get_org_info(char_id)
        details = {"id": kill_id, "hash":kill_hash,"victim_name":char_name,"victim_id":char_id,"victim_ship":ship_name, "victim_ship_id":ship_id,"victim_orgs":org_info,"kill_time":kill_time}
        return details

    async def get_character_name(self, character_id):
        op = self.esi.get_operation("get_characters_character_id")
        results = await self.__do_request(op, {"character_id":character_id})
        if results is None:
            return None
        return results.get("name")

    async def get_type_name(self, type_id):
        op = self.esi.get_operation("get_universe_types_type_id")
        results = await self.__do_request(op, {"type_id":type_id})
        if results is None:
            return None
        return results.get("name")

    async def get_org_info(self, character_id):
        op = self.esi.get_operation("post_characters_affiliation")
        results = await self.__do_request(op, {"characters":[character_id]})
        if len(results) != 1:
            return
        result = results[0]
        alliance_id = result.get("alliance_id")
        corp_id = result.get("corporation_id")
        ids = []
        ids.append(corp_id)
        if alliance_id is not None:
            ids.append(alliance_id)
        op = self.esi.get_operation("post_universe_names")
        results = await self.__do_request(op, {"ids":ids})
        if results is None:
            return {}
        org_info = {}
        for result in results:
            if result.get("category") == "alliance":
                org_info["alliance_id"] = result.get("id")
                org_info["alliance_name"] = result.get("name")
            elif result.get("category") == "corporation":
                org_info["corporation_id"] = result.get("id")
                org_info["corporation_name"] = result.get("name")
        return org_info
                

    async def send_mail(self, recipient_id, recipient_name, body, subject):
        #Form JSON
        recipients = []
        recipient_details = {}
        recipient_details["recipient_type"] = "character"
        recipient_details["recipient_id"] = recipient_id
        recipients.append(recipient_details)
        mail = {}
        mail["approved_cost"] = 0
        mail["body"] = body
        mail["recipients"] = recipients
        mail["subject"] = subject

        char_id = await self.get_char_id()
        op = self.esi.get_operation("post_characters_character_id_mail")
        results = await self.__do_request(op, {"character_id":char_id, "mail":mail})
        if results is None:
            return {"sent":False, "error":self.last_error}
        return {"sent":True}






        