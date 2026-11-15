import pytest
from app.security.roles import Role

@pytest.mark.parametrize("actual, required, expected", [
    (Role.ADMIN,    Role.ADMIN,    True),
    (Role.ADMIN,    Role.OPERATOR, True),
    (Role.ADMIN,    Role.READER,   True),
    (Role.OPERATOR, Role.OPERATOR, True),
    (Role.OPERATOR, Role.READER,   True),
    (Role.OPERATOR, Role.ADMIN,    False),
    (Role.READER,   Role.OPERATOR, False),
    (Role.READER,   Role.ADMIN,    False),
])
def test_role_hierarchy(actual, required, expected):
    assert actual.allows(required) is expected