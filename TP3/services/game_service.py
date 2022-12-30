from sqlalchemy import *
from model.player import Player
from model.battlefield import Battlefield
from model.game import Game
from model.cruiser import Cruiser
from model.destroyer import Destroyer
from model.submarine import Submarine
from model.frigate import Frigate
from dao.game_dao import GameDao, WeaponEntity, VesselEntity


class GameService:

    def __init__(self):
        self.db_session = None
        self.GameDao = None
        self.game_dao = GameDao()

    def create_game(self, player_name: str, min_x: int, max_x: int, min_y: int, max_y: int, min_z: int,
                    max_z: int) -> int:
        game = Game()
        battle_field = Battlefield(min_x, max_x, min_y, max_y, min_z, max_z)
        game.add_player(Player(player_name, battle_field))
        return self.game_dao.create_game(game)

    def join_game(self, game_id: int, player_name: str) -> bool:
        game = self.GameDao.find_game(game_id)
        player = game.get_players()[0]
        game.add_player(Player(player_name, player.battle_field))
        return True

    def get_game(self, game_id: int) -> Game:
        game = self.GameDao.find_game(game_id)
        return game

    def add_vessel(self, game_id: int, player_name: str, vessel_type: str, x: int, y: int, z: int) -> bool:
        game = self.get_game(game_id)
        player = [i for i in game.get_players() if i.name == player_name][0]
        battlefield = player.get_battlefield()
        if vessel_type == "Cruiser":
            vessel = Cruiser(x, y, z)
        if x < battlefield.min_x or x > battlefield.max_x or y < battlefield.min_y or y > battlefield.max_y or z < battlefield.min_z or z > battlefield.max_z:
            raise ValueError("La position est hors du champ du bataille")    
        elif vessel_type == "Destroyer":

            vessel = Destroyer(x, y, z)
        elif vessel_type == "Submarine":
            vessel = Submarine(x, y, z)    
        elif vessel_type == "Frigate":
            vessel = Frigate(x, y, z)
      
        else:
            raise ValueError("Invalid  type")
        battlefield.add_vessel(vessel)
        self.GameDao.create_vessel(battlefield.id, vessel)
        return True

    def shoot_at(self, game_id: int, shooter_name: str, vessel_id: int, x: int, y: int, z: int) -> bool:
        vessel = self.game_dao.find_vessel(vessel_id)
        game = self.game_dao.find_game(game_id)
        if vessel.weapon.ammunitions >= 1:
            stmt = update(WeaponEntity).where(WeaponEntity.vessel_id == vessel_id).values(
                {WeaponEntity.ammunitions: WeaponEntity.ammunitions - 1})
            self.db_session.scalars(stmt).one()
            for player in game.get_players():
                if player.get_name() != shooter_name:
                    if player.get_battlefield().fired_at(x, y, z):
                        stmt = update(VesselEntity).where(VesselEntity.coord_x == x, VesselEntity.coord_y == y,
                                                          VesselEntity.coord_z == z).values(
                            {VesselEntity.hits_to_be_destroyed: VesselEntity.hits_to_be_destroyed - 1})
                        self.db_session.scalars(stmt).one()
                        return True
                    return False

    def get_game_status(self, game_id: int, shooter_name: str) -> str:
        game = self.get_game(game_id)
        shooter = [p for p in game.get_players() if p.name == shooter_name][0]
        target = [p for p in game.get_players() if p.name != shooter_name][0]
        d = 0
        l = 0
        e = 0
        z = 0
        for s in shooter.get_battlefield().get_vessels():
            if s.hits_to_be_destroyed != 0:
                d += 1
            elif s.weapon.ammunitions != 0:
                l += 1
        if d == 0 or l == 0:
            return "PERDU"
        for t in target.get_battlefield().get_vessels():
            if t.hits_to_be_destroyed != 0:
                e += 1
            elif t.weapon.ammunitions != 0:
                z += 1
        if e == 0 or z == 0:
            return "GAGNE"
        else:
            return "COURS"
