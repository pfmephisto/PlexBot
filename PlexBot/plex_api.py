import logging
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount
from plexapi.audio import Audio
from plexapi.exceptions import NotFound

logger = logging.getLogger(__name__)


class Plex():

    def __init__(self, **kwargs):
        """Fetches and returns this thing

        :param token:
            This is the token for the user account
        :type token: ``str``

        :param username:
            This is the username of the account
        :type token: ``str``

        :param password:
            This is the password for the account
        :type token: ``str``

        :param server:
            This is the server to be used.
        :type token: ``str``
        """

        self.token = kwargs.get('token')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.server = kwargs.get('server')

        self.plex: PlexServer = None
        self.music = None  # Music library

        if not self.token:
            self._connect_to_server_lognin()
        else:
            self._connect_to_server_token()

    def find_music(self, serach, num_Results=10, LibraryName=None):
        if not LibraryName and self.music is None:
            self._set_default_music_library()
        elif LibraryName:
            self.music = self.plex.library.section(str(LibraryName))

        if self.music is None:
            raise Exception('No library selected')

        results = [song for song in
                   self.music.search(str(serach),
                                     maxresults=int(num_Results))]
        return results[:num_Results]

    def currently_playing(self) -> Audio:

        sessions = self.plex.sessions()

        currently_playing = []

        for session in sessions:
            if session.TAG == 'Track':
                currently_playing.append(session)

            # check if any sone is currently playing
            if len(currently_playing) != 0:
                return currently_playing

        # in case nothing is playing return None
        return None

    def get_token(self) -> str:
        try:
            return str(self.plex._token)
        except NotFound as e:
            logger.debug('Unable to log in: %s', e.msg)
            return None

    def _set_default_music_library(self):

        # All music sections
        musicSections = [MusicSection for MusicSection in
                         self.plex.library.sections() if
                         type(MusicSection).__name__ == 'MusicSection']

        if len(musicSections) != 0:
            # Sort list by library size
            musicSections.sort(key=lambda x: x.totalSize, reverse=True)

            # Select largest music library
            self.music = musicSections[0]

            # LibraryName = music.title
        else:
            raise Exception('Server does not contain a music library')

    def _connect_to_server_lognin(self):
        # Check if the device name can becostomized
        account = MyPlexAccount(str(self.username), str(self.password))
        # returns a PlexServer instance
        self.plex = account.resource(str(self.server)).connect()
        # return plex, plex.authToken

    def _connect_to_server_token(self):
        account = MyPlexAccount(token=self.token)
        self.plex = account.resource(str(self.server)).connect()
