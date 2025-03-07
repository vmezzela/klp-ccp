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
from elftools.elf.elffile import ELFFile
import subprocess

def __get_debug_info_path(build_id):
    """
    Fetches debug information for a given build ID using the system debuginfod.
    """
    debuginfod_cmd = ["debuginfod-find", "debuginfo", build_id]

    # TODO: error handling
    debug_info_path = subprocess.run(debuginfod_cmd, check=True, capture_output=True, text=True)
    return debug_info_path.stdout.strip()


def __get_build_id(elf):
    for section in elf.iter_sections():
        if section.name == ".note.gnu.build-id":
            note = next(section.iter_notes(), None)
            if note and note["n_type"] == "NT_GNU_BUILD_ID":
                return note["n_desc"]
    return None

def get_debug_info(elf: ELFFile):
    build_id = __get_build_id((elf))
    debug_info_file_path = __get_debug_info_path(build_id)
    debug_info_file = open(debug_info_file_path, 'rb')
    elf = ELFFile(debug_info_file)
    return elf.get_dwarf_info()
