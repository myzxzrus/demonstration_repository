from .users import router_users
from .auth import router_auth
from .game import router_game
from .audit import router_audit


api_list = [router_users, router_auth, router_game, router_audit]


