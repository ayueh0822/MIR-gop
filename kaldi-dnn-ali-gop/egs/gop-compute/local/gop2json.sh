dnn=true

kaldiRoot=~/kaldi
landDir=$kaldiRoot/egs/pkasr/matbn_mispro/lang/ky92k_forpaift_v11
dictDir=$kaldiRoot/egs/pkasr/matbn_mispro/dict/ky92k_forpaift_v11

if [[ "$dnn" = false ]]; then
    echo "Using GMM model!"
    gopDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_withTone_testOnly_tri5_gmm
else
    echo "Using DNN model!"
    gopDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_withTone_testOnly_dnn
fi

misInfo=/home/ms2017/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/local/mispro_parse/text_mispro_new

if [ -d "$gopDir/parse" ]; then
  rm -rf $gopDir/parse_backup
  mv $gopDir/parse $gopDir/parse_backup 
fi

python3 gop2json.py $landDir $dictDir $gopDir $misInfo
