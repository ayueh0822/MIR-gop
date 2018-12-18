landDir='/home/ms2017/kaldi/egs/pkasr/matbn_mispro/lang/ky92k_forpaift_v11'
dictDir='/home/ms2017/kaldi/egs/pkasr/matbn_mispro/dict/ky92k_forpaift_v11'
gopDir='/home/ms2017/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/eval_matbn_mispro_tri4_advanced_gmmTesting_new'

rm -rf $gopDir/parse

python3 gop2json.py $landDir $dictDir $gopDir
