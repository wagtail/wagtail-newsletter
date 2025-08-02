import requests

from .campaigns import APICampaigns
from .lists import APILists


class Client:
    def __init__(self, base: str, auth: requests.auth.HTTPBasicAuth):
        self.session = requests.Session()
        self.session.auth = auth
        self.base = base

    @property
    def lists(self) -> APILists:
        return APILists(self.base, self.session)

    @property
    def campaigns(self) -> APICampaigns:
        return APICampaigns(self.base, self.session)
