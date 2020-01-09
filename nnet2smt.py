import logging
import argparse
import sys

from nnet import NNet

from pysmt.shortcuts import Symbol, REAL, Real, GE, GT, LE, LT, Times, Plus, Equals,\
    Max, Function, FunctionType, FreshSymbol, And, Or, Not, Implies, Solver

from pysmt.parsing import parse


from pysmt.smtlib.script import smtlibscript_from_formula


class Nnet2Smt:

    def __init__(self, filename, violation):
        self.nnet = NNet(filename)
        self.violation_path=violation
        self.input_vars = []
        self.output_vars = []
        self.relus = []
        self.relus_level = []
        self.formulae = []
        self.relu_fun = Symbol("relu", FunctionType(REAL, (REAL,)))

    def print_nnet_info(self):
        print("Number of Inputs : %d" % self.nnet.inputSize)
        print("Number of Outputs : %d" % self.nnet.outputSize)
        print("Number of Layers : %d" % self.nnet.numLayers)

    def parse_violation(self, violation):
        file = open(violation)
        for line in file:
           predicate = parse(line)
           self.formulae.append(predicate)

    def convert(self, abstract=False):

        for i in range(self.nnet.inputSize):
            x = Symbol("x%d" % i, REAL)
            self.input_vars.append(x)
        for i in range(self.nnet.outputSize):
            y = Symbol("y%d" % i, REAL)
            self.output_vars.append(y)
        # for i,v in enumerate(self.input_vars):
        #     # normalized
        #     m = self.nnet.mins[i]
        #     l = GE(self.input_vars[i],
        #            Real((m - self.nnet.means[i])/self.nnet.ranges[i]))
        #     self.formulae.append(l)
        #     # normalized
        #     m = self.nnet.maxes[i]
        #     l = LE(self.input_vars[i],
        #            Real((m - self.nnet.means[i])/self.nnet.ranges[i]))
        #     self.formulae.append(l)

        prev_layer_result = self.input_vars.copy()
        layer_result = []
        zero = Real(0)
        self.relus_level.append(set())
        for l in range(self.nnet.numLayers - 1):
            self.relus_level.append(set())
            for ls in range(self.nnet.layerSizes[l+1]):
                r = self.dot(self.nnet.weights[l][ls], prev_layer_result)
                r = Plus(r, Real(float(self.nnet.biases[l][ls])))
                r_sum = FreshSymbol(REAL)
                self.formulae.append(Equals(r_sum, r))
                if abstract:
                    relu_v = FreshSymbol(REAL)
                    r = relu_v
                    self.relus.append((relu_v, r_sum))
                    self.relus_level[l+1].add((relu_v, r_sum))
                else:
                    r = Max(r_sum, zero)
                layer_result.append(r)
            prev_layer_result = layer_result.copy()
            layer_result.clear()

        for i, y in enumerate(self.output_vars):
            o = self.dot(self.nnet.weights[-1][i], prev_layer_result)
            o = Plus(o, Real(float(self.nnet.biases[-1][i])))
            # # undo normalization
            # o = Times(o, Real(self.nnet.ranges[-1]))
            # o = Plus(o, Real(self.nnet.means[-1]))
            self.formulae.append(Equals(y, o))

        self.parse_violation(self.violation_path)


    def add_relu_eager_constraint(self):
        # Eager lemma encoding for relus
        zero = Real(0)
        for r, aux in self.relus:
            self.formulae.append(Implies(GT(aux, zero),Equals(r,aux)))
            self.formulae.append(Implies(LE(aux, zero),Equals(r,zero)))

    def add_relu_maxOA_constraint(self):
        zero = Real(0)
        for r, aux in self.relus:
            # MAX abstraction
            self.formulae.append(LT(r,aux))
            self.formulae.append(LT(r,zero))
            # MAX - case based upper bound
            self.formulae.append(Implies(GT(aux, zero),GT(r,aux)))
            self.formulae.append(Implies(LE(aux, zero),GT(r,zero)))


    def dot(self, num_list, pysmt_list):
        assert(len(num_list) == len(pysmt_list))
        res = Real(0)
        for n in range(len(num_list)):
            nreal = Real(float(num_list[n]))
            prod = Times(pysmt_list[n], nreal)
            res = Plus(res, prod)
        return res

    def get_smt_formula(self):
        return And(self.formulae)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    #logger.setLevel(logging.DEBUG)

    p = argparse.ArgumentParser()
    p.add_argument('nnet', help='input nnet filename')
    p.add_argument('violation', help='violation filename')
    p.add_argument('abstraction', help='violation filename')


    opts = p.parse_args()


    logger.debug('Filename is ' + opts.nnet)
    logger.debug('Violation file is ' + opts.violation)
    overapproximate_max=bool(int(opts.abstraction))
    logger.debug('Using Max overapproximation '+ str(overapproximate_max))

    nnet2smt = Nnet2Smt(opts.nnet, opts.violation)
    #nnet2smt.print_nnet_info()
    nnet2smt.convert(True)
    if overapproximate_max:
        nnet2smt.add_relu_maxOA_constraint()
    else:
        nnet2smt.add_relu_eager_constraint()

    f = nnet2smt.get_smt_formula()

    script_out = smtlibscript_from_formula(f)
    script_out.serialize(outstream=sys.stdout, daggify=False)
