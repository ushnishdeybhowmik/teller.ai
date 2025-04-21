import geocoder

class Geolocation:
    def __init__(self):
        self.g = geocoder.ip('me')

    def get_location(self):
        return self.g.latlng[0], self.g.latlng[1]
    
    def set_location(self):
        self.g = geocoder.ip('me')