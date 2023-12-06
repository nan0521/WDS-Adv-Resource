import os
import requests
import shutil
import json
from pydub import AudioSegment

WDS_Env_Url = os.environ.get("WDS_ENV_URL")
WDS_Env_Req = requests.post(WDS_Env_Url)
WDS_Env = (WDS_Env_Req.json())['result']

masterlistUrl = os.environ.get("WDS_MASTERLIST_URL")

# bgm dir
bgm_temp_dir = './bgm_temp'
bgm_dir = './bgm'
bgm_temp_wav_dir = './bgm_wav_temp'
if not os.path.exists(bgm_temp_dir):
    os.makedirs(bgm_temp_dir)

#se dir
se_temp_dir = './se_temp'
se_dir = './se'
se_temp_wav_dir = './se_wav_temp'
if not os.path.exists(se_temp_dir):
    os.makedirs(se_temp_dir)

#acb -> wav -> mp3
def acbToMp3(input_dir, temp_dir, output_dir):
    if os.path.exists(input_dir):

        for fname in os.listdir(input_dir):

            acb_full_path = os.path.join(input_dir, fname)

            # 生成wav的位置
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            # 生成mp3的位置
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # run command and save to temp dir
            os.system(f'./vgmstream-cli -S 0 -o {temp_dir}/?n.wav -i {acb_full_path}')

            # exchange to mp3 format 
            for wavfile in os.listdir(temp_dir):
                if wavfile.endswith(".wav"):
                    full_wav_path = os.path.join(temp_dir, wavfile)
                    sound = AudioSegment.from_wav(full_wav_path)
                    sound.export(os.path.join(output_dir, wavfile.replace('.wav', '.mp3')), format="mp3")
            
            # del temp file
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        # del file
        if os.path.exists(input_dir):
            shutil.rmtree(input_dir)


catalog_master = requests.get(f'{masterlistUrl}/assets/cri-catalog.json')
if catalog_master.status_code == 200:
    catalog_data = catalog_master.json()

    bgm_urlid = [index for (index, item) in enumerate(catalog_data['m_InternalIdPrefixes']) if 'adventurebgm_assets_adventurebgm' in item][0]
    se_urlid = [index for (index, item) in enumerate(catalog_data['m_InternalIdPrefixes']) if 'adventurese_assets_se' in item][0]

    for asset in catalog_data['m_InternalIds']:

        # bgm
        if asset.startswith(f'{bgm_urlid}#'):
            filename = asset.split('/')[-1]
            name = filename.split('.')[0]

            voiceRes = requests.get(f'{WDS_Env["assetUrl"]}/cri-assets/Android/{WDS_Env["assetVersion"]}/cridata_remote_assets_criaddressables/{name}.acb.bundle')
            if voiceRes.status_code == 200:
                open(os.path.join(bgm_temp_dir, f'{name}.acb'), "wb").write(voiceRes.content)

        # se
        if asset.startswith(f'{se_urlid}#'):
            filename = asset.split('/')[-1]
            name = filename.split('.')[0]

            voiceRes = requests.get(f'{WDS_Env["assetUrl"]}/cri-assets/Android/{WDS_Env["assetVersion"]}/cridata_remote_assets_criaddressables/{name}.acb.bundle')
            if voiceRes.status_code == 200:
                open(os.path.join(se_temp_dir, f'{name}.acb'), "wb").write(voiceRes.content)

    # bgm
    acbToMp3(bgm_temp_dir, bgm_temp_wav_dir, bgm_dir)
    bgm_masterlist = []
    for mp3file in os.listdir(bgm_dir):
        if mp3file.endswith("mp3"):
            bgm_masterlist.append(mp3file.split('.mp3')[0])
    bgm_data = json.dumps(bgm_masterlist, indent=4, ensure_ascii=False)
    open('./BGMMasterlist.json', "w", encoding='utf8').write(bgm_data)

    # se 
    acbToMp3(se_temp_dir, se_temp_wav_dir, se_dir)
    se_masterlist = []
    for mp3file in os.listdir(se_dir):
        if mp3file.endswith("mp3"):
            se_masterlist.append(mp3file.split('.mp3')[0])
    se_data = json.dumps(se_masterlist, indent=4, ensure_ascii=False)
    open('./SEMasterlist.json', "w", encoding='utf8').write(se_data)