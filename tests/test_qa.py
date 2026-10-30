import numpy as np
import pytest
from transformers import BertTokenizerFast
from src.predict import tokenize_for_qa, decode_windows, apply_threshold
from src.train import prepare_features
from src.metrics import score_answer
from src.threshold import sweep_threshold

@pytest.fixture
def tokenizer(tmp_path):
    vocab=tmp_path/'vocab.txt'
    vocab.write_text('\n'.join(['[PAD]','[UNK]','[CLS]','[SEP]','[MASK]','where','alpha','omega','cafe','?']),encoding='utf-8')
    return BertTokenizerFast(vocab_file=str(vocab),do_lower_case=True)

def test_training_answer_in_last_window(tokenizer):
    context='alpha '*40+'omega'
    batch={'context':[context], 'question':['where?'],
           'answers':[{'text':['omega'],'answer_start':[context.index('omega')]}]}
    features=prepare_features(batch,tokenizer,16,4)
    cls=features['input_ids'][0].index(tokenizer.cls_token_id)
    assert len(features['input_ids'])>1
    assert features['start_positions'][0]==cls
    assert features['start_positions'][-1]!=cls
    assert features['input_ids'][-1][features['start_positions'][-1]]==tokenizer.convert_tokens_to_ids('omega')

def test_no_answer_uses_cls(tokenizer):
    features=prepare_features({'context':['alpha'],'question':['where?'],
                               'answers':[{'text':[],'answer_start':[]}]},tokenizer,16,4)
    assert features['start_positions']==[0] and features['end_positions']==[0]

def test_decoder_ignores_question_and_padding_and_preserves_unicode(tokenizer):
    context='alpha '*40+'café omega'
    features=tokenize_for_qa({'context':[context],'question':['omega?']},tokenizer,16,4)
    starts=np.full((len(features['input_ids']),16),-20.)
    ends=starts.copy()
    for i in range(len(starts)):
        starts[i,0]=ends[i,0]=0
        starts[i,1]=ends[i,1]=100 # question must be ignored
        for j,(a,b) in enumerate(features['offset_mapping'][i]):
            if features.sequence_ids(i)[j]==1 and context[a:b]=='café':
                starts[i,j]=ends[i,j]=10
    result=decode_windows(context,features,starts,ends,tokenizer)
    assert result['answer']=='café'
    assert result['start']==context.index('café')
    assert result['null_diff']==-20
    assert apply_threshold(result,0)['answer']=='café'
    assert apply_threshold(result,-21)['answer'] is None

def test_maximum_question_does_not_break_windowing(tokenizer):
    features=tokenize_for_qa({'context':['alpha '*900],'question':['?'*500]},tokenizer)
    assert len(features['input_ids'])>1
    assert all(len(x)==384 for x in features['input_ids'])

def test_metrics_and_threshold():
    assert score_answer('The café',['café'])==(1.,1.)
    assert score_answer(None,[])==(1.,1.)
    assert score_answer('red apple',['apple'])==(0.,2/3)
    rows=[{'raw':{'answer':'alpha','start':0,'null_diff':-3},'references':['alpha']},
          {'raw':{'answer':'wrong','start':0,'null_diff':3},'references':[]}]
    threshold=sweep_threshold(rows)
    assert -3<=threshold<3
