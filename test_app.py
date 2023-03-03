import unittest
from unittest.mock import MagicMock, patch
from app import *

class TestUniverse(unittest.TestCase):
  def setUp(self):
      pass

  def tearDown(self):
      pass
  
  def test_universe_get_random_player(self):
    player = PokemonPlayer(1, "bulbasaur", 67, 7)
    mock_requestor = MagicMock()
    mock_requestor.getPlayerById.return_value = player
    factory = PlayerFactory(mock_requestor)
    factory._getRandomId = MagicMock()
    factory._getRandomId.return_value = 1
    universe = Universe(factory)
    self.assertEqual(universe.getRandomPlayer(), player)
    mock_requestor.getPlayerById.assert_called_once_with(1)

class TestPlayer(unittest.TestCase):
  def setUp(self):
      pass

  def tearDown(self):
      pass
  
  def test_pokemon_player(self):
    player = PokemonPlayer(1, "bulbasaur", 67, 7)
    self.assertEqual(player.id, 1)
    self.assertEqual(player.name, "bulbasaur")
    self.assertEqual(player.weight, 67)
    self.assertEqual(player.height, 7)

  def test_pokemon_player_repr(self):
    player = PokemonPlayer(1, "bulbasaur", 67, 7)
    self.assertEqual(player.__repr__(), "Pokemon(id=1,name=bulbasaur,weight=67,height=7)") 

  def test_starwars_player(self):
    player = StarWarsPlayer(1, "Luke Skywalker", 77, 172)
    self.assertEqual(player.id, 1)
    self.assertEqual(player.name, "Luke Skywalker")
    self.assertEqual(player.weight, 77)
    self.assertEqual(player.height, 172)

  def test_starwars_player_repr(self):
    player = StarWarsPlayer(1, "Luke Skywalker", 77, 172)
    self.assertEqual(player.__repr__(), "StarWars(id=1,name=Luke Skywalker,weight=77,height=172)") 

class TestResponseConverter(unittest.TestCase):
  def setUp(self):
      pass

  def tearDown(self):
      pass

  def test_pokemon_response_converter_to_count(self):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
      "count": 1279
    }  
    converter = PokemonResponseConverter()
    count = converter.toCount(mock_response)
    self.assertEqual(count, 1279)
    
  def test_pokemon_response_converter_to_player(self):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
      "name": "bulbasaur",
      "weight": 67,
      "height": 7,
    }  
    converter = PokemonResponseConverter()
    player = converter.toPlayer(1, mock_response)
    self.assertEqual(player.id, 1)
    self.assertEqual(player.name, "bulbasaur")
    self.assertEqual(player.weight, 67)
    self.assertEqual(player.height, 7)

  def test_starwars_response_converter_to_count(self):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
      "count": 82
    }  
    converter = StarWarsResponseConverter()
    count = converter.toCount(mock_response)
    self.assertEqual(count, 82)

  def test_starwars_response_converter_to_player(self):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
      "name": "Luke Skywalker",
      "mass": "77",
      "height": "172",
    }  
    converter = StarWarsResponseConverter()
    player = converter.toPlayer(1, mock_response)
    self.assertEqual(player.id, 1)
    self.assertEqual(player.name, "Luke Skywalker")
    self.assertEqual(player.weight, 77)
    self.assertEqual(player.height, 172)
      
class TestCache(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_dict_cache_return_player(self):
    cache = DictCache()
    player = PokemonPlayer(1, "bulbasaur", 67, 7)
    cache.setItem(1, player)
    self.assertEqual(cache.getItem(1), player)

  def test_dict_cache_return_none(self):
    cache = DictCache()
    player = PokemonPlayer(1, "bulbasaur", 67, 7)
    cache.setItem(1, player)
    self.assertIsNone(cache.getItem(2))

class TestPlayerRequestor(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_pokemon_player_requestor_return_cached_player(self):
    player = PokemonPlayer(1, "bulbasaur", 67, 7)

    mock_converter = MagicMock()
   
    mock_cache = MagicMock()
    mock_cache.getItem.return_value = player

    requestor = PokemonPlayerRequestor('https://pokeapi.co', mock_converter, mock_cache)
    self.assertEqual(requestor.getPlayerById(1), player)
    mock_cache.getItem.assert_called_once_with(1)

  def test_starwars_player_requestor_return_cached_player(self):
    player = StarWarsPlayer(1, "Luke Skywalker", 77, 172)

    mock_converter = MagicMock()
   
    mock_cache = MagicMock()
    mock_cache.getItem.return_value = player

    requestor = PokemonPlayerRequestor('https://swapi.dev', mock_converter, mock_cache)
    self.assertEqual(requestor.getPlayerById(1), player)
    mock_cache.getItem.assert_called_once_with(1)

  @patch('app.requests')
  def test_pokemon_player_requestor_raise_exception(self, mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_requests.Session().__enter__().get().__enter__.return_value = mock_response
   
    mock_converter = MagicMock()
   
    mock_cache = MagicMock()
    mock_cache.getItem.return_value = None

    requestor = PokemonPlayerRequestor('https://pokeapi.co', mock_converter, mock_cache)
    self.assertRaises(InvalidPlayerIdException, requestor.getPlayerById, 1)

  @patch('app.requests')
  def test_starwars_player_requestor_raise_exception(self, mock_requests):
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_requests.Session().__enter__().get().__enter__.return_value = mock_response
   
    mock_converter = MagicMock()
   
    mock_cache = MagicMock()
    mock_cache.getItem.return_value = None

    requestor = StarWarsPlayerRequestor('https://swapi.dev', mock_converter, mock_cache)
    self.assertRaises(InvalidPlayerIdException, requestor.getPlayerById, 1)

class TestPlayerFactory(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_player_factory_random_id(self):
    player = PokemonPlayer(1, "bulbasaur", 67, 7)

    mock_requestor = MagicMock()
    mock_requestor.getPlayerById.return_value = player

    factory = PlayerFactory(mock_requestor)
    factory._getRandomId = MagicMock()
    factory._getRandomId.return_value = 1

    self.assertEqual(factory.createPlayer(), player)
    factory._getRandomId.assert_called_once()
    mock_requestor.getPlayerById.assert_called_once_with(1)

class TestTeam(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_team_roles(self):
    players = [
      PokemonPlayer(id=723, name="dartrix", weight=160, height=7),
      PokemonPlayer(id=959, name="tinkaton", weight=1128, height=7),
      PokemonPlayer(id=253, name="grovyle", weight=216, height=9),
      PokemonPlayer(id=577, name="solosis", weight=10, height=3),
      PokemonPlayer(id=71, name="victreebel", weight=155, height=17)
    ]

    team = Team(players)

    self.assertEqual(team.getGoalie(), players[4])
    self.assertListEqual(team.getDefense(), [players[1], players[2]])
    # self.assertCountEqual(team.getDefense(), [players[1], players[2]])
    self.assertListEqual(team.getOffense(), [players[3], players[0]])
    # self.assertCountEqual(team.getOffense(), [players[0], players[3]])

class TestTeamFactory(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_team_factory_default_size(self):
    player = PokemonPlayer(1, "bulbasaur", 67, 7)

    mock_universe = MagicMock()
    mock_universe.getRandomPlayer.return_value = player

    factory = TeamFactory(mock_universe)
    team = factory.createTeam()

    self.assertListEqual(team._players, [player for _ in range(5)])
    self.assertEqual(mock_universe.getRandomPlayer.call_count, 5)

  def test_team_factory_custom_size(self):
    player = PokemonPlayer(1, "bulbasaur", 67, 7)

    mock_universe = MagicMock()
    mock_universe.getRandomPlayer.return_value = player

    factory = TeamFactory(mock_universe)
    team = factory.createTeam(10)

    self.assertListEqual(team._players, [player for _ in range(10)])
    self.assertEqual(mock_universe.getRandomPlayer.call_count, 10)