#
# NNET to SMT2 converter
#
# Author : Ahmed Irfan
#          <irfan@cs.stanford.edu>
#
#

import logging

from NNet.python.nnet import NNet

from pysmt.shortcuts import Symbol, REAL, Real, GE, LE, Times, Plus, Equals,\
    Max, FreshSymbol, And, Solver

class Nnet2Smt:

    def __init__(self, filename):
        self.nnet = NNet(filename)
        self.input_vars = []
        self.output_vars = []
        self.relus = []
        self.relus_level = []
        self.formulae = []

        
    def print_nnet_info(self):
        print("Number of Inputs : %d" % self.nnet.inputSize)
        print("Number of Outputs : %d" % self.nnet.outputSize)
        print("Number of Layers : %d" % self.nnet.numLayers)

    def convert(self, abstract=False):
        for i in range(self.nnet.inputSize):
            x = Symbol("x%d" % i, REAL)
            self.input_vars.append(x)
        for i in range(self.nnet.outputSize):
            y = Symbol("y%d" % i, REAL)
            self.output_vars.append(y)
        for i, m in enumerate(self.nnet.mins):
            # normalized
            l = GE(self.input_vars[i],
                   Real((m - self.nnet.means[i])/self.nnet.ranges[i]))
            self.formulae.append(l)
        for i, m in enumerate(self.nnet.maxes):
            # normalized
            l = LE(self.input_vars[i],
                   Real((m - self.nnet.means[i])/self.nnet.ranges[i]))
            self.formulae.append(l)

        prev_layer_result = self.input_vars.copy()
        layer_result = []
        zero = Real(0)
        self.relus_level.append(set())
        for l in range(self.nnet.numLayers - 1):
            self.relus_level.append(set())
            for ls in range(self.nnet.layerSizes[l+1]):
                r = self.dot(self.nnet.weights[l][ls], prev_layer_result)
                r = Plus(r, Real(float(self.nnet.biases[l][ls])))
                r_aux = FreshSymbol(REAL)
                self.formulae.append(Equals(r_aux, r))
                if abstract:
                    relu_v = FreshSymbol(REAL)
                    r = relu_v
                    self.relus.append((relu_v, r_aux))
                    self.relus_level[l+1].add((relu_v, r_aux))
                else:
                    r = Max(r_aux, zero)
                layer_result.append(r)
            prev_layer_result = layer_result.copy()
            layer_result.clear()

        for i, y in enumerate(self.output_vars):
            o = self.dot(self.nnet.weights[-1][i], prev_layer_result)
            o = Plus(o, Real(float(self.nnet.biases[-1][i])))
            # undo normalization
            o = Times(o, Real(self.nnet.ranges[-1]))
            o = Plus(o, Real(self.nnet.means[-1]))
            self.formulae.append(Equals(y, o))


    def dot(self, num_list, pysmt_list):
        assert(len(num_list) == len(pysmt_list))
        res = Real(0)
        for n in range(len(num_list)):
            nreal = Real(float(num_list[n]))
            prod = Times(pysmt_list[n], nreal)
            res = Plus(res, prod)
        return res

