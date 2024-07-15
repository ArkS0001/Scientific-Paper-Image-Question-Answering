# Scientific-Paper-Image-Question-Answering
SPIQA



  Download the whole dataset (all splits).

    from huggingface_hub import snapshot_download
    snapshot_download(repo_id="google/spiqa", repo_type="dataset", local_dir='.') ### Mention the local directory path

   Download specific file.

    from huggingface_hub import hf_hub_download
    hf_hub_download(repo_id="google/spiqa", filename="test-A/SPIQA_testA.json", repo_type="dataset", local_dir='.') ### Mention the local directory path

Questions and Answers from a Specific Paper in test-A

    import json
    testA_metadata = json.load(open('test-A/SPIQA_testA.json', 'r'))
    paper_id = '1702.03584v3'
    print(testA_metadata[paper_id]['qa'])

Questions and Answers from a Specific Paper in test-B

    import json
    testB_metadata = json.load(open('test-B/SPIQA_testB.json', 'r'))
    paper_id = '1707.07012'
    print(testB_metadata[paper_id]['question']) ## Questions
    print(testB_metadata[paper_id]['composition']) ## Answers

Questions and Answers from a Specific Paper in test-C

    import json
    testC_metadata = json.load(open('test-C/SPIQA_testC.json', 'r'))
    paper_id = '1808.08780'
    print(testC_metadata[paper_id]['question']) ## Questions
    print(testC_metadata[paper_id]['answer']) ## Answers
