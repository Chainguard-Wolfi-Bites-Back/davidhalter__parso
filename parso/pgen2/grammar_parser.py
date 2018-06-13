# Copyright 2004-2005 Elemental Security, Inc. All Rights Reserved.
# Licensed to PSF under a Contributor Agreement.

# Modifications:
# Copyright David Halter and Contributors
# Modifications are dual-licensed: MIT and PSF.

from parso.python import tokenize
from parso.utils import parse_version_string
from parso.python import token


class GrammarParser():
    """
    The parser for Python grammar files.
    """
    def __init__(self, bnf_grammar):
        self._bnf_grammar = bnf_grammar
        self.generator = tokenize.tokenize(
            bnf_grammar,
            version_info=parse_version_string('3.6')
        )
        self._gettoken()  # Initialize lookahead

    def parse(self):
        # grammar: (NEWLINE | rule)* ENDMARKER
        while self.type != token.ENDMARKER:
            while self.type == token.NEWLINE:
                self._gettoken()

            # rule: NAME ':' rhs NEWLINE
            self._current_rule_name = self._expect(token.NAME)
            self._expect(token.COLON)

            a, z = self._parse_rhs()
            self._expect(token.NEWLINE)

            yield a, z

    def _parse_rhs(self):
        # rhs: items ('|' items)*
        a, z = self._parse_items()
        if self.value != "|":
            return a, z
        else:
            aa = NFAState(self._current_rule_name)
            zz = NFAState(self._current_rule_name)
            while True:
                # Add the possibility to go into the state of a and come back
                # to finish.
                aa.add_arc(a)
                z.add_arc(zz)
                if self.value != "|":
                    break

                self._gettoken()
                a, z = self._parse_items()
            return aa, zz

    def _parse_items(self):
        # items: item+
        a, b = self._parse_item()
        while self.type in (token.NAME, token.STRING, token.LPAR, token.LSQB):
            c, d = self._parse_item()
            # Need to end on the next item.
            b.add_arc(c)
            b = d
        return a, b

    def _parse_item(self):
        # item: '[' rhs ']' | atom ['+' | '*']
        if self.value == "[":
            self._gettoken()
            a, z = self._parse_rhs()
            self._expect(token.RSQB)
            # Make it also possible that there is no token and change the
            # state.
            a.add_arc(z)
            return a, z
        else:
            a, z = self._parse_atom()
            value = self.value
            if value not in ("+", "*"):
                return a, z
            self._gettoken()
            # Make it clear that we can go back to the old state and repeat.
            z.add_arc(a)
            if value == "+":
                return a, z
            else:
                # The end state is the same as the beginning, nothing must
                # change.
                return a, a

    def _parse_atom(self):
        # atom: '(' rhs ')' | NAME | STRING
        if self.value == "(":
            self._gettoken()
            a, z = self._parse_rhs()
            self._expect(token.RPAR)
            return a, z
        elif self.type in (token.NAME, token.STRING):
            a = NFAState(self._current_rule_name)
            z = NFAState(self._current_rule_name)
            # Make it clear that the state transition requires that value.
            a.add_arc(z, self.value)
            self._gettoken()
            return a, z
        else:
            self._raise_error("expected (...) or NAME or STRING, got %s/%s",
                              self.type, self.value)

    def _expect(self, type):
        if self.type != type:
            self._raise_error("expected %s(%s), got %s(%s)",
                              type, token.tok_name[type], self.type, self.value)
        value = self.value
        self._gettoken()
        return value

    def _gettoken(self):
        tup = next(self.generator)
        self.type, self.value, self.begin, prefix = tup

    def _raise_error(self, msg, *args):
        if args:
            try:
                msg = msg % args
            except:
                msg = " ".join([msg] + list(map(str, args)))
        line = self._bnf_grammar.splitlines()[self.begin[0] - 1]
        raise SyntaxError(msg, ('<grammar>', self.begin[0],
                                self.begin[1], line))


class NFAState(object):
    def __init__(self, from_rule):
        self.from_rule = from_rule
        self.arcs = []  # list of (label, NFAState) pairs

    def add_arc(self, next, label=None):
        assert label is None or isinstance(label, str)
        assert isinstance(next, NFAState)
        self.arcs.append((label, next))

    def __repr__(self):
        return '<%s: from %s>' % (self.__class__.__name__, self.from_rule)
