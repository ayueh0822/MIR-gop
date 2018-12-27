kaldiRoot=~/kaldi
landDir=$kaldiRoot/egs/pkasr/matbn_mispro/lang/ky92k_forpaift_v11
dictDir=$kaldiRoot/egs/pkasr/matbn_mispro/dict/ky92k_forpaift_v11
gopDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/eval_matbn_mispro_tri4_advanced_dnnTesting

rm -rf $gopDir/parse

python3 gop2json.py $landDir $dictDir $gopDir
