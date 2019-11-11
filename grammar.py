
import enum

class Symbol(object):
    def __init__(self, name, number, nt=False):
        self.name = name
        self.number = number
        self.nt = nt

    def __str__(self):
        return self.name + '(' + ('N' if self.nt else 'T') + ',' + str(self.number) + ')'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.number == other.number

    def is_term(self):
        return not self.nt

    def is_not_term(self):
        return self.nt

    def __hash__(self):
        return self.number


class NT(object):
    epsilon = Symbol('epsilon', 0)
    dollar = Symbol('dollar', -1)

    def __init__(self, n: set, t: set):
        self.cnt = 0
        self.n = n
        self.t = t
        dict([(1, 2), ])
        self.N = dict(map(lambda x: (x, self.sign(x, True)), n))
        self.T = dict(map(lambda x: (x, self.sign(x)), t))

    def sign(self, n, nt=False):
        self.cnt += 1
        return Symbol(n, self.cnt, nt)

    def recognize(self, name):
        if name == 'epsilon':
            return NT.epsilon
        if name in self.n:
            return self.N[name]
        if name in self.t:
            return self.T[name]


class GrammarType(enum.Enum):
    Nothing = None
    LL1 = 1


class Sequence(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Production(object):
    def __init__(self, lhs: Sequence, rhs: Sequence):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return 'lhs:' + str(self.lhs) + ', rhs:' + str(self.rhs)

    def __repr__(self):
        return self.__str__()


class Grammar(object):

    def __init__(self, *args):
        if isinstance(args[0], Grammar):
            self.NT, self.tokenP, self.tokenS = args[0].NT, args[0].tokenP, args[0].tokenS
        elif isinstance(args[0], NT):
            if isinstance(args[2], Symbol):
                self.tokenS = args[2]
            else:
                raise TypeError('tokenS type error')
            if isinstance(args[1], list):
                self.tokenP = args[1]
            else:
                raise TypeError('tokenP type error')
            if isinstance(args[0], NT):
                self.NT = args[0]
            else:
                raise TypeError('NT type error')
        elif isinstance(args[0], set):
            n, t, p, s = args
            self.NT = NT(n, t)
            self.tokenP = list(map(self.tokenize_p, p))
            self.tokenS = self.NT.recognize(s)

    def tokenize_p(self, p):
        return Production(*map(lambda x: Sequence(map(self.NT.recognize, x.split())), p.split('->')))

    def is_cfg(self):
        for pdt in self.tokenP:
            if len(pdt.lhs) != 1 or pdt.lhs[0].is_term():
                return False
        return True


class G(Grammar):
    def __init__(self, *args):
        super().__init__(*args)

    def build(self, grammar_type: GrammarType = None):
        if grammar_type is None:
            return self
        elif grammar_type == GrammarType.LL1:
            if not self.is_cfg():
                raise TypeError('cant convert non-cf grammar to LL(1)')
            return LL1(self)


class _GWF(Grammar):
    def __init__(self, *args):
        super().__init__(*args)
        self.first = None


class FirstableBuild(Grammar):
    def __new__(cls, *args, **kwargs):
        if isinstance(args[0], Grammar):
            args[0].first = dict()
            return FirstableBuild.build(args[0])
        else:
            raise TypeError('Firstable class does not build new grammar')

    @staticmethod
    def build(self: _GWF):
        self.first[NT.epsilon] = {NT.epsilon}
        for n in self.NT.N.values():
            self.first[n] = set()
        for t in self.NT.T.values():
            self.first[t] = {t}
        while FirstableBuild.__first_nt(self, self.first):
            pass
        return self

    @staticmethod
    def __first_nt(self: _GWF, s):
        upt = False
        for sym, fir in s.items():
            lx = len(fir)
            fir = FirstableBuild.__first_sym(self, sym)
            if lx != len(fir):
                upt = True
            s[sym] = fir
        return upt

    @staticmethod
    def __first_sym(self: _GWF, s: Symbol, term=False):
        f: set = self.first[s]
        if term or s.is_term():
            return f
        for pdt in self.tokenP:
            if pdt.lhs[0] == s:
                f = f.union(FirstableBuild.__first_seq(self, pdt.rhs))
        return f

    @staticmethod
    def __first_seq(self: _GWF, seq: Sequence):
        assert len(seq) != 0
        f = FirstableBuild.__first_sym(self, seq[0], True)
        e = NT.epsilon in f
        for sym in seq[1:]:
            if not e:
                return f
            x = FirstableBuild.__first_sym(self, sym, True)
            e = NT.epsilon in x
            f = f.union(x)
        return f


class LL1(Grammar):
    def __init__(self, *args):
        super().__init__(*args)
        self.first = dict()
        self.__build()

    def build(self, grammar_type: GrammarType = None):
        if grammar_type is None:
            return G(self)
        elif grammar_type == GrammarType.LL1:
            return self

    def __build(self):
        FirstableBuild(self)


if __name__ == '__main__':
    g = G({'A'}, {'a', 'b'}, {'A -> A a', 'A -> b'}, 'A')
    ll1 = g.build(GrammarType.LL1)
    print(ll1.tokenP)
    print(ll1.tokenS)
    print(ll1.first)
    g = G({'A', 'B', 'C'}, {'a', 'b', 'c'}, {'A -> A a', 'A -> B C', 'A -> b', 'B -> epsilon', 'C -> c'}, 'A')
    ll1 = g.build(GrammarType.LL1)
    print(ll1.first)
    g = G({'A', 'B', 'C'}, {'a', 'b', 'c'}, {'A -> A a', 'A -> B C', 'A -> b', 'B -> b', 'C -> c'}, 'A')
    ll1 = g.build(GrammarType.LL1)
    print(ll1.first)

    # print(isinstance(ggg, LL1))
