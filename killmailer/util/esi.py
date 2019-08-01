from esipysi import EsiPysi, EsiAuth
from django.conf import settings
from urllib.error import HTTPError
import logging

class Esi():
    log = logging.getLogger(__name__)

    def __init__(self, request):
        access = request.session.get("access-token")
        refresh = request.session.get("refresh-token")
        self.auth = EsiAuth(settings.ESI_CLIENT, settings.ESI_SECRET, access, refresh, None)
        self.esi = EsiPysi("https://esi.evetech.net/_latest/swagger.json")
        self.char_id = None
        self.corp_id = None
        self.alliance_id = None
        self.in_alliance = None

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
            self.log.exception("An error ({}) occured with the ESI call \"{}\" with parameters: {}".format(result.status, op, parameters))
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






        