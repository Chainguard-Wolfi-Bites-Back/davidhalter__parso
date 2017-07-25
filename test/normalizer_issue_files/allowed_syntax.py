"""
Some syntax errors are a bit complicated and need exact checking. Here we
gather some of the potentially dangerous ones.
"""

from __future__ import division

# With a dot it's not a future import anymore.
from .__future__ import absolute_import

'' ''
''r''u''
b'' BR''

foo: int = 4
(foo): int = 3
((foo)): int = 3
foo.bar: int
foo[3]: int

for x in [1]:
    try:
        continue  # Only the other continue and pass is an error.
    finally:
        #: E901
        continue


for x in [1]:
    break
    continue

try:
    pass
except ZeroDivisionError:
    pass
    #: E722:0
except:
    pass

try:
    pass
    #: E722:0 E901:0
except:
    pass
except ZeroDivisionError:
    pass