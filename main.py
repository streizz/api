import pygame
import requests
import sys
import os
import math

from distance import lonlat_distance
from geo import reverse_geocode

lat_step = 0.008
lon_step = 0.02
coord_to_geo_x = 0.0000428
coord_to_geo_y = 0.0000428


def ll(x, y):
    return "{0},{1}".format(x, y)


class SearchResults(object):
    def __init__(self, point, address, postal_code=None) -> None:
        self.point = point
        self.address = address
        self.postal_code = postal_code


class mapParams(object):
    def __init__(self) -> None:

        self.lat = 55.729738
        self.lon = 37.664777
        self.zoom = 15
        self.type = "map"

        self.search_results = None
        self.use_postal_code = False

    def ll(self):
        return ll(self.lon, self.lat)

    def update(self, event):
        print(event.key)
        if event.key == 1073741899 and self.zoom < 19:  # PG_UP
            self.zoom += 1
        elif event.key == 1073741902 and self.zoom > 2:  # PG_DOWN
            self.zoom -= 1
        elif event.key == 1073741904:  # LEFT_ARROW
            self.lon -= lon_step * math.pow(2, 15 - self.zoom)
        elif event.key == 1073741903:  # RIGHT_ARROW
            self.lon += lon_step * math.pow(2, 15 - self.zoom)
        elif event.key == 1073741906 and self.lat < 85:  # UP_ARROW
            self.lat += lat_step * math.pow(2, 15 - self.zoom)
        elif event.key == 1073741905 and self.lat > -85:  # DOWN_ARROW
            self.lat -= lat_step * math.pow(2, 15 - self.zoom)
        elif event.key == 49:  # 1
            self.type = "map"
        elif event.key == 50:  # 2
            self.type = "sat"
        elif event.key == 51:  # 3
            self.type = "sat,skl"
        elif event.key == 127:  # DELETE
            self.search_result = None
        elif event.key == 1073741897:  # INSERT
            self.use_postal_code = not self.use_postal_code

        if self.lon > 180:
            self.lon -= 360
        if self.lon < -180:
            self.lon += 360

    def screen_to_geo(self, pos):
        dy = 225 - pos[1]
        dx = pos[0] - 300
        lx = self.lon + dx * coord_to_geo_x * math.pow(2, 15 - self.zoom)
        ly = self.lat + dy * coord_to_geo_y * math.cos(math.radians(self.lat)) * math.pow(2,
                                                                                          15 - self.zoom)
        print(self.lon, self.lat, lx, ly, dx, dy)
        return lx, ly

    def add_reverse_toponym_search(self, pos):
        point = self.screen_to_geo(pos)
        toponym = reverse_geocode(ll(point[0], point[1]))
        if toponym:
            self.search_result = SearchResults(point, toponym["metaDataProperty"]["GeocoderMetaData"]["text"],
                                               toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code"))
        else:
            self.search_result = SearchResults(point, None, None)


def load_map(mp):
    map_request = "http://static-maps.yandex.ru/1.x/?ll={ll}&z={z}&l={type}".format(ll=mp.ll(),
                                                                                    z=mp.zoom,
                                                                                    type=mp.type)
    if mp.search_result:
        map_request += "&pt={0},{1},pm2grm".format(mp.search_result.point[0],
                                                   mp.search_result.point[1])

    response = requests.get(map_request)
    if not response:
        print("Ошибка выполнения запроса:")
        print(map_request)
        print("Http статус:", response.status_code, "(", response.reason, ")")
        sys.exit(1)

    map_file = "map.png"
    try:
        with open(map_file, "wb") as file:
            file.write(response.content)
    except IOError as ex:
        print("Ошибка записи временного файла:", ex)
        sys.exit(2)

    return map_file


def render_text(text):
    font = pygame.font.Font(None, 30)
    return font.render(text, 1, (100, 0, 100))


def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 450))

    mp = mapParams()

    while True:
        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            break
        elif event.type == pygame.KEYUP:
            mp.update(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mp.add_reverse_toponym_search(event.pos)
        else:
            continue

        map_file = load_map(mp)

        screen.blit(pygame.image.load(map_file), (0, 0))

        if mp.search_result:
            if mp.use_postal_code and mp.search_result.postal_code:
                text = render_text(
                    mp.search_result.postal_code + ", " + mp.search_result.address)
            else:
                text = render_text(mp.search_result.address)
            screen.blit(text, (20, 400))

        pygame.display.flip()

    pygame.quit()
    os.remove(map_file)


if __name__ == "__main__":
    main()
