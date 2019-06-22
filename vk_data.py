from datetime import datetime, timedelta
from random import randint
from time import sleep

import requests

from settings import VK_TOKEN, VK_API_VERSION, VK_API_OWNER_ID, VK_IDS, MY_ALBUMS


# PHOTO_SIZE_PRIORITY = ('w', 'z', 'y')
class VKApi:
    def __init__(self):
        self.albums = None
        self.last_update = datetime.now() - timedelta(days=1)
        self.photos = {}

    def get_albums(self):
        difference = datetime.now() - self.last_update
        if difference.total_seconds() > 3600 * 23:
            params = {'owner_id': VK_API_OWNER_ID,
                      'access_token': VK_TOKEN,
                      'v': VK_API_VERSION,
                      'need_system': 1}
            result = requests.get('https://api.vk.com/method/photos.getAlbums', params)
            if result.status_code == 200:
                if 'response' in result.json():
                    self.albums = result.json()
                    for album in MY_ALBUMS:
                        self.albums['response']['items'].append(album)
                    self.albums['response']['count'] += 3
                    self.last_update = datetime.now()
                    self.photos = {}
                else:
                    sleep(1)
                    return self.get_albums()

    def get_random_album_id(self):
        self.get_albums()
        if self.albums is not None:
            try:
                random_album = randint(0, self.albums['response']['count'] - 1)
            except KeyError:
                print(self.albums)
                raise

            return self.albums['response']['items'][random_album]['id'], self.albums['response']['items'][random_album][
                'title'], self.albums['response']['items'][random_album]['owner_id']

        else:
            return None, None

    def get_photos_from_random_album(self):
        album_id, album_title, owner_id = self.get_random_album_id()
        if album_id not in self.photos:
            params = {'owner_id': owner_id,
                      'access_token': VK_TOKEN,
                      'v': VK_API_VERSION,
                      'count': 1000,
                      'extended': 1,
                      'album_id': album_id}
            result = requests.get('https://api.vk.com/method/photos.get', params)
            if result.status_code == 200:
                # print('got new photos')
                if 'response' in result.json():
                    self.photos.update({album_id: result.json()})
                    return result.json(), album_title
                else:
                    sleep(1)
                    return self.get_photos_from_random_album()
            else:
                return None, None
        else:
            return self.photos[album_id], album_title

    def get_comments_from_photo(self, photo_id, owner_id):
        params = {'owner_id': owner_id,
                  'access_token': VK_TOKEN,
                  'v': VK_API_VERSION,
                  'count': 100,
                  'extended': 1,
                  'photo_id': photo_id}
        result = requests.get('https://api.vk.com/method/photos.getComments', params)
        if result.status_code == 200:
            if 'response' in result.json():
                return result.json()['response']
            else:
                sleep(1)
                return self.get_comments_from_photo(photo_id, owner_id)
        else:
            return None

    def create_comment_on_photo(self, photo_id, owner_id, access_token, comment):
        params = {'owner_id': owner_id,
                  'access_token': access_token,
                  'v': VK_API_VERSION,
                  'message': comment,
                  'photo_id': photo_id}
        result = requests.post('https://api.vk.com/method/photos.createComment', params)
        if result.status_code == 200:
            result_dict = result.json()
            if 'response' in result_dict:
                if type(result_dict['response']) == int:
                    return True
                else:
                    return False
            if 'error' in result_dict:
                return False
            else:
                sleep(1)
                return self.create_comment_on_photo(photo_id, owner_id, access_token, comment)
        else:
            return None

    def search_comment_author_from_list(self, list_of_dicts, query):
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

                caption = f"{random_photo_info['id']}@ Альбом - {album_title}"
                if random_photo_info['text']:
                    caption += f"\n{random_photo_info['text']}"

                if random_photo_info['comments']['count'] > 0:
                    comments = self.get_comments_from_photo(random_photo_info['id'], random_photo_info['owner_id'])
                    # profiles = DataFrame(comments['profiles'])
                    for comment in comments['items']:
                        caption += f"\n{self.search_comment_author_from_list(comments['profiles'], comment['from_id'])}"
                        caption += f"\n{comment['text']}"

                    # print(profiles[profiles['id'] == comments['items'][0]['from_id']].to_dict('records'))

                return random_photo_info['sizes'][max_photo[1]]['url'], caption

        return None, None
