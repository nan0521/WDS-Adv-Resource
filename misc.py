import os
import requests
import UnityPy
import json

WDS_Env_Url = os.environ.get("WDS_ENV_URL")
WDS_Env_Req = requests.post(WDS_Env_Url)
WDS_Env = (WDS_Env_Req.json())['result']

masterlistUrl = os.environ.get("WDS_MASTERLIST_URL")

# spine setting
spineFolder = './spine/'
if not os.path.exists(spineFolder):
    os.makedirs(spineFolder)

spinemaster = json.load(open('./SpineMasterlist.json', 'rb')) if os.path.exists('./SpineMasterlist.json') else []
spinelist = [item["Id"] for item in spinemaster]

# cards setting
cardsFolder = './cards'
if not os.path.exists(cardsFolder):
    os.makedirs(cardsFolder)

bgFolder = './background'
if not os.path.exists(bgFolder):
    os.makedirs(bgFolder)

bgmaster = json.load(open('./BackgroundMasterlist.json', 'rb')) if os.path.exists('./BackgroundMasterlist.json') else []

# load 2d-catalog master data
catalog_master = requests.get(f'{masterlistUrl}/assets/2d-catalog.json')
if catalog_master.status_code == 200:
    catalog_data = catalog_master.json()

    spine_urlid = [index for (index, item) in enumerate(catalog_data['m_InternalIdPrefixes']) if 'adventurecharacterstand_assets_adventurecharacterstands' in item][0]
    card_urlid = [index for (index, item) in enumerate(catalog_data['m_InternalIdPrefixes']) if 'charactercardtextures_assets_charactercardtextures' in item][0]
    bg_urlid = [index for (index, item) in enumerate(catalog_data['m_InternalIdPrefixes']) if 'adventurebackground_assets_adventurebackgrounds' in item][0]

    for asset in catalog_data['m_InternalIds']:

        # spine
        if asset.startswith(f'{spine_urlid}#'):
            filename = asset.split('/')[-1]
            spineId = filename.split('.')[0]

            # check the spine data isexit
            if not spineId in spinelist:
                fullurl = f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/adventurecharacterstand_assets_adventurecharacterstands/{filename}'                
                assetsReq = requests.get(fullurl)
                if assetsReq.status_code == 200:
                    assetsbundle = UnityPy.load(assetsReq.content)
                    for obj in assetsbundle.objects:
                        if obj.type.name == "Texture2D":
                            data = obj.read()
                            data.image.save(os.path.join(spineFolder, f'{data.name}.png'))

                        if obj.type.name == "TextAsset":
                            data = obj.read()
                            open(os.path.join(spineFolder, data.name), "wb").write(bytes(data.script))

                spinemaster.append({
                    "Id" : int(spineId),
                    "CharacterId" : int(spineId[0 : 3]),
                    "CompanyId" : int(spineId[0]),
                })

        # card Image
        if asset.startswith(f'{card_urlid}#'):
            filename = asset.split('/')[-1]
            cardId = filename.split('.')[0]

            fullurl = f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/charactercardtextures_assets_charactercardtextures/{filename}'
            assetsReq = requests.get(fullurl)
            if assetsReq.status_code == 200:
                assetsbundle = UnityPy.load(assetsReq.content)
                for path, obj in assetsbundle.container.items():
                    if obj.type.name == "Sprite" and path.endswith('.jpg'):
                        data = obj.read()
                        if data.name == cardId:
                            data.image.save(os.path.join(cardsFolder, f'{data.name}.png'))
        
        # backgorund
        if asset.startswith(f'{bg_urlid}#'):
            filename = asset.split('/')[-1]
            bgId = filename.split('.')[0]

            if not bgId in bgmaster:
                fullurl = f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/adventurebackground_assets_adventurebackgrounds/{filename}'
                assetsReq = requests.get(fullurl)
                if assetsReq.status_code == 200:
                    assetsbundle = UnityPy.load(assetsReq.content)
                    for obj in assetsbundle.objects:
                        if obj.type.name == "Texture2D":
                            data = obj.read()
                            if data.name == bgId:
                                data.image.save(os.path.join(bgFolder, f'{data.name}.png'))
                                bgmaster.append(data.name)

# save spine list
json_data = json.dumps(spinemaster, indent=4, ensure_ascii=False)
open(f'./SpineMasterlist.json', "w", encoding='utf8').write(json_data)

# save background list
bg_json_data = json.dumps(bgmaster, indent=4, ensure_ascii=False)
open(f'./BackgroundMasterlist.json', "w", encoding='utf8').write(bg_json_data)