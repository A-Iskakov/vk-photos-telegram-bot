

import requests

from settings import VK_TOKEN, VK_API_VERSION, VK_API_OWNER_ID
from random import randint
PHOTO_SIZE_PRIORITY = ('w', 'z', 'y')
class VKApi:
    def __init__(self):
        pass

    def get_albums(self):
        params = {'owner_id': VK_API_OWNER_ID,
                  'access_token': VK_TOKEN,
                  'v': VK_API_VERSION,
                  'need_system': 1}
        result = requests.get('https://api.vk.com/method/photos.getAlbums', params)
        if result.status_code == 200:
            return result.json()
        else:
            return None

    def get_random_album_id(self):
        albums = self.get_albums()
        if albums:
            random_album = randint(0, albums['response']['count']-1)
            return albums['response']['items'][random_album]['id']
        else:
            return None

    def get_photos_from_random_album(self):
        params = {'owner_id': VK_API_OWNER_ID,
                  'access_token': VK_TOKEN,
                  'v': VK_API_VERSION,
                  'count': 1000,
                  'album_id': self.get_random_album_id()}
        result = requests.get('https://api.vk.com/method/photos.get', params)
        if result.status_code == 200:
            return result.json()
        else:
            return None

    def get_random_photo(self):
        photos = self.get_photos_from_random_album()
        if photos:
            random_photo_id = randint(0, photos['response']['count']-1)
            random_photo_info = photos['response']['items'][random_photo_id]
            index = -1
            max_photo = ('x', index)
            for item in reversed(random_photo_info['sizes']):
                if item['type'] == 'w':
                    max_photo  = ('w', index)
                    break
                if item['type'] == 'z':
                    max_photo = ('z', index)
                    index -= 1
                    continue
                if item['type'] == 's':
                    break

                if item['type'] == 'y' and max_photo[0] != 'z':
                    max_photo = ('y', index)
                    index -= 1
                    continue
                if item['type'] == 'x' and max_photo[0] != 'z' and max_photo[0] != 'y':
                    max_photo = ('x', index)
                    index -= 1
                    continue
                index -= 1
            # pprint(random_photo_info['sizes'])
            # return  max_photo

            return random_photo_info['sizes'][max_photo[1]]['url'], random_photo_info['text']
        else:
            return None, None
