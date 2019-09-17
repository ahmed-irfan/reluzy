import argparse
import logging

from reluzy import Reluzy

def main():

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    p = argparse.ArgumentParser()
    p.add_argument('filename', help='input nnet filename')

    opts = p.parse_args()
    
    logger.debug('Filename is ' + opts.filename)

    # nnet2smt = Nnet2Smt(opts.filename)
    # nnet2smt.print_nnet_info()
    # nnet2smt.convert(True)
    # print(nnet2smt.relus)
    # print(nnet2smt.relus_level)

    rz = Reluzy(opts.filename, logger)
    res = rz.solve()
    

if __name__ == "__main__":
    main()

    
