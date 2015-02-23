from firedrake import *
import pytest


def run_poisson(typ):
    if typ == "mg":
        parameters = {"snes_type": "ksponly",
                      "ksp_type": "preonly",
                      "pc_type": "mg",
                      "pc_mg_type": "full",
                      "mg_levels_ksp_type": "chebyshev",
                      "mg_levels_ksp_max_it": 2,
                      "mg_levels_pc_type": "jacobi",
                      "snes_convergence_test": "skip"}
    elif typ == "fas":
        parameters = {"snes_type": "fas",
                      "snes_fas_type": "full",
                      "fas_coarse_snes_type": "newtonls",
                      "fas_coarse_ksp_type": "preonly",
                      "fas_coarse_pc_type": "redundant",
                      "fas_coarse_redundant_pc_type": "lu",
                      "fas_coarse_snes_linesearch_type": "basic",
                      "fas_levels_snes_type": "newtonls",
                      "fas_levels_snes_linesearch_type": "basic",
                      "fas_levels_snes_max_it": 1,
                      "fas_levels_ksp_type": "chebyshev",
                      "fas_levels_ksp_max_it": 2,
                      "fas_levels_pc_type": "jacobi",
                      "fas_levels_ksp_convergence_test": "skip",
                      "snes_max_it": 1,
                      "snes_convergence_test": "skip"}
    else:
        raise RuntimeError("Unknown parameter set '%s' request", typ)

    mesh = UnitSquareMesh(10, 10)

    nlevel = 2

    mh = MeshHierarchy(mesh, nlevel)

    V = FunctionSpaceHierarchy(mh, 'CG', 2)

    u = FunctionHierarchy(V)
    u_ = u[-1]
    f = FunctionHierarchy(V)
    f_ = f[-1]
    v = TestFunction(V[-1])
    F = dot(grad(u_), grad(v))*dx - f_*v*dx
    bcs = DirichletBC(V[-1], 0.0, (1, 2, 3, 4))
    # Choose a forcing function such that the exact solution is not an
    # eigenmode.  This stresses the preconditioner much more.  e.g. 10
    # iterations of ilu fails to converge this problem sufficiently.
    for f_ in f:
        f_.interpolate(Expression("-0.5*pi*pi*(4*cos(pi*x[0]) - 5*cos(pi*x[0]*0.5) + 2)*sin(pi*x[1])"))

    problem = NonlinearVariationalProblem(F, u_, bcs=bcs)

    solver = NLVSHierarchy(problem, solver_parameters=parameters)

    solver.solve()

    exact = Function(V[-1])
    exact.interpolate(Expression("sin(pi*x[0])*tan(pi*x[0]*0.25)*sin(pi*x[1])"))

    return norm(assemble(exact - u_))


@pytest.mark.parametrize("typ",
                         ["mg", "fas"])
def test_poisson_gmg(typ):
    assert run_poisson(typ) < 4e-6


@pytest.mark.parallel
def test_poisson_gmg_parallel_mg():
    assert run_poisson("mg") < 4e-6


@pytest.mark.parallel
def test_poisson_gmg_parallel_fas():
    assert run_poisson("fas") < 4e-6


if __name__ == "__main__":
    import os
    pytest.main(os.path.abspath(__file__))
