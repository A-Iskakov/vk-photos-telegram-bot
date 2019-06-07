from datetime import datetime, timedelta
from random import randint

import requests

from settings import VK_TOKEN, VK_API_VERSION, VK_API_OWNER_ID, VK_IDS


# PHOTO_SIZE_PRIORITY = ('w', 'z', 'y')
class VKApi:
    def __init__(self):
        self.albums = None
        self.last_update = datetime.now() - timedelta(days=1)

    def get_albums(self):
        difference = datetime.now() - self.last_update
        if difference.total_seconds() > 3600:
            params = {'owner_id': VK_API_OWNER_ID,
                      'access_token': VK_TOKEN,
                      'v': VK_API_VERSION,
                      'need_system': 1}
            result = requests.get('https://api.vk.com/method/photos.getAlbums', params)
            if result.status_code == 200:
                self.albums = result.json()
                return self.albums
            else:
                return None
        else:
            return self.albums

    def get_random_album_id(self):
        albums = self.get_albums()
        if albums:
            random_album = randint(0, albums['response']['count']-1)
            return albums['response']['items'][random_album]['id'], albums['response']['items'][random_album]['title']
        else:
            return None, None

    def get_photos_from_random_album(self):
        album_id, album_title = self.get_random_album_id()
        params = {'owner_id': VK_API_OWNER_ID,
                  'access_token': VK_TOKEN,
                  'v': VK_API_VERSION,
                  'count': 1000,
                  'extended': 1,
                  'album_id': album_id}
        result = requests.get('https://api.vk.com/method/photos.get', params)
        if result.status_code == 200:
            return result.json(), album_title
        else:
            return None, None

    def get_comments_from_photo(self, photo_id):
        params = {'owner_id': VK_API_OWNER_ID,
                  'access_token': VK_TOKEN,
                  'v': VK_API_VERSION,
                  'count': 100,
                  'extended': 1,
                  'photo_id': photo_id}
        result = requests.get('https://api.vk.com/method/photos.getComments', params)
        if result.status_code == 200:
            return result.json()['response']
        else:
            return None

    def search_list(self, list_of_dicts, query):
        for elem in list_of_dicts:
            if elem['id'] == query:
                if elem['first_name'] != 'DELETED':
                    result = elem['first_name']
                else:
                    check = VK_IDS.get(elem['id'], False)
                    if check:
                        result = check
                    else:
                        result = elem['id']
                return result

    def get_random_photo(self):
        photos, album_title = self.get_photos_from_random_album()
        if photos is not None:
            if 'response' in photos:
                random_photo_id = randint(0, photos['response']['count'] - 1)
                random_photo_info = photos['response']['items'][random_photo_id]
                index = -1
                max_photo = ('x', index)
                for item in reversed(random_photo_info['sizes']):
                    if item['type'] == 'w':
                        max_photo = ('w', index)
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
                caption = f"<i>Альбом</i> - <b>{album_title}</b>"
                if random_photo_info['text']:
                    caption += f"\n<b>{random_photo_info['text']}</b>\n"

                if random_photo_info['comments']['count'] > 0:
                    comments = self.get_comments_from_photo(random_photo_info['id'])
                    # profiles = DataFrame(comments['profiles'])
                    for comment in comments['items']:
                        caption += f"\n<b>{self.search_list(comments['profiles'], comment['from_id'])}</b>"
                        caption += f"\n<i>{comment['text']}</i>"

                    # print(profiles[profiles['id'] == comments['items'][0]['from_id']].to_dict('records'))

                return random_photo_info['sizes'][max_photo[1]]['url'], caption

        return None, None
