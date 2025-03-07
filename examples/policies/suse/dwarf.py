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

from elftools.dwarf.die import DIE
from elftools.elf.elffile import ELFFile
from functools import wraps
from pathlib import PurePath

from .debuginfod import get_debug_info
from .utils import clean_relative_path


def require_attr(attr, require_die=False):
    def decorator(func):
        @wraps(func)
        def wrapper(die: DIE):
            attr_value = die.attributes.get(attr)
            if attr_value:
                return func(attr_value, die) if require_die else func(attr_value)
            return None
        return wrapper
    return decorator


@require_attr("DW_AT_decl_file", require_die=True)
def __desc_file(attr_name, die):
    """
    Retrieve and return the file path where a function is defined.
    """
    # FIXME: we hit the asserts sometimes
    cu = die.cu
    dwarfinfo = cu.dwarfinfo
    lineprogram = dwarfinfo.line_program_for_CU(cu)

    # Filename/dirname arrays are 0-based in DWARF v5
    offset = 0 if lineprogram.header.version >= 5 else -1

    file_index = offset + int(attr_name.value)
    # TODO: value 0 means that no source has been specified
    assert 0 <= file_index < len(lineprogram.header.file_entry)
    file_entry = lineprogram.header.file_entry[file_index]
    file_name = PurePath(file_entry.name.decode('utf-8', errors='ignore'))

    dir_index = offset + int(file_entry.dir_index)
    assert 0 <= dir_index < len(lineprogram.header.include_directory)
    enc_dir_path = lineprogram.header.include_directory[dir_index]
    dir_path = PurePath(enc_dir_path.decode('utf-8', errors='ignore'))

    return clean_relative_path(dir_path/file_name)


@require_attr("DW_AT_name")
def __desc_name(attr_name):
    return attr_name.value.decode('utf-8', errors='ignore')


@require_attr("DW_AT_decl_line")
def __desc_line(attr_name):
    return attr_name.value


@require_attr("DW_AT_low_pc")
def __desc_addr(attr_name):
    return attr_name.value


FUNC_ATTR_DESCRIPTIONS = {
    "name":__desc_name,
    "file":__desc_file,
    "line":__desc_line,
    "addr":__desc_addr
}


def __die_is_func(die: DIE):
    return die.tag == 'DW_TAG_subprogram'


# def __get_cu_name(cu):
#     cu_die = cu.get_top_DIE()
#     name_attr = cu_die.attributes.get('DW_AT_name')
#     assert name_attr
#     cu_name = PurePath(name_attr.value.decode('utf-8', errors='ignore'))
#     return str(clean_relative_path(cu_name))
#
#
# __cu_cache = {}
# def __get_cu_by_name(dwarf_info, name):
#     if name not in __cu_cache:
#         for cu in dwarf_info.iter_CUs():
#             cu_name = __get_cu_name(cu)
#
#             assert cu_name not in __cu_cache
#             __cu_cache[cu_name] = cu
#
#             if cu_name == name:
#                 break
#
#     return __cu_cache.get(name, None)


def get_sym_debug_info(elf: ELFFile, function, compilation_unit):
    # FIXME: this function doesn't take into account that a funciton belonging
    # to a compilation unit can actually be declared in a file that's
    # differenct from the CU
    # print("debug:", function, compilation_unit)

    dwarf_info = get_debug_info(elf)

    # TODO: cache CU by name
    for cu in dwarf_info.iter_CUs():
        cu_die = cu.get_top_DIE()
        name_attr = cu_die.attributes.get('DW_AT_name')
        assert name_attr

        cu_name = PurePath(name_attr.value.decode('utf-8', errors='ignore'))
        cu_name = clean_relative_path(cu_name)

        if cu_name != PurePath(compilation_unit):
            continue

        for die in cu.iter_DIEs():
            if not __die_is_func(die):
                continue

            if FUNC_ATTR_DESCRIPTIONS['name'](die) != function:
                # TODO: cache DIE by function name
                continue

            if PurePath(FUNC_ATTR_DESCRIPTIONS['file'](die)) == PurePath(compilation_unit):
                return FUNC_ATTR_DESCRIPTIONS['addr'](die)

