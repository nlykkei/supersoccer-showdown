from __future__ import annotations
import abc
import requests
import random
import locale

locale.setlocale(locale.LC_ALL, "")

class InvalidPlayerIdException(Exception):
  pass

class Universe:
  def __init__(self, playerFactory: PlayerFactory) -> None:
    self.playerFactory = playerFactory 

  def getRandomPlayer(self) -> Player:
    return self.playerFactory.createPlayer()

class Player(abc.ABC):
  def __init__(self, id: int, name: str, weight: float, height: float) -> None:
    self.id = id
    self.name = name
    self.weight = weight
    self.height = height

  @abc.abstractmethod
  def __repr__(self) -> str:
    pass

class PokemonPlayer(Player):
  def __init__(self, id: int, name: str, weight: float, height: float) -> None:
    super().__init__(id, name, weight, height)    

  def __repr__(self) -> str:
    return f'Pokemon(id={self.id},name={self.name},weight={self.weight},height={self.height})'

class StarWarsPlayer(Player):
  def __init__(self, id: int, name: str, weight: float, height: float) -> None:
    super().__init__(id, name, weight, height)    

  def __repr__(self) -> str:
    return f'StarWars(id={self.id},name={self.name},weight={self.weight},height={self.height})'

class ResponseConverter(abc.ABC):
  @abc.abstractmethod
  def toPlayer(self, id: int, res: requests.Response) -> Player:
    pass

  @abc.abstractmethod
  def toCount(self, res: requests.Response) -> int:
    pass

class PokemonResponseConverter(ResponseConverter):
  def __init__(self):
    pass

  def toPlayer(self, id: int, res: requests.Response) -> Player:
    json = res.json() 
    return PokemonPlayer(id=id, 
                         name=json["name"], 
                         weight=json["weight"], 
                         height=json["height"])

  def toCount(self, res: requests.Response) -> int:
    json = res.json()
    return json["count"]  

class StarWarsResponseConverter(ResponseConverter):
  def __init__(self):
    pass

  def toPlayer(self, id: int, res: requests.Response) -> Player:
    json = res.json() 
    return StarWarsPlayer(id=id, 
                          name=json["name"], 
                          weight=locale.atof(json["mass"]) if json["mass"] != "unknown" else 0, 
                          height=locale.atof(json["height"]) if json["height"] != "unknown" else 0)

  def toCount(self, res: requests.Response) -> int:
    json = res.json()
    return json["count"]

class Cache(abc.ABC):
  def getItem(self, key: any) -> any:
    pass

  def setItem(self, key: any, val: any):
    pass

class DictCache(Cache):
  def __init__(self):
    self.cache = {}

  def getItem(self, key: int) -> Player | None:
    return self.cache.get(key, None)

  def setItem(self, key: int, val: Player):
    self.cache[key] = val 

class PlayerRequestor(abc.ABC):
  def __init__(self, url: str, converter: ResponseConverter, cache: Cache) -> None:
    self.url = url
    self.converter = converter
    self.cache = cache

  @abc.abstractmethod
  def getPlayerCount(self) -> int:
    pass

  @abc.abstractmethod
  def getPlayerById(self, id: int) -> Player:
    pass

class PokemonPlayerRequestor(PlayerRequestor):
  def __init__(self, url: str, converter: ResponseConverter, cache: Cache) -> None:
    super().__init__(url, converter, cache)

  def getPlayerCount(self) -> int:
    with requests.Session() as rs:
      rs.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=requests.urllib3.Retry(total=5, connect=5, read=5, backoff_factor=1)))
      with rs.get(f'{self.url}/api/v2/pokemon/', verify=True) as r:
        r.raise_for_status()
        count = self.converter.toCount(r)
        return count

  def getPlayerById(self, id: int) -> Player:
    cachedPlayer = self.cache.getItem(id)
    if cachedPlayer is not None:
      return cachedPlayer
    with requests.Session() as rs:
      rs.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=requests.urllib3.Retry(total=5, connect=5, read=5, backoff_factor=1)))
      with rs.get(f'{self.url}/api/v2/pokemon/{id}', verify=True) as r:
        if r.status_code == 404:
          raise InvalidPlayerIdException
        r.raise_for_status()
        player = self.converter.toPlayer(id, r)
        self.cache.setItem(id, player)
        return player

class StarWarsPlayerRequestor(PlayerRequestor):
  def __init__(self, url: str, converter: ResponseConverter, cache: Cache) -> None:
    super().__init__(url, converter, cache)

  def getPlayerCount(self) -> int:
    with requests.Session() as rs:
      rs.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=requests.urllib3.Retry(total=5, connect=5, read=5, backoff_factor=1)))
      with rs.get(f'{self.url}/api/people/', verify=True) as r:
        r.raise_for_status()
        count = self.converter.toCount(r)
        return count     

  def getPlayerById(self, id: int) -> Player:
    cachedPlayer = self.cache.getItem(id)
    if cachedPlayer is not None:
      return cachedPlayer
    with requests.Session() as rs:
      rs.mount('https://', requests.adapters.HTTPAdapter(
        max_retries=requests.urllib3.Retry(total=5, connect=5, read=5, backoff_factor=1)))
      with rs.get(f'{self.url}/api/people/{id}', verify=True) as r:
        if r.status_code == 404:
          raise InvalidPlayerIdException
        r.raise_for_status()
        player = self.converter.toPlayer(id, r)
        self.cache.setItem(id, player)
        return player

class PlayerFactory:
  def __init__(self, playerRequestor: PlayerRequestor) -> None:
    self.playerRequestor = playerRequestor
    self.playerCount = None

  def _getRandomId(self) -> int:
    if self.playerCount is None:
      self.playerCount = self.playerRequestor.getPlayerCount()
    return random.choice(range(self.playerCount)) + 1

  def createPlayer(self, id : int | None = None) -> Player:
    if id is None:
      id = self._getRandomId()
    while True:
      try:
        return self.playerRequestor.getPlayerById(id)
      except InvalidPlayerIdException:
        id = self._getRandomId()

class PokemonPlayerFactory(PlayerFactory):
  def __init__(self):
    super().__init__(PokemonPlayerRequestor('https://pokeapi.co', PokemonResponseConverter(), DictCache()))

class StarWarsPlayerFactory(PlayerFactory):
  def __init__(self):
    super().__init__(StarWarsPlayerRequestor('https://swapi.dev', StarWarsResponseConverter(), DictCache()))
    
class Team:
  def __init__(self, players: list[Player]) -> None:
    self._players = players
    self._goalie = None
    self._defense = None
    self._offense = None

  def getGoalie(self):
    if self._goalie is None:
      self._goalie = sorted(self._players, key=lambda player: player.height, reverse=True)[0]
    return self._goalie

  def getDefense(self):
    if self._defense is None:
      self._defense = sorted(self._players, key=lambda player: player.weight, reverse=True)[:2]
    return self._defense

  def getOffense(self):
    if self._offense is None:
      self._offense = sorted(self._players, key=lambda player: player.height)[:2]
    return self._offense
  
  def __repr__(self) -> str:
    return f'Team(players={self._players})'  

class TeamFactory:
  def __init__(self, universe: Universe):
    self.universe = universe

  def createTeam(self, size: int = 5) -> Team:
    players = []
    for _ in range(size):
      player = self.universe.getRandomPlayer()
      players.append(player)
    return Team(players)

class PokemonTeamFactory(TeamFactory):
  def __init__(self):
    super().__init__(Universe(StarWarsPlayerFactory()))

class StarWarsTeamFactory(TeamFactory):
  def __init__(self):
    super().__init__(Universe(StarWarsPlayerFactory()))
    
def main():
  print(10 * "-" + " pokemon " + 10 * "-")
  pokemonTeam = PokemonTeamFactory().createTeam()
  print(pokemonTeam)
  print('goalie:', pokemonTeam.getGoalie())
  print('defense:', pokemonTeam.getDefense())
  print('offense:', pokemonTeam.getOffense())

  print(10 * "-" + " starwars " + 10 * "-")
  starWarsTeam = StarWarsTeamFactory().createTeam()
  print(starWarsTeam)
  print('goalie:', starWarsTeam.getGoalie())
  print('defense:', starWarsTeam.getDefense())
  print('offense:', starWarsTeam.getOffense())

if __name__ == '__main__':
  main()