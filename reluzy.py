#
# Reluzy : A Lazy NN-with-Relu Solver
# 
# Author : Ahmed Irfan
#          <irfan@cs.stanford.edu>
#

import logging

from nnet2smt import Nnet2Smt

from pysmt.shortcuts import Solver, And, Real, Max, Equals, GE, LE, Implies


class Reluzy:

    def __init__(self, filename):
        self.logger = logging.getLogger(__name__)
        self.nnet2smt = Nnet2Smt(filename)
        self.nnet2smt.convert(True)
        self.input_vars = self.nnet2smt.input_vars
        self.output_vars = self.nnet2smt.output_vars
        self.formulae = self.nnet2smt.formulae
        self.relus = self.nnet2smt.relus
        self.solver = Solver(name='yices')
        self.sat_checker = Solver(name='yices')
        self.init()
        
    def init(self):
        self.solver.add_assertion(And(self.formulae))
        self.sat_checker.add_assertion(And(self.formulae))
        for r1, r2 in self.relus:
            self.sat_checker.add_assertion(Equals(r1, Max(r2, Real(0))))
        
    def solve(self):
        while True:
            res = self.solver.solve()
            if not res:
                print('unsat')
                break
            else:
                lemmas = self.refine()
                if not lemmas:
                    print('sat')
                    break
                else:
                    self.solver.add_assertion(And(lemmas))


    def check_sat(self):
        self.logger.info('Checking for Sat')
        self.sat_checker.push()
        for v in self.input_vars:
            self.sat_checker.add_assertion(Equals(v, self.solver.get_value(v)))
        res = self.sat_checker.solve()
        if res:
            for x in self.input_vars:
                print(v, self.sat_checker.get_value(x))
            return True
        else:
            self.sat_checker.pop()
            return False
            

    def refine(self):
        self.logger.info('Refining')
        lemmas = self.refine_zero_pos()
        if not lemmas:
            lemmas = self.refine_zero_neg()

        if not lemmas:
            lemmas = self.refine_slope_lb()

        if not lemmas:
            lemmas = self.refine_slope_ub()

        if not lemmas:
            for v in self.input_vars:
                print(v, self.solver.get_value(v))
        elif self.check_sat():
            return False

        return lemmas

    def refine_zero_pos(self):
        lemmas = []
        zero = Real(0)
        for r1, _ in self.relus:
            l = GE(r1, zero)
            tval = self.solver.get_value(l)
            if l.is_false():
                lemmas.append(l)
        return lemmas

    def refine_zero_neg(self):
        lemmas = []
        zero = Real(0)
        for r1, r2 in self.relus:
            l = Implies(LE(r2, zero), LE(r1, zero))
            tval = self.solver.get_value(l)
            if l.is_false():
                lemmas.append(l)
        return lemmas
        
    def refine_slope_lb(self):
        lemmas = []
        zero = Real(0)
        for r1, r2 in self.relus:
            l = Implies(GE(r2, zero), GE(r1, r2))
            tval = self.solver.get_value(l)
            if l.is_false():
                lemmas.append(l)
        return lemmas
       
    def refine_slope_ub(self):
        lemmas = []
        zero = Real(0)
        for r1, r2 in self.relus:
            l = Implies(GE(r2, zero), LE(r1, r2))
            tval = self.solver.get_value(l)
            if l.is_false():
                lemmas.append(l)
        return lemmas
    
