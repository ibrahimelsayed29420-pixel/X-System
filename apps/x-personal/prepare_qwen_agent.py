from x_personal.brain import local_request

result=local_request('/api/create',{'model':'x-qwen-agent:latest','from':'qwen3:4b-instruct',
    'stream':False,'parameters':{'temperature':.2,'num_ctx':8192,'num_predict':256}},timeout=120)
if result.get('status')!='success':raise RuntimeError('Local agent model creation failed')
print('Local non-thinking tool model prepared from existing Qwen weights')
