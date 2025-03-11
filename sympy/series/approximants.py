from sympy.core.singleton import S
from sympy.core.symbol import Symbol
from sympy.polys.polytools import lcm
from sympy.utilities import public
from sympy import Expr, Poly
from typing import Generator
from sympy.polys.polytools import extended_euclidean_algorithm

@public
def approximants(l, X=Symbol('x'), simplify=False):
    """
    Return a generator for consecutive Pade approximants for a series.
    It can also be used for computing the rational generating function of a
    series when possible, since the last approximant returned by the generator
    will be the generating function (if any).

    Explanation
    ===========

    The input list can contain more complex expressions than integer or rational
    numbers; symbols may also be involved in the computation. An example below
    show how to compute the generating function of the whole Pascal triangle.

    The generator can be asked to apply the sympy.simplify function on each
    generated term, which will make the computation slower; however it may be
    useful when symbols are involved in the expressions.

    Examples
    ========

    >>> from sympy.series import approximants
    >>> from sympy import lucas, fibonacci, symbols, binomial
    >>> g = [lucas(k) for k in range(16)]
    >>> [e for e in approximants(g)]
    [2, -4/(x - 2), (5*x - 2)/(3*x - 1), (x - 2)/(x**2 + x - 1)]

    >>> h = [fibonacci(k) for k in range(16)]
    >>> [e for e in approximants(h)]
    [x, -x/(x - 1), (x**2 - x)/(2*x - 1), -x/(x**2 + x - 1)]

    >>> x, t = symbols("x,t")
    >>> p=[sum(binomial(k,i)*x**i for i in range(k+1)) for k in range(16)]
    >>> y = approximants(p, t)
    >>> for k in range(3): print(next(y))
    1
    (x + 1)/((-x - 1)*(t*(x + 1) + (x + 1)/(-x - 1)))
    nan

    >>> y = approximants(p, t, simplify=True)
    >>> for k in range(3): print(next(y))
    1
    -1/(t*(x + 1) - 1)
    nan

    See Also
    ========

    sympy.concrete.guess.guess_generating_function_rational
    mpmath.pade
    """
    from sympy.simplify import simplify as simp
    from sympy.simplify.radsimp import denom
    p1, q1 = [S.One], [S.Zero]
    p2, q2 = [S.Zero], [S.One]
    while len(l):
        b = 0
        while l[b]==0:
            b += 1
            if b == len(l):
                return
        m = [S.One/l[b]]
        for k in range(b+1, len(l)):
            s = 0
            for j in range(b, k):
                s -= l[j+1] * m[b-j-1]
            m.append(s/l[b])
        l = m
        a, l[0] = l[0], 0
        p = [0] * max(len(p2), b+len(p1))
        q = [0] * max(len(q2), b+len(q1))
        for k in range(len(p2)):
            p[k] = a*p2[k]
        for k in range(b, b+len(p1)):
            p[k] += p1[k-b]
        for k in range(len(q2)):
            q[k] = a*q2[k]
        for k in range(b, b+len(q1)):
            q[k] += q1[k-b]
        while p[-1]==0: p.pop()
        while q[-1]==0: q.pop()
        p1, p2 = p2, p
        q1, q2 = q2, q

        # yield result
        c = 1
        for x in p:
            c = lcm(c, denom(x))
        for x in q:
            c = lcm(c, denom(x))
        out = ( sum(c*e*X**k for k, e in enumerate(p))
              / sum(c*e*X**k for k, e in enumerate(q)) )
        if simplify:
            yield(simp(out))
        else:
            yield out
    return


@public
def pade_approximants(
    f: Expr, x: Expr, order: int
) -> Generator[tuple[Poly, Poly], None, None]:
    """
    Returns all pade approximants of the expression f of the desired order

    Description
    ===========

    Given a function f and an integer order, the function computes all pade approximants
    of order [m/n] with m + n = order.

    Parameters
    ==========

    f : Expr
        The function to approximate
    x : Expr
        The variable of the function
    order : int
        The desired order of the pade approximants

    Returns
    =======

    pade approximants : Generator[tuple[Poly, Poly], None, None]
        Generator for (numerator, denominator) pairs of polynomials representing the numerator
        and denominators of the approximants.

    Examples
    ========

    >>> from sympy.abc import x
    >>> from sympy import sin, exp
    >>> from sympy.series.approximants import pade_approximants

    >>> pade_exp = pade_approximants(exp(x), x, 2)
    >>> for num, denom in pade_exp: print(num, denom)
    Poly(1/2*x**2 + x + 1, x, domain='QQ') Poly(1, x, domain='QQ')
    Poly(2*x + 4, x, domain='QQ') Poly(-2*x + 4, x, domain='QQ')
    Poly(1, x, domain='QQ') Poly(1/2*x**2 - x + 1, x, domain='QQ')

    To get the pade approximants, divide the numerator by the denominator

    >>> pade_sin = pade_approximants(sin(x), x, 5)
    >>> for num, denom in pade_sin: print(num/denom)
    x**5/120 - x**3/6 + x
    -(20*x**4 - 120*x**2)/(120*x)
    (-7*x**3/60 + x)/(x**2/20 + 1)
    360*x**2/(7*(60*x**3/7 + 360*x/7))
    x/(7*x**4/360 + x**2/6 + 1)
    """

    assert order >= 0, "order must be a non-negative integer"

    f_taylor_poly = f.series(x, n=order + 1).removeO().as_poly(x, field=True)
    remainder_monomial = Poly(x ** (order + 1), x)

    yield f_taylor_poly, f_taylor_poly.one

    eea = extended_euclidean_algorithm(remainder_monomial, f_taylor_poly)

    for _, t, r in eea:
        yield r, t


@public
def pade_approximant(f: Expr, x: Expr, m: int, n: int | None = None) -> Expr:
    """
    [m/n] pade approximant of f around x=0

    Description
    ===========

    For a function f and integers m and n, the [m/n] pade approximant of f is the rational function
    p(x)/f(x) such that p(x) and q(x) are polynomials of degree at most m and n respectively. The pade
    approximation is such that the taylor series of p(x)/q(x) around x=0 matches the taylor series of f(x)
    up to at least (m + n)th order in x.

    Parameters
    ==========

    f : Expr
        The function to approximate
    x : Expr
        The variable of the function
    m : int
        The degree of the numerator polynomial
    n : int | None
        The degree of the denominator polynomial. If None, n = m

    Returns
    =======

    pade approximant : Expr
        The pade approximant of f, a rational function

    Examples
    ========

    >>> import sympy as sp
    >>> from sympy.series.approximants import pade_approximant
    >>> x = sp.symbols('x')

    >>> pade_exp = pade_approximant(sp.exp(x), x, 2)
    >>> pade_exp
    (x**2/4 + 3*x/2 + 3)/(x**2/4 - 3*x/2 + 3)

    The numerators and denominators of an [m/n] pade approximant do not
    necessarily have order m and n respectively

    >>> pade_sin = pade_approximant(sp.sin(x), x, 1, 3)
    >>> pade_sin
    36*x/(6*x**2 + 36)

    The [m/0] pade approximant is the mth order taylor polynomial of f

    >>> pade_cos = pade_approximant(sp.cos(x), x, 4, 0)
    >>> pade_cos
    x**4/24 - x**2/2 + 1
    """
    if n is None:
        n = m

    assert m >= 0 and n >= 0, "m and n must be non-negative integers"

    approximants = pade_approximants(f, x, m + n)

    numerator, denominator = next(approximants)
    for next_numerator, next_denominator in approximants:
        if next_numerator.degree() < m:
            return numerator / denominator

        numerator, denominator = next_numerator, next_denominator

    if numerator.degree() == m:
        return numerator / denominator

    # if it hasn't returned yet, there is no [m/n] pade approximant
    return None
