// gopbin/compute-gop-gmm.cc

// Copyright 2016-2017  Junbo Zhang
//                      Ming Tu

// This program based on Kaldi (https://github.com/kaldi-asr/kaldi).
// However, this program is NOT UNDER THE SAME LICENSE of Kaldi's.
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// version 2 as published by the Free Software Foundation;
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "gop/dnn-gop.h"

int main(int argc, char *argv[]) {
  try {
    using namespace kaldi;
    
    const char *usage =
        "Compute GOP with DNN-based models.\n"
        "Usage:   compute-dnn-gop [options] tree-in model-in lexicon-fst-in feature-rspecifier online_ivector-rspecifier "
        "transcriptions-rspecifier gop-wspecifier alignment-wspecifier phoneme_log_likelihood-wspecifier\n"
        "e.g.: \n"
        " compute-gmm-gop tree 1.mdl lex.fst scp:train.scp ark:train.tra ark,t:gop.1 ark,t:algin.1 ark,t:phn_ll.1\n";

    ParseOptions po(usage);
    std::string use_gpu = "yes";
    po.Register("use-gpu", &use_gpu,
                 "yes|no|optional|wait, only has effect if compiled with CUDA");

    po.Read(argc, argv);
    if (po.NumArgs() != 9) {
      po.PrintUsage();
      exit(1);
    }
#if HAVE_CUDA==1
    printf("fucc\n");
    CuDevice::Instantiate().SelectGpuId(use_gpu);
#endif

    std::string tree_in_filename = po.GetArg(1);
    std::string model_in_filename = po.GetArg(2);
    std::string lex_in_filename = po.GetArg(3);
    std::string feature_rspecifier = po.GetArg(4);
    std::string online_ivector_rspecifier = po.GetArg(5);
    std::string transcript_rspecifier = po.GetArg(6);
    std::string gop_wspecifier = po.GetArg(7);
    std::string alignment_wspecifier = po.GetArg(8);
    std::string phn_ll_wspecifier = po.GetArg(9);

    SequentialBaseFloatMatrixReader feature_reader(feature_rspecifier);
    RandomAccessBaseFloatMatrixReader online_ivector_reader(online_ivector_rspecifier);
    RandomAccessInt32VectorReader transcript_reader(transcript_rspecifier);
    BaseFloatVectorWriter gop_writer(gop_wspecifier);
    Int32VectorWriter alignment_writer(alignment_wspecifier);
    BaseFloatVectorWriter phn_ll_writer(phn_ll_wspecifier);

    DnnGop gop;
    gop.Init(tree_in_filename, model_in_filename, lex_in_filename);

    // Compute for each utterance
    for (; !feature_reader.Done(); feature_reader.Next()) {
      std::string utt = feature_reader.Key();
      if (! transcript_reader.HasKey(utt)) {
        KALDI_WARN << "Can not find alignment for utterance " << utt;        
        continue;
      }

      //KALDI_LOG << "Processing utterance " << utt;

      const Matrix<BaseFloat> &features = feature_reader.Value();
      const Matrix<BaseFloat> *online_ivector = &online_ivector_reader.Value(utt);
      //KALDI_LOG << "ivector dimension is " << online_ivector->NumRows();
      const std::vector<int32> &transcript = transcript_reader.Value(utt);

      gop.Compute(features, online_ivector, transcript);
      gop_writer.Write(utt, gop.Result());
      alignment_writer.Write(utt, gop.get_alignment());
      phn_ll_writer.Write(utt, gop.get_phn_ll());

      //=================================================================
      
      Vector<BaseFloat> word_seq;
      Vector<BaseFloat> phone_seq;
    
      word_seq.Resize(transcript.size());
      for (int i = 0; i < transcript.size(); i++)
        word_seq(i) = transcript[i];

      std::vector<int32> phone_seq_tmp = gop.Phonemes();
      phone_seq.Resize(phone_seq_tmp.size());
      for (int i=0; i<phone_seq_tmp.size(); i++)
        phone_seq(i) = phone_seq_tmp[i];    

      gop_writer.Write(utt + "________text", word_seq);
      gop_writer.Write(utt + "_______phone", phone_seq);
      gop_writer.Write(utt + "____interval", gop.get_phn_itvl());

      std::vector< Vector<BaseFloat> > compete_phone_likelihood;
      compete_phone_likelihood = gop.get_phn_cmpt();
      for (int i=0; i<compete_phone_likelihood.size(); i++){
       
        std::ostringstream ss;
        ss << phone_seq(i);
        std::string ph(ss.str());

        gop_writer.Write(ph, compete_phone_likelihood[i]);
      }
          
      
      //=================================================================

    }
    KALDI_LOG << "Done.";
# if HAVE_CUDA==1
    CuDevice::Instantiate().PrintProfile();
#endif
    return 0;
  } catch(const std::exception &e) {
    std::cerr << e.what();
    return -1;
  }
}
