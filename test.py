import argparse
import logging

from reluzy import Reluzy

def main():

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    p = argparse.ArgumentParser()
    p.add_argument('nnet', help='input nnet filename')
    p.add_argument('violation', help='violation filename')

    opts = p.parse_args()

    logger.debug('Filename is ' + opts.nnet)
    logger.debug('Violation file is ' + opts.violation)

    rz = Reluzy(opts.nnet, opts.violation, logger)
    res = rz.solve()

if __name__ == "__main__":
    main()

    
