# This file is part of Lumina.
#
# Lumina is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lumina is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Lumina. If not, see <https://www.gnu.org/licenses/>.

__author__ = "Lukas Reiter"
__copyright__ = "Copyright (C) 2024 Lukas Reiter"
__license__ = "GPLv3"

import enum


class RoleEnum(enum.IntEnum):
    """
    Enum for account roles.
    """
    auditor = 100
    admin = 200


class ApiPermissionDetails:
    """
    Class that contains the details of a REST API permission.
    """
    def __init__(self, description: str, api_access: bool = False):
        self.description = description
        self.api_access = api_access


class ApiPermissionEnum(enum.Enum):
    """
    Enum that specifies all atomic REST API permissions.

    Based on this enum, the permissions for all account roles can be granularly defined.
    """
    country_read = ApiPermissionDetails(description="Read countries", api_access=True)
    account_read = ApiPermissionDetails(description="Read accounts")
    account_update = ApiPermissionDetails(description="Update an account")
    account_me_read = ApiPermissionDetails(description="Read the current account")
    account_me_update = ApiPermissionDetails(description="Update the current account")
    websocket = ApiPermissionDetails(description="Establish a WebSocket connection")


# Perform a check to ensure that there are no duplicate values in the enum.
scopes = [item for item in ApiPermissionEnum]
assert len(scopes) == 6
result_count = {}
for scope in scopes:
    if scope.value not in result_count:
        result_count[scope.value] = 0
    else:
        raise ValueError(f"Duplicate value '{scope.value}' in enum '{scope.name}'.")


# Dictionary that maps a account roles to REST API permissions/scopes.
ROLE_PERMISSION_MAPPING = {
    RoleEnum.admin.name: [item.name for item in ApiPermissionEnum],
    RoleEnum.auditor.name: [item.name for item in ApiPermissionEnum if item.name.endswith("_read")] +
                           [ApiPermissionEnum.account_me_read.name],
}


# We create a lookup table for all roles and their API permissions.
ROLE_API_PERMISSIONS = {}
for role, permissions in ROLE_PERMISSION_MAPPING.items():
    ROLE_API_PERMISSIONS[role] = []
    for access in permissions:
        info = ApiPermissionEnum[access]
        if info.value.api_access:
            ROLE_API_PERMISSIONS[role].append({"id": access, "name": info.value.description})
