import msgpack_lz4block
import json
import requests
import os
import datetime
import pytz
import UnityPy

script_version = os.environ.get("SCRIPT_VERSION")

WDS_Env_Url = os.environ.get("WDS_ENV_URL")
WDS_Env_Req = requests.post(WDS_Env_Url)
WDS_Env = (WDS_Env_Req.json())['result']

masterlistUrl = os.environ.get("WDS_MASTERLIST_URL")

EPBase_dir = './episode'
eventImage_dir = './image/eventLogo'
sideImage_dir = './image/cardIcon'
posterImage_dir = './image/posterIcon'
temp_dir = './temp'

keymap = [
    "Id",
    "EpisodeMasterId",
    "Order",
    "GroupOrder",
    "Effect",
    "SpeakerName",
    "FontSize",
    "Phrase",
    "Title",
    "BackgroundImageFileName",
    "BackgroundCharacterImageFileName",
    "BackgroundImageFileFadeType",
    "BgmFileName",
    "SeFileName",
    "StillPhotoFileName",
    "MovieFileName",
    "WindowEffect",
    "SceneCameraMasterId",
    "VoiceFileName",
    "CharacterMotions",
    "SpeakerIconId",
    "FadeValue1",
    "FadeValue2",
    "FadeValue3",
]

motionkeymap = [
    "slotNumber",
    "FacialExpressionMasterId",
    "HeadMotionMasterId",
    "HeadDirectionMasterId",
    "BodyMotionMasterId",
    "LipSyncMasterId",
    "SpineId",
    "CharacterAppearanceType",
    "CharacterPosition",
    "CharacterLayerType",
    "SpineSize"
]

orderToNum = {
    "First" : 1,
    "Second" : 2
}

posterTypeToNum = {
    "Information" : 0,
    "Chapter1" : 1,
    "Chapter2" : 2,
    "Chapter3" : 3,
    "Chapter4" : 4,
    "AfterTalk" : 5
}

def addKey(listcontent):
    list = []
    for data in listcontent:
        motions = []
        for motion in data[19]:
            charmotion = {}
            for mid in range(len(motionkeymap)):
                if not motion[mid] == None:
                    charmotion[motionkeymap[mid]] = motion[mid]
            motions.append(charmotion)

        unit = {}
        for unid in range(len(keymap)):
            if unid == 19:
                unit[keymap[unid]] = motions
            elif not data[unid] == None:
                unit[keymap[unid]] = data[unid]

        list.append(unit)
    
    return list

def createFormat(EpisodeId, StoryType, Order, Title, EpisodeDetail, orderlist):
    
    if Title == "":
        Title = "？？？"

    script = {
        "EpisodeId" : EpisodeId,
        "StoryType" : StoryType,
        "Order" : Order,
        "Prev" : None,
        "Next" : None,
        "Title" : Title,
        "EpisodeDetail" : EpisodeDetail,
    }

    if EpisodeId - 1 in orderlist:
        script["Prev"] = EpisodeId - 1

    if EpisodeId + 1 in orderlist:
        script["Next"] = EpisodeId + 1

    return script

if os.path.exists('./GameStoryMasterlist.json'):
    GameStoryMasterlist = json.load(open('./GameStoryMasterlist.json', 'rb'))
    if not GameStoryMasterlist['ScriptVersion'] == script_version:
        GameStoryMasterlist = {
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
else :
    GameStoryMasterlist = {
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
    
if not os.path.exists(EPBase_dir):
    os.makedirs(EPBase_dir)

if not os.path.exists(sideImage_dir):
    os.makedirs(sideImage_dir)

if not os.path.exists(eventImage_dir):
    os.makedirs(eventImage_dir)

if not os.path.exists(posterImage_dir):
    os.makedirs(posterImage_dir)

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

# ------------------------ Main Episode ------------------------
# 生成主線資訊
masterlistres = requests.get(f'{masterlistUrl}/StoryMaster.json')
if masterlistres.status_code == 200:
    for data in masterlistres.json() :
        if data["Type"] == 2 or data["Type"] == "Event":
            continue
        GroupIsexit = [item for item in GameStoryMasterlist["StoryMaster"]["Main"] if item.get('Id') == data["Id"]]
        if not len(GroupIsexit) > 0:
            GameStoryMasterlist["StoryMaster"]["Main"].append({
                "Id" : data["Id"],
                "CompanyId": data["CompanyMasterId"],
                "ChapterOrder": data["ChapterOrder"],
                "Episode" : []
            })
    GameStoryMasterlist["StoryMaster"]["Main"].sort(key = lambda x: x["Id"] )

masterlistres = requests.get(f'{masterlistUrl}/EpisodeMaster.json')
if masterlistres.status_code == 200:
    EpisodeMasterlist = masterlistres.json() 
    for data in EpisodeMasterlist:
        GroupIsexit = [item for item in GameStoryMasterlist["StoryMaster"]["Main"] if item.get('Id') == data["StoryMasterId"]][0]
        if GroupIsexit:
            # 檢查列表中屬於這個故事所有的Episode
            orderlist = [item["Id"] for item in EpisodeMasterlist if item.get('StoryMasterId') == data["StoryMasterId"]]
            # 生成故事文檔
            res = requests.get(f'{WDS_Env["masterDataUrl"]}/scenes/{data["Id"]}.bin')
            if res.status_code == 200:
                msgdata = msgpack_lz4block.deserialize(res.content)
                to_json = createFormat(data["Id"], 1, data["Order"], data["Title"], addKey(msgdata), orderlist)
                json_data = json.dumps(to_json, indent=4, ensure_ascii=False)
                open(os.path.join(EPBase_dir, f'{data["Id"]}.json'), "w", encoding='utf8').write(json_data)
            # 檢查列表中是否存在
            Isexit = [item for item in GroupIsexit["Episode"] if item.get('EpisodeId') == data["Id"]]
            if not len(Isexit) > 0:
                GroupIsexit["Episode"].append({
                    "EpisodeId" : data["Id"],
                    "Title" : data["Title"],
                    "Order" : data["Order"],
                })
                # 生成語音檔
                voiceRes = requests.get(f'{WDS_Env["assetUrl"]}/cri-assets/Android/{WDS_Env["assetVersion"]}/cridata_remote_assets_criaddressables/{data["Id"]}.acb.bundle')
                if voiceRes.status_code == 200:
                    open(os.path.join(temp_dir, f'{data["Id"]}.acb'), "wb").write(voiceRes.content)

            # 列表排序
            GroupIsexit["Episode"].sort(key = lambda x: x["EpisodeId"] )

# ------------------------ Event Episode ------------------------
# 生成活動資訊
StoryEvent = requests.get(f'{masterlistUrl}/StoryEventMaster.json')
if StoryEvent.status_code == 200:
    for story in StoryEvent.json():
        GroupIsexit = [item for item in GameStoryMasterlist["StoryMaster"]["Event"] if item.get('Id') == story["Id"]]
        if not len(GroupIsexit) > 0:
            GameStoryMasterlist["StoryMaster"]["Event"].append({
                "Id" : story["Id"],
                "Title": story["Title"],
                "Episode" : []
            })
            # 更新卡片照片
            assetsReq = requests.get(f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/eventslogo_assets_events/logo_{story["Id"]}.bundle')
            assetsbundle = UnityPy.load(assetsReq.content)
            for obj in assetsbundle.objects:
                if obj.type.name == "Texture2D":
                    data = obj.read()
                    data.image.save(os.path.join(eventImage_dir, f'logo_{story["Id"]}.png'))

    GameStoryMasterlist["StoryMaster"]["Event"].sort(key = lambda x: x["Id"] )

masterlistres = requests.get(f'{masterlistUrl}/StoryEventEpisodeMaster.json')
if masterlistres.status_code == 200:
    EpisodeMasterlist = masterlistres.json()
    for data in EpisodeMasterlist:
        GroupIsexit = [item for item in GameStoryMasterlist["StoryMaster"]["Event"] if item.get('Id') == data["StoryMasterId"]][0]
        if GroupIsexit:
            # 檢查列表中屬於這個故事所有的Episode
            orderlist = [item["Id"] for item in EpisodeMasterlist if item.get('StoryMasterId') == data["StoryMasterId"]]
            # 生成故事文檔
            res = requests.get(f'{WDS_Env["masterDataUrl"]}/scenes/{data["Id"]}.bin')
            if res.status_code == 200:
                msgdata = msgpack_lz4block.deserialize(res.content)
                to_json = createFormat(data["Id"], 2, data["Order"], data["Title"], addKey(msgdata), orderlist)
                json_data = json.dumps(to_json, indent=4, ensure_ascii=False)
                open(os.path.join(EPBase_dir, f'{data["Id"]}.json'), "w", encoding='utf8').write(json_data)
            # 檢查列表中是否存在
            Isexit = [item for item in GroupIsexit["Episode"] if item.get('EpisodeId') == data["Id"]]
            if not len(Isexit) > 0:
                GroupIsexit["Episode"].append({
                    "EpisodeId" : data["Id"],
                    "Title" : data["Title"],
                    "Order" : data["Order"],
                })
                # 生成語音檔
                voiceRes = requests.get(f'{WDS_Env["assetUrl"]}/cri-assets/Android/{WDS_Env["assetVersion"]}/cridata_remote_assets_criaddressables/{data["Id"]}.acb.bundle')
                if voiceRes.status_code == 200:
                    open(os.path.join(temp_dir, f'{data["Id"]}.acb'), "wb").write(voiceRes.content)
            # 列表排序
            GroupIsexit["Episode"].sort(key = lambda x: x["EpisodeId"] )

# ------------------------ Side Episode ------------------------
# 生成角色資訊
charBase = requests.get(f'{masterlistUrl}/CharacterBaseMaster.json')
if charBase.status_code == 200:
    for chardata in charBase.json():
        GroupIsexit = [item for item in GameStoryMasterlist["StoryMaster"]["Side"] if item.get('Id') == chardata["Id"]]
        if not len(GroupIsexit) > 0:
            GameStoryMasterlist["StoryMaster"]["Side"].append({
                "Id" : chardata["Id"],
                "Name": chardata["Name"],
                "CompanyMasterId" : chardata["CompanyMasterId"],
                "Groups" : []
            })
    GameStoryMasterlist["StoryMaster"]["Side"].sort(key = lambda x: x["Id"] )

# 生成卡片資訊
masterlistres = requests.get(f'{masterlistUrl}/CharacterMaster.json')
if masterlistres.status_code == 200:
    CharacterMasterdata = masterlistres.json()
    for char in GameStoryMasterlist["StoryMaster"]["Side"]:
        charGroups = [item for item in CharacterMasterdata if item.get('CharacterBaseMasterId') == char["Id"]]
        for carddata in charGroups:
            Isexit = [item for item in char["Groups"] if item.get('Id') == carddata["Id"]]
            if not len(Isexit) > 0:
                char["Groups"].append({
                    "Id" : carddata["Id"],
                    "Title": carddata["Name"],
                    "Episode" : []
                })
        char["Groups"].sort(key = lambda x: x["Id"] )

Side_Update = False
masterlistres = requests.get(f'{masterlistUrl}/CharacterEpisodeMaster.json')
if masterlistres.status_code == 200:
    charepisodedata = masterlistres.json()
    for data in GameStoryMasterlist["StoryMaster"]["Side"]:
        for group in data["Groups"]:
            EPData = [item for item in charepisodedata if item.get('CharacterMasterId') == group["Id"]]
            for ep in EPData:
                # 檢查列表中屬於這個故事所有的Episode
                orderlist = [item["Id"] for item in EPData]
                # 生成故事文檔
                res = requests.get(f'{WDS_Env["masterDataUrl"]}/scenes/{ep["EpisodeMasterId"]}.bin')
                if res.status_code == 200:
                    msgdata = msgpack_lz4block.deserialize(res.content)
                    to_json = createFormat(ep["EpisodeMasterId"], 3, orderToNum[ep["EpisodeOrder"]], group["Title"], addKey(msgdata), orderlist)
                    json_data = json.dumps(to_json, indent=4, ensure_ascii=False)
                    open(os.path.join(EPBase_dir, f'{ep["EpisodeMasterId"]}.json'), "w", encoding='utf8').write(json_data)
                # 檢查列表中是否存在
                Isexit = [item for item in group["Episode"] if item.get('EpisodeId') == ep["EpisodeMasterId"]]
                if not len(Isexit) > 0:
                    group["Episode"].append({
                        "EpisodeId" : ep["EpisodeMasterId"],
                        "Order": orderToNum[ep["EpisodeOrder"]]
                    })
                    # 卡片照片需要更新
                    Side_Update = True
                    # 生成語音檔
                    voiceRes = requests.get(f'{WDS_Env["assetUrl"]}/cri-assets/Android/{WDS_Env["assetVersion"]}/cridata_remote_assets_criaddressables/{ep["EpisodeMasterId"]}.acb.bundle')
                    if voiceRes.status_code == 200:
                        open(os.path.join(temp_dir, f'{ep["EpisodeMasterId"]}.acb'), "wb").write(voiceRes.content)
            # 列表排序
            group["Episode"].sort(key = lambda x: x["EpisodeId"])
    
# 更新卡片照片
if Side_Update == True:
    assetsReq = requests.get(f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/spriteatlases_assets_spriteatlases/characters.bundle')
    assetsbundle = UnityPy.load(assetsReq.content)
    for obj in assetsbundle.objects:
        if obj.type.name == "Sprite":
            data = obj.read()
            data.image.save(os.path.join(sideImage_dir, f'{data.name}.png'))

# ------------------------ Spot ------------------------
masterlistres = requests.get(f'{masterlistUrl}/SpotConversationMaster.json')
if masterlistres.status_code == 200:
    for data in masterlistres.json():
        # 生成故事文檔
        res = requests.get(f'{WDS_Env["masterDataUrl"]}/scenes/{data["EpisodeMasterId"]}.bin')
        if res.status_code == 200:
            msgdata = msgpack_lz4block.deserialize(res.content)
            to_json = createFormat(data["EpisodeMasterId"], 4, 1, "スポット会話", addKey(msgdata), [])
            json_data = json.dumps(to_json, indent=4, ensure_ascii=False)
            open(os.path.join(EPBase_dir, f'{data["EpisodeMasterId"]}.json'), "w", encoding='utf8').write(json_data)
        # 檢查列表中是否存在
        Isexit = [item for item in GameStoryMasterlist["StoryMaster"]["Spot"] if item.get('EpisodeId') == data["EpisodeMasterId"]]
        if not len(Isexit) > 0:
            chararr = []
            for num in range(1, 6):
                if f'CharacterId{num}' in data:
                    if not data[f'CharacterId{num}'] == None:
                        chararr.append(data[f'CharacterId{num}'])
            GameStoryMasterlist["StoryMaster"]["Spot"].append({
                "EpisodeId" : data["EpisodeMasterId"],
                "Title" : "スポット会話",
                "Order" : 1,
                "CharacterIds" : chararr
            })
            # 生成語音檔
            voiceRes = requests.get(f'{WDS_Env["assetUrl"]}/cri-assets/Android/{WDS_Env["assetVersion"]}/cridata_remote_assets_criaddressables/{data["EpisodeMasterId"]}.acb.bundle')
            if voiceRes.status_code == 200:
                open(os.path.join(temp_dir, f'{data["EpisodeMasterId"]}.acb'), "wb").write(voiceRes.content)

    # 列表排序
    GameStoryMasterlist["StoryMaster"]["Spot"].sort(key = lambda x: x["EpisodeId"] )

# ------------------------ Posters ------------------------
posterlist = []
masterlistres = requests.get(f'{masterlistUrl}/PosterMaster.json')
if masterlistres.status_code == 200:
    posterlist = masterlistres.json()

Poster_Update = False
masterlistres = requests.get(f'{masterlistUrl}/PosterStoryMaster.json')
if masterlistres.status_code == 200:
    posterstorydata = masterlistres.json()
    for poster in posterlist:
        # 找尋該poster的故事
        Episodes = [item for item in posterstorydata if item.get('PosterMasterId') == poster["Id"]]
        # 如果有故事
        if len(Episodes) > 0:
            # 檢查列表中是否存在
            Isexit = [item for item in GameStoryMasterlist["StoryMaster"]["Poster"] if item.get('Id') == poster["Id"]]
            if not len(Isexit) > 0:
                GameStoryMasterlist["StoryMaster"]["Poster"].append({
                    "Id" : poster["Id"],
                    "Name" : poster["Name"],
                    "PronounceName" : poster["PronounceName"],
                    "CharacterIds" : poster["AppearanceCharacterBaseMasterIds"]
                })
                Poster_Update = True
                # 創建新的
                posterdetail = {
                    "EpisodeId": poster["Id"],
                    "StoryType": 5,
                    "Title": poster["Name"],
                    "EpisodeDetail" : []
                }
                for ep in Episodes:
                    posterdetail["EpisodeDetail"].append({
                        "Id" : ep["Id"],
                        "EpisodeType": posterTypeToNum[ep["EpisodeType"]],
                        "CharacterId" : ep["CharacterBaseMasterId"] if "CharacterBaseMasterId" in ep else None,
                        "Description" : ep["Description"],
                        "Order": ep["Order"]
                    })
                # 儲存
                json_data = json.dumps(posterdetail, indent=4, ensure_ascii=False)
                open(os.path.join(EPBase_dir, f'{poster["Id"]}.json'), "w", encoding='utf8').write(json_data)
    # 列表排序
    GameStoryMasterlist["StoryMaster"]["Poster"].sort(key = lambda x: x["Id"] )
    

# 更新Poster照片
if Poster_Update == True:
    assetsReq = requests.get(f'{WDS_Env["assetUrl"]}/2d-assets/Android/{WDS_Env["assetVersion"]}/spriteatlases_assets_spriteatlases/posters.bundle')
    assetsbundle = UnityPy.load(assetsReq.content)
    for obj in assetsbundle.objects:
        if obj.type.name == "Sprite":
            data = obj.read()
            data.image.save(os.path.join(posterImage_dir, f'{data.name}.png'))


# ------------------------ Special ------------------------
masterlistres = requests.get(f'{masterlistUrl}/SplashMaster.json')
if masterlistres.status_code == 200:
    SplashEpisode = [item for item in masterlistres.json() if item.get('SplashType') == "Episode"]
    for data in SplashEpisode:
        # 生成故事文檔
        res = requests.get(f'{WDS_Env["masterDataUrl"]}/scenes/{data["SplashValue"]}.bin')
        if res.status_code == 200:
            msgdata = msgpack_lz4block.deserialize(res.content)
            to_json = createFormat(int(data["SplashValue"]), 4, 1, "", addKey(msgdata), [])
            json_data = json.dumps(to_json, indent=4, ensure_ascii=False)
            open(os.path.join(EPBase_dir, f'{data["SplashValue"]}.json'), "w", encoding='utf8').write(json_data)

        # 檢查列表中是否存在
        Isexit = [item for item in GameStoryMasterlist["StoryMaster"]["Special"] if item.get('EpisodeId') == data["SplashValue"]]
        if not len(Isexit) > 0:
            GameStoryMasterlist["StoryMaster"]["Special"].append({
                "EpisodeId" : data["SplashValue"],
                "Title" : "",
                "Order" : 1,
            })
            # 生成語音檔
            voiceRes = requests.get(f'{WDS_Env["assetUrl"]}/cri-assets/Android/{WDS_Env["assetVersion"]}/cridata_remote_assets_criaddressables/{data["SplashValue"]}.acb.bundle')
            if voiceRes.status_code == 200:
                open(os.path.join(temp_dir, f'{data["SplashValue"]}.acb'), "wb").write(voiceRes.content)

    # 列表排序
    GameStoryMasterlist["StoryMaster"]["Special"].sort(key = lambda x: x["EpisodeId"] )


# 生成 GameStoryMasterlist.json
date = datetime.datetime.now(pytz.timezone('Asia/Tokyo'))
GameStoryMasterlist['LatestDate'] = date.strftime("%Y-%m-%d %H:%M:%S")
GameStoryMasterlist['ScriptVersion'] = script_version
json_data = json.dumps(GameStoryMasterlist, indent=4, ensure_ascii=False)
open(f'./GameStoryMasterlist.json', "w", encoding='utf8').write(json_data)