# -*- coding: utf-8 -*-
from unittest import TestCase

from mock import mock

from astrobox.cargo_box import CargoBox
from robogame_engine.geometry import Point
from robogame_engine.theme import theme


class CargoBoxVehicle(CargoBox):

    def __init__(self, coord, *args, **kwargs):
        super(CargoBoxVehicle, self).__init__(*args, **kwargs)
        self.coord = coord
        self.on_load_complete = mock.MagicMock()
        self.on_unload_complete = mock.MagicMock()


class TestCargo(TestCase):

    def setUp(self):
        theme.set_theme_module(mod_path='tests.themes.for_cargo_box')
        self.initial_cargo = 50
        self.maximum_cargo = 100
        self.half_load_speed = theme.LOAD_SPEED // 2
        self.unit1 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=self.initial_cargo, maximum_cargo=self.maximum_cargo)
        self.unit2 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=self.initial_cargo, maximum_cargo=self.maximum_cargo)

    def test_propeties(self):
        self.assertEqual(self.unit1.payload, self.initial_cargo)
        self.assertFalse(self.unit1.is_full)
        self.assertFalse(self.unit1.is_empty)
        self.assertEqual(self.unit1.free_space, self.maximum_cargo - self.initial_cargo)
        self.assertEqual(self.unit1.fullness, .5)
        self.unit1 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=self.maximum_cargo, maximum_cargo=self.maximum_cargo)
        self.assertTrue(self.unit1.is_full)
        self.assertFalse(self.unit1.is_empty)
        self.assertEqual(self.unit1.free_space, 0)
        self.assertEqual(self.unit1.fullness, 1.0)
        self.unit1 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=0, maximum_cargo=self.maximum_cargo)
        self.assertFalse(self.unit1.is_full)
        self.assertTrue(self.unit1.is_empty)
        self.assertEqual(self.unit1.free_space, self.maximum_cargo)
        self.assertEqual(self.unit1.fullness, 0.0)

    def test_load(self):
        self.unit1.load_from(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo + theme.LOAD_SPEED)
        self.assertEqual(self.unit2.payload, self.initial_cargo - theme.LOAD_SPEED)
        self.assertEqual(self.unit1.on_load_complete.call_count, 0)

    def test_load_from_empty(self):
        self.unit2 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=0, maximum_cargo=self.maximum_cargo)
        self.unit1.load_from(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo)
        self.assertEqual(self.unit2.payload, 0)
        self.assertEqual(self.unit1.on_load_complete.call_count, 1)

    def test_load_from_nearly_empty(self):
        self.unit2 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=self.half_load_speed, maximum_cargo=self.maximum_cargo)
        self.unit1.load_from(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo + self.half_load_speed)
        self.assertEqual(self.unit2.payload, 0)
        self.assertEqual(self.unit1.on_load_complete.call_count, 1)

    def test_load_to_full(self):
        self.unit1 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=self.maximum_cargo, maximum_cargo=self.maximum_cargo)
        self.unit1.load_from(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.maximum_cargo)
        self.assertEqual(self.unit2.payload, self.initial_cargo)
        self.assertEqual(self.unit1.on_load_complete.call_count, 1)

    def test_load_to_almost_full(self):
        half_load_speed = theme.LOAD_SPEED // 2
        self.unit1 = CargoBoxVehicle(
            coord=Point(0, 0),
            initial_cargo=self.maximum_cargo - half_load_speed,
            maximum_cargo=self.maximum_cargo)
        self.unit1.load_from(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.maximum_cargo)
        self.assertEqual(self.unit2.payload, self.initial_cargo - half_load_speed)

    def test_unload(self):
        self.unit1.unload_to(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo - theme.LOAD_SPEED)
        self.assertEqual(self.unit2.payload, self.initial_cargo + theme.LOAD_SPEED)
        self.assertEqual(self.unit1.on_unload_complete.call_count, 0)

    def test_unload_from_empty(self):
        self.unit1 = CargoBoxVehicle(coord=Point(0, 0), initial_cargo=0, maximum_cargo=self.maximum_cargo)
        self.unit1.unload_to(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, 0)
        self.assertEqual(self.unit2.payload, self.initial_cargo)
        self.assertEqual(self.unit1.on_unload_complete.call_count, 1)

    def test_unload_from_nearly_empty(self):
        self.unit1 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=self.half_load_speed, maximum_cargo=self.maximum_cargo)
        self.unit1.unload_to(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, 0)
        self.assertEqual(self.unit2.payload, self.initial_cargo + self.half_load_speed)
        self.assertEqual(self.unit1.on_unload_complete.call_count, 1)

    def test_unload_to_full(self):
        self.unit2 = CargoBoxVehicle(
            coord=Point(0, 0), initial_cargo=self.maximum_cargo, maximum_cargo=self.maximum_cargo)
        self.unit1.unload_to(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo)
        self.assertEqual(self.unit2.payload, self.maximum_cargo)
        self.assertEqual(self.unit1.on_unload_complete.call_count, 1)

    def test_unload_to_almost_full(self):
        self.unit2 = CargoBoxVehicle(
            coord=Point(0, 0),
            initial_cargo=self.maximum_cargo - self.half_load_speed,
            maximum_cargo=self.maximum_cargo
        )
        self.unit1.unload_to(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo - self.half_load_speed)
        self.assertEqual(self.unit2.payload, self.maximum_cargo)
        self.assertEqual(self.unit1.on_unload_complete.call_count, 1)

    def test_big_distance(self):
        self.unit2 = CargoBoxVehicle(
            coord=Point(theme.LOAD_DISTANCE, 0),
            initial_cargo=self.initial_cargo,
            maximum_cargo=self.maximum_cargo
        )
        self.unit1.load_from(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo)
        self.assertEqual(self.unit2.payload, self.initial_cargo)
        self.assertEqual(self.unit1.on_load_complete.call_count, 0)
        self.unit1.unload_to(self.unit2)
        self.unit1.game_step()
        self.assertEqual(self.unit1.payload, self.initial_cargo)
        self.assertEqual(self.unit2.payload, self.initial_cargo)
        self.assertEqual(self.unit1.on_unload_complete.call_count, 0)
