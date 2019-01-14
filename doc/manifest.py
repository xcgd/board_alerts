#!/usr/bin/env python
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 XCG Consulting (http://www.xcg-consulting.fr/)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import ast


def main():
    with open("../__manifest__.py", "r") as f:
        read_data = f.read()
    d = ast.literal_eval(read_data)
    with open("manifest", "w") as out:
        out.write(d["description"])


if __name__ == "__main__":
    main()
