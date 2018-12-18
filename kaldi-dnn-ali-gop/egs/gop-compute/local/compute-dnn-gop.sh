#!/bin/sh

# Copyright 2016-2017  Author: Ming Tu

# Begin configuration section.
nj=1
cmd=run.pl
split_per_speaker=true
# Begin configuration.
# End configuration options.

echo "$0 $@"  # Print the command line for logging

[ -f path.sh ] && . ./path.sh # source the path.
. parse_options.sh || exit 1;

if [ $# != 5 ]; then
   echo "usage: local/compute-dnn-gop.sh <data-dir> <lang-dir> <src-dir> <gop-dir>"
   echo "e.g.:  local/compute-dnn-gop.sh data/train data/lang exp/tri1 exp/tri1_gop"
   echo "main options (for others, see top of script file)"
   echo "  --config <config-file>                           # config containing options"
   echo "  --nj <nj>                                        # number of parallel jobs"
   echo "  --cmd (utils/run.pl|utils/queue.pl <queue opts>) # how to run jobs."
   echo "  --split_per_speaker                              # split by speaker (true) or utterance (false)"
   exit 1;
fi

data=$1
online_ivector_dir=$2
lang=$3
srcdir=$4
dir=$5

for f in $data/text $lang/oov.int $srcdir/tree $srcdir/final.mdl; do
  [ ! -f $f ] && echo "$0: expected file $f to exist" && exit 1;
done

oov=`cat $lang/oov.int` || exit 1;
mkdir -p $dir/log
echo $nj > $dir/num_jobs
splice_opts=`cat $srcdir/splice_opts 2>/dev/null` # frame-splicing options.
cp $srcdir/splice_opts $dir 2>/dev/null # frame-splicing options.
cmvn_opts=`cat $srcdir/cmvn_opts 2>/dev/null`
cp $srcdir/cmvn_opts $dir 2>/dev/null # cmn/cmvn option.
delta_opts=`cat $srcdir/delta_opts 2>/dev/null`
cp $srcdir/delta_opts $dir 2>/dev/null

if $split_per_speaker; then
  sdata=$data/split$nj
  [[ -d $sdata && $data/feats.scp -ot $sdata ]] || split_data.sh $data $nj || exit 1;
else
  sdata=$data/split${nj}utt
  [[ -d $sdata && $data/feats.scp -ot $sdata ]] || split_data.sh --per-utt $data $nj || exit 1;
fi

utils/lang/check_phones_compatible.sh $lang/phones.txt $srcdir/phones.txt || exit 1;
cp $lang/phones.txt $dir || exit 1;

cp $srcdir/{tree,final.mdl} $dir || exit 1;
# cp $srcdir/final.occs $dir;

echo "$0: feature type is raw"

feats="ark,s,cs:apply-cmvn $cmvn_opts --utt2spk=ark:$sdata/JOB/utt2spk scp:$sdata/JOB/cmvn.scp scp:$sdata/JOB/feats.scp ark:- |"

#ivector_period=$(cat $online_ivector_dir/ivector_period) || exit 1;
ivectors="scp:$online_ivector_dir/ivector_online.scp"

echo "$0: computing GOP in $data using model from $srcdir, putting results in $dir"

mdl=$srcdir/final.mdl
tra="ark:utils/sym2int.pl --map-oov $oov -f 2- $lang/words.txt $sdata/JOB/text|";
$cmd JOB=1:$nj $dir/log/gop.JOB.log \
  compute-dnn-gop --use-gpu=no $dir/tree $dir/final.mdl $lang/L.fst "$feats" "$ivectors" "$tra" "ark,t:$dir/gop.JOB" "ark,t:$dir/align.JOB" "ark,t:$dir/phoneme_ll.JOB" || exit 1;

# Generate alignment
$cmd JOB=1:$nj $dir/log/align.JOB.log \
  linear-to-nbest "ark,t:$dir/align.JOB" "$tra" "" "" "ark:-" \| \
  lattice-align-words-lexicon "$lang/phones/align_lexicon.int" "$dir/final.mdl" "ark:-" "ark,t:$dir/aligned.JOB" || exit 1;
  #lattice-align-words "$lang/phones/word_boundary.int" "$dir/final.mdl" "ark:-" "ark,t:$dir/aligned.JOB" || exit 1;

$cmd JOB=1:$nj $dir/log/align_word.JOB.log \
  nbest-to-ctm "ark,t:$dir/aligned.JOB" "$dir/word.JOB.ctm"
$cmd JOB=1:$nj $dir/log/align_phone.JOB.log \
  lattice-to-phone-lattice "$dir/final.mdl" "ark,t:$dir/aligned.JOB" "ark:-" \| \
  nbest-to-ctm "ark:-" "$dir/phone.JOB.ctm" || exit 1;

for n in $(seq $nj); do
  cat $dir/gop.$n || exit 1;
done > $dir/gop.txt || exit 1

python local/ctm2textgrid.py $nj $dir $dir/aligned_textgrid $lang/words.txt $lang/phones.txt $data/utt2dur

# Convenience for debug
# apply-cmvn --utt2spk=ark:data/eval/split1/1/utt2spk scp:data/eval/split1/1/cmvn.scp scp:data/eval/split1/1/feats.scp ark:- | add-deltas ark:- ark,t:data/eval/feats.1.ark.txt
# utils/sym2int.pl --map-oov `cat data/lang/oov.int` -f 2- data/lang/words.txt data/eval/text > data/eval/trans
# compute-gmm-gop exp/tri1/tree exp/tri1/final.mdl data/lang/L.fst ark,t:data/eval/feats.1.ark.txt ark,t:data/eval/trans ark,t:gop.1

echo "$0: done computing GOP and generating alignments."
