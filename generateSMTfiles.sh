#!/bin/bash

networks=Networks/

for nnet in `ls $networks*.nnet`; do
    for prop in 1 2 3 4 5 6; do
       name=`basename $nnet .nnet`_p$prop
       echo $name 
       python ../nnet2smt.py $nnet property$prop.txt 0 0 > smt/${name}_e.smt2 
       python ../nnet2smt.py $nnet property$prop.txt 1 0 > smt/${name}_l.smt2 
       python ../nnet2smt.py $nnet property$prop.txt 0 1 > smt/${name}_e_sf.smt2 
       python ../nnet2smt.py $nnet property$prop.txt 1 1 > smt/${name}_l_sf.smt2 
    done
done
