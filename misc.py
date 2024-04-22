import os
import requests
import UnityPy
import json
import datetime
import pytz

WDS_Env_Url = os.environ.get("WDS_ENV_URL")
WDS_Env_Req = requests.post(WDS_Env_Url)
WDS_Env = (WDS_Env_Req.json())['result']

masterlistUrl = os.environ.get("WDS_MASTERLIST_URL")

# spine setting
spineFolder = './spine/'
if not os.path.exists(spineFolder):
    os.makedirs(spineFolder)

spinemaster = []

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
            IsExitImg = False
            IsExitMeta = False
            try:
                fullurl = f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/adventurecharacterstand_assets_adventurecharacterstands/{filename}'                
                assetsReq = requests.get(fullurl)
                if assetsReq.status_code == 200:
                    assetsbundle = UnityPy.load(assetsReq.content)
                    for obj in assetsbundle.objects:
                        if obj.type.name == "Texture2D":
                            data = obj.read()
                            data.image.save(os.path.join(spineFolder, f'{spineId}.png'))
                            IsExitImg = True

                        if obj.type.name == "TextAsset":
                            data = obj.read()
                            ext = data.name.split('.')[-1]
                            open(os.path.join(spineFolder, f'{spineId}.{ext}'), "wb").write(bytes(data.script))
                            IsExitMeta = True

                if IsExitImg and IsExitMeta:
                    spinemaster.append({
                        "Id" : int(spineId),
                        "CharacterId" : int(spineId[0 : 3]),
                        "CompanyId" : int(spineId[0]),
                    })
            except:
                print(spineId)

        # card Image
        if asset.startswith(f'{card_urlid}#'):
            filename = asset.split('/')[-1]
            cardId = filename.split('.')[0]
            try:
                fullurl = f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/charactercardtextures_assets_charactercardtextures/{filename}'
                assetsReq = requests.get(fullurl)
                if assetsReq.status_code == 200:
                    assetsbundle = UnityPy.load(assetsReq.content)
                    for path, obj in assetsbundle.container.items():
                        if obj.type.name == "Sprite" and path.endswith('.jpg'):
                            data = obj.read()
                            if data.name == cardId:
                                data.image.save(os.path.join(cardsFolder, f'{data.name}.png'))
            except:
                print(cardId)
        
        # backgorund
        if asset.startswith(f'{bg_urlid}#'):
            filename = asset.split('/')[-1]
            bgId = filename.split('.')[0]
            try:
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
            except:
                print(bgId)


# save spine list
json_data = json.dumps(spinemaster, indent=4, ensure_ascii=False)
open(f'./SpineMasterlist.json', "w", encoding='utf8').write(json_data)

# save background list
bg_json_data = json.dumps(bgmaster, indent=4, ensure_ascii=False)
open(f'./BackgroundMasterlist.json', "w", encoding='utf8').write(bg_json_data)


gamemaster = json.load(open('./GameStoryMasterlist.json', 'rb')) if os.path.exists('./GameStoryMasterlist.json') else {
            "LatestDate": '',
            "ScriptVersion" : "1.0.0",
            "StoryMaster" : {
                "Main" : [],
                "Event" : [],
                "Side" : [],
                "Spot" : [],
                "Poster" : [],
                "Special" : [],
            }
        }
date = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
gamemaster['LatestDate'] = date.strftime("%Y-%m-%d %H:%M:%S")
gamemaster_data = json.dumps(gamemaster, indent=4, ensure_ascii=False)
open(f'./GameStoryMasterlist.json', "w", encoding='utf8').write(gamemaster_data)
