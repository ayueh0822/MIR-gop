#!/bin/sh

# Copyright 2017   Author: Ming Tu
# Arguments:
# audio-dir: where audio files are stored
# data-dir: where extracted features are stored
# result-dir: where results are stored                               

echo "================ start ================"
date
echo "======================================="

set -e
#set -x

dnn=true
tone=false

nj=20 # number of parallel jobs. Set it depending on number of CPU cores
split_per_speaker=true # split by speaker (true) or sentence (false)

# Enviroment preparation
. ./cmd.sh
. ./path.sh

rm steps utils
[ -h steps ] || ln -s $KALDI_ROOT/egs/wsj/s5/steps
[ -h utils ] || ln -s $KALDI_ROOT/egs/wsj/s5/utils
. parse_options.sh || exit 1;

#if [ $# != 3 ]; then
#   echo "usage: run.sh <data-dir> <result-dir>"
#   echo "main options (for others, see top of script file)"
#   echo "  --dnn false                           # whether to use DNN model"
#   echo "  --nj                                  # number of jobs"
#   echo "  --split_per_speaker                   # split by speaker (true) or sentence (false)"
#   exit 1;
#fi

#audio_dir=$1
#data_dir=$2
#result_dir=$3

misproDir=~/kaldi/egs/pkasr/matbn_misproTestOnlyReplace
if [[ "$tone" = false ]]; then
  matbnDir=~/kaldi/egs/pkasr/matbn_200_no_tone
  lanfDir=$misproDir/lang/no_tone_decode
  gmmResultDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_noTone_testOnlyReplace_tri5_gmm
  dnnResultDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_noTone_testOnlyReplace_dnn
else
  matbnDir=~/kaldi/egs/pkasr/matbn_200_s0
  lanfDir=$misproDir/lang/ky92k_forpaift_v11
  gmmResultDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_withTone_testOnlyReplace_tri5_gmm
  dnnResultDir=~/MIR-gop/kaldi-dnn-ali-gop/egs/gop-compute/exp/matbn_mispro_withTone_testOnlyReplace_dnn
fi

#data=$misproDir/data/train

gmmModel=$matbnDir/exp/tri5
dnnModel=$matbnDir/exp/chain_tdnnf

gmmFeatsDir=$misproDir/feats/mfcc_pitch/train
dnnFeatsDir=$misproDir/feats/mfcc_hires_pitch/train
ivecDir=$misproDir/ivectors/train

# data preparation
#local/data_preparation.sh --nj $nj --dnn $dnn $audio_dir $data_dir
#./utils/data/get_utt2dur.sh $data

# move feats.scp & cmvn.scp to right path
# this for GMM
# cp $gmmFeatsDir/feats.scp $misproDir/data/train/
# cp $gmmFeatsDir/cmvn.scp $misproDir/data/train/

# this for DNN
# cp $dnnFeatsDir/feats.scp $misproDir/data/train/
# cp $dnnFeatsDir/cmvn.scp $misproDir/data/train/

cp $misproDir/data/train/text $gmmFeatsDir
cp $misproDir/data/train/text $dnnFeatsDir

# Calculation
if [[ "$dnn" = false ]]; then
  echo "Using GMM model!"
  ./utils/data/get_utt2dur.sh $gmmFeatsDir
  local/compute-gmm-gop.sh --nj "$nj" --cmd "$decode_cmd" --split_per_speaker "$split_per_speaker" $gmmFeatsDir $lanfDir $gmmModel $gmmResultDir   ### gmm model
else
  echo "Using DNN model!"
  ./utils/data/get_utt2dur.sh $dnnFeatsDir
  local/compute-dnn-gop.sh --nj "$nj" --cmd "$decode_cmd" --split_per_speaker "$split_per_speaker" $dnnFeatsDir $ivecDir $lanfDir \
             $dnnModel $dnnResultDir    ### dnn model
fi

echo "================ finish ================"
date
echo "========================================"
