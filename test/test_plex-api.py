import os
from dotenv import load_dotenv
from src.plex_api import Plex

load_dotenv()
plex = None


def test_log_in():
    plex = Plex(username=str(os.getenv('USERNAME')),
                password=str(os.getenv('PASSWORD')),
                server=str(os.getenv('SERVER')))
    assert plex is not None


def test_login_using_token():
    plex = Plex(token=str(os.getenv('PLEX_TOKEN')),
                server=str(os.getenv('SERVER')))
    assert plex is not None


def test_find_song():
    plex = Plex(username=str(os.getenv('USERNAME')),
                password=str(os.getenv('PASSWORD')),
                server=str(os.getenv('SERVER')))
    song = plex.find_music('No Respect')
    assert song is not None


def test_get_token():
    pass
