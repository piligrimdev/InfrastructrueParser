# -*- coding: utf-8 -*-
import pynetbox
from transliterate import translit, exceptions as translit_exceptions
from typing import Callable


class NetboxAPI:
    @staticmethod
    def display_id_map(response: list) -> dict:
        result = dict()
        if len(response) == 0:
            return result
        result["_default"] = response[0].id
        for dtype in response:
            result[dtype.display] = dtype.id
        return result

    @staticmethod
    def create_slug(name: str) -> str:
        try:
            name = translit(name, reversed=True)  # raises exception when passed latin string
        except translit_exceptions.LanguageDetectionError:
            pass
        result = ""
        for ch in name:
            if ch.isalpha() or ch.isdigit() or ch == '_' or ch == '-':
                result += ch
        return result

    def _setup_data(self):
        self.entities = dict()

        self.entities['manufacturers'] = NetboxAPI.display_id_map(list(self.nb.dcim.manufacturers.all()))
        if len(self.entities['manufacturers']) == 0:
            self.create_manufacturer('_default')

        self.entities['device_types'] = NetboxAPI.display_id_map(list(self.nb.dcim.device_types.all()))
        if len(self.entities['device_types']) == 0:
            self.create_device_type('_default', '_default')

        self.entities['sites'] = NetboxAPI.display_id_map(list(self.nb.dcim.sites.all()))
        if len(self.entities['sites']) == 0:
            self.create_site('_default')

        self.entities['locations'] = NetboxAPI.display_id_map(list(self.nb.dcim.locations.all()))
        if len(self.entities['locations']) == 0:
            self.create_location('_default', '_default')

        self.entities['racks'] = NetboxAPI.display_id_map(list(self.nb.dcim.racks.all()))
        if len(self.entities['racks']) == 0:
            self.create_rack_location('_default', '_default', "_default")

        self.entities['device_roles'] = NetboxAPI.display_id_map(list(self.nb.dcim.device_roles.all()))
        if len(self.entities['device_roles']) == 0:
            self.create_device_role('_default', True)

    def __init__(self, host, token):
        if token == "":
            pass
        self.nb = pynetbox.api(host, token=token)
        self._setup_data()

    def create_device(self, dtype: str, name: str, tag: str, role: str = None,
                      serial_number: str = None, locations: str = None,
                      rack_locations: str = None, custom_fields: dict = None) -> bool:

        if dtype not in self.entities['device_types'].keys():
            self.create_device_type(dtype, '_default')
            print(f"Created device type '{dtype}'")

        if not serial_number:
            serial_number = ""

        if not locations:
            locations = '_default'
        elif locations not in self.entities['locations'].keys():
            self.create_location(locations, '_default')
            print(f"Created location '{locations}'")

        if not rack_locations:
            rack_locations = '_default'
        elif rack_locations not in self.entities['racks'].keys():
            self.create_rack_location(rack_locations, '_default', locations)
            print(f"Created rack location '{rack_locations}'")

        if not role:
            role = '_default'
        elif role not in self.entities['device_roles'].keys():
            self.create_device_role(role, False)
            print(f"Created role '{role}'")

        obj = {
            "name": name,
            'device_type': self.entities['device_types'][dtype],
            "tag": tag,
            'role': self.entities['device_roles'][role],
            "serial_number": serial_number,
            "locations": self.entities['locations'][locations],
            "rack": self.entities['racks'][rack_locations],
            'site': self.entities['sites']['_default'],
            'status': 'active'
        }

        return self.create(obj, create_method=self.nb.dcim.devices.create, custom_fields=custom_fields)

    def create_location(self, name: str, site_key: str, custom_fields: dict = None) -> bool:
        obj = {
            "name": name,
            'slug': NetboxAPI.create_slug(name),
            'site': self.entities['sites'][site_key],
            'status': 'active'
        }
        return self.create(obj, self.nb.dcim.locations.create, 'locations', custom_fields)

    def create_device_role(self, name: str, apply_to_vms: bool, custom_fields: dict = None) -> bool:
        obj = {
            "name": name,
            'slug': NetboxAPI.create_slug(name),
            'vm_role': apply_to_vms
        }
        return self.create(obj, self.nb.dcim.device_roles.create, 'device_roles', custom_fields)

    def create_rack_location(self, name: str, site_key: str, location_key: str, custom_fields: dict = None) -> bool:
        obj = {
            "name": name,
            'slug': NetboxAPI.create_slug(name),
            'site': self.entities['sites'][site_key],
            'location': self.entities['locations'][location_key],
            'status': 'active'
        }
        return self.create(obj, self.nb.dcim.racks.create, 'racks', custom_fields)

    def create_device_type(self, name: str, manufacturer_key: str, custom_fields: dict = None):
        if not manufacturer_key:
            manufacturer_key = '_default'
        elif manufacturer_key not in self.entities['manufacturers'].keys():
            self.create_manufacturer(manufacturer_key)

        obj = {
            "model": name,
            'slug': NetboxAPI.create_slug(name),
            'manufacturer': self.entities['manufacturers'][manufacturer_key]
        }

        return self.create(obj, self.nb.dcim.device_types.create, 'device_types', custom_fields)

    def create_manufacturer(self, name: str, custom_fields: dict = None):
        obj = {
            "name": name,
            'slug': NetboxAPI.create_slug(name)
        }

        return self.create(obj, save_dict='manufacturers', create_method=self.nb.dcim.manufacturers.create,
                           custom_fields=custom_fields)

    def create_site(self, name: str, custom_fields: dict = None):
        obj = {
            "name": name,
            'slug': NetboxAPI.create_slug(name)
        }

        return self.create(obj, save_dict='sites', create_method=self.nb.dcim.sites.create,
                           custom_fields=custom_fields)

    def create(self, data: dict, create_method: Callable[[list[dict]], list], save_dict: str = None,
               custom_fields: dict = None) -> bool:

        if not custom_fields:
            custom_fields = {}
        data['custom_fields'] = custom_fields

        try:
            resp = create_method([data])[0]
            if save_dict:
                self.entities[save_dict][resp.display] = resp.id
            return True
        except Exception as e:
            print(e)
            return False
