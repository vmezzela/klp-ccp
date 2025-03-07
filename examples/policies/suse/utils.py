#
# Copyright (C) 2025  SUSE Software Solutions Germany GmbH
#
# This file is part of klp-ccp.
#
# klp-ccp is free software: you can redistribute it and/or modify it
# under the terms of version 2 of the GNU General Public License as
# published by the Free Software Foundation.
#
# klp-ccp is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with klp-ccp. If not, see <https://www.gnu.org/licenses/>.
#


from pathlib import PurePath


def __clean_relative_path_r(path: PurePath):
    parts = path.parts
    if parts and parts[0] != "..":
        return path

    new_path = PurePath(*parts[1:])
    return __clean_relative_path_r(new_path)


def clean_relative_path(path):
    """
    Drop all the leading ".." from the path
    """
    return __clean_relative_path_r(PurePath(path))
