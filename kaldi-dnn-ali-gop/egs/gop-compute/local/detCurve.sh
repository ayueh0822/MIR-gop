isTone=false

if [[ "$isTone" = false ]]; then
    echo "No tone!"
    gmmDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_noTone_testOnlyReplace_tri5_gmm
    dnnDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_noTone_testOnlyReplace_dnn
else
    echo "With tone!"
    gmmDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_withTone_testOnly_tri5_gmm
    dnnDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_withTone_testOnly_dnn
fi

python3 detCurve.py $isTone $gmmDir $dnnDir