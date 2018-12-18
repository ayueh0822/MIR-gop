. ./path.sh
. ./cmd.sh

cmd=run.pl

data=/home/kaldi/kaldi/egs/pkasr/matbn_mispro/data/train

nj=10
lang=/home/kaldi/kaldi/egs/pkasr/matbn_mispro/lang/ky92k_forpaift_v11
dir=/home/kaldi/kaldi-dnn-ali-gop/egs/gop-compute/exp/eval_matbn_mispro_tri4_advanced
split_per_speaker=false;

if $split_per_speaker; then
  sdata=$data/split$nj
    [[ -d $sdata && $data/feats.scp -ot $sdata ]] || split_data.sh $data $nj || exit 1;
    else
      sdata=$data/split${nj}utt
        [[ -d $sdata && $data/feats.scp -ot $sdata ]] || split_data.sh --per-utt $data $nj || exit 1;
        fi

oov=`cat $lang/oov.int` || exit 1;
tra="ark:utils/sym2int.pl --map-oov $oov -f 2- $lang/words.txt $sdata/JOB/text|";
$cmd JOB=1:$nj ./align.JOB.log \
  linear-to-nbest "ark,t:$dir/align.JOB" "$tra" "" "" "ark:-" \| \
  lattice-align-words-lexicon "$lang/phones/align_lexicon.int" "$dir/final.mdl" "ark:-" "ark,t:$dir/aligned.JOB" || exit 1;
  #lattice-align-words "$lang/phones/word_boundary.int" "$dir/final.mdl" "ark:-" "ark,t:$dir/aligned.JOB" || exit 1;
