from enum import IntEnum

class Role(IntEnum):
    READER = 1
    OPERATOR = 2
    ADMIN = 3

    def allows(self, required: "Role") -> bool:
        """Un rôle autorise une action si son niveau est >= au niveau requis."""
        return self >= required