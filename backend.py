import os
import re 
import json
import send2trash
import bangumi_api

#-------------------------------------------------------------------------------------------------------------------------

def scan_file(file):
    #扫描指定目录下的所有视频文件，并获取它们的信息
    video_types = ('.mp4', '.mkv', '.avi')         #定义视频文件类型，可以根据需要添加更多的类型
    anime_data = {} 

    for root, dirs, files in os.walk(file):        #遍历指定目录及其子目录中的所有文件，返回当前目录路径、子目录和文件名称
        folder_name = os.path.basename(root)            #获取当前目录的名称
        aniname = name_convert(folder_name)                #调用上面的函数动画名称转换，获取干净的动画文件夹名称
        anifolder_path=os.path.join(root)                   #拼接当前目录的完整路径
        
        for f in files:                            #遍历每个文件
            if f.lower().endswith(video_types):    #检查文件是否是视频文件
              file_path = os.path.join(root, f)    #拼接文件的完整路径

              info = file_info(file_path)          #调用上面的函数文件信息

              if info :
                  if aniname not in anime_data:    #如果当前目录名称不在对应字典中，则添加一个新的键值对

                    try:
                        api_data = bangumi_api.bgm_api(aniname)     #调用bangumi_api获取动画信息,用个变量存储

                    except TypeError:              #用try来增加容错
                        api_data = None

                    if api_data:  #如果成功获取到动画信息
                        official_name = api_data['official_name']  #获取官方名称
                        cover_url = api_data['cover_url']          #获取封面URL

                    else:  #如果没有成功获取到动画信息，则使用目录名称作为动画名称
                        official_name = aniname
                        cover_url = ""

                    anime_data[aniname] ={                       #创造对应的键值对
                        'official_name': official_name,
                        'cover_url': cover_url,
                        'folder_path': anifolder_path,
                        'videos': []
                    }
                
                  anime_data[aniname]['videos'].append(info)   #把单个的视频文件加入到视频列表中
       


    return anime_data



def file_info(file_path):
    #获取文件信息，包括文件名、路径和大小
    try:
        getfsize = os.path.getsize(file_path)            #获取文件大小，单位为字节
        file_size=round(getfsize/(1024*1024),2)     #转换为MB并保留两位小数

        file_name = os.path.basename(file_path)          #获取文件名

        return {
            'name': file_name,
            'path': file_path,
            'size': file_size
        }

    except Exception as e:
        print(f"这个文件似乎有点问题QwQ:{file_path}")
        return None
    
#-------------------------------------------------------------------------------------------------------------------------

def name_convert(name):
    #动画名称转换，清理掉文件名中的括号及其内容，提取出干净的动画名称
    pattern = r"\[.*?\]|\{.*?\}|\(.*?\)|【.*?】|{.*?}"  # 匹配方括号、花括号、圆括号，中文方括号和中文花括号内的内容

    cleaned_name = re.sub(pattern, "", name)  # 替换方括号内的内容为空字符串，清理括号里的东西

    cleaned_name = cleaned_name.strip()  # 去除首尾的空白字符

    if cleaned_name == "" :
        #如果清理后的名称为空，则尝试提取括号内最长的内容作为动画名称
        cleanedname2 = re.findall(r"\[.*?\]", name)
        if cleanedname2:
            cleaned_name=max(cleanedname2, key=len)  
            cleaned_name = cleaned_name.strip("[]")
            cleaned_name = aftersplit(cleaned_name)
            return cleaned_name
        else:
            return name
    else:
        cleaned_name = aftersplit(cleaned_name)
        return cleaned_name
    

def aftersplit(name):
    #进一步清理名称，去掉一些常见的分隔符及其后面的内容
    splitbox = ['-','_','——','-',':','：']
    for i in splitbox:
        if i in name:
            after_splitname = name.split(i)[0].strip()

            if '△' in after_splitname:
                after_splitname = after_splitname.strip('△')
                return after_splitname
            
            return after_splitname
    return name



#-------------------------------------------------------------------------------------------------------------------------

# Json_path = 'anime_data.json'        #拼接json文件的路径（源代码版本）


userpath = os.path.expanduser('~')     #获取User目录路径
Amg_path = os.path.join(userpath, 'AppData', 'Roaming', 'Animananger')  #存储数据的目录路径
if not os.path.exists(Amg_path):   #如果目录不存在，则创建目录
    os.makedirs(Amg_path)
Json_path = os.path.join(Amg_path, 'anime_data.json')    #拼接json文件的路径 （exe版本）


def save_data(data):            #将扫描的数据保存到json文件中    
                        
    with open(Json_path, 'w', encoding='utf-8') as f:   #将数据保存到json文件中
        json.dump(data, f, ensure_ascii=False, indent=4)   #使用json.dump()函数将数据写入文件，参数ensure_ascii=False表示不转义非ASCII字符，indent=4表示使用4个空格进行缩进
    return data


def load_data():
    #从json文件中加载数据
    try:
        with open(Json_path, 'r', encoding='utf-8') as f:   #从json文件中加载数据
            data = json.load(f)   #使用json.load()函数将文件中的数据加载到变量data中
        return data

    except FileNotFoundError:
        save_data({})   #如果json文件不存在，则调用save_data()函数创建一个空的json文件
        return {}
    except json.JSONDecodeError:
        save_data({})   #如果json文件存在但内容无法解析，则调用save_data()函数重置为一个空的json文件
        return {}
    
#-------------------------------------------------------------------------------------------------------------------------

def delete_data(target):
    # 删除指定动画的数据
    try:                                                    
        with open(Json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)  
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    
    if target in data:                                          
        folder_path = data.get(target, {}).get('folder_path', None)
        
        try:
            # 1. 检查物理路径是否存在
            if folder_path and os.path.exists(folder_path):
                # 2. 规范化路径 (将 E:/a\b 变成 E:\a\b)，防止 Windows 底层 API 报错
                normalized_path = os.path.normpath(folder_path)
                send2trash.send2trash(normalized_path)
            
            # 3. 关键点：无论文件是不是已经被手动删除了，只要进到这里，
            #    都必须把本地 JSON 数据里的记录抹掉，防止产生删不掉的幽灵数据！
            del data[target]
            save_data(data)
            
            return True
        
        except PermissionError:
            print(f"\n[删除失败] 文件夹被占用！请检查是否还有播放器正在播放《{target}》？\n")
            return False
            
        except Exception as e:
            # 捕获异常并打印，拒绝“默默报错”
            print(f"\n[删除异常] 删除 {target} 时发生错误: {str(e)}\n")
            return False
    
    return False


#-------------------------------------------------------------------------------------------------------------------------


# if __name__ == "__main__":  

#     input_file = r'E:\视频\Anime'

#     a=save_data(scan_file(input_file))

#     for folder_name,data in a.items():
#        print(f'番名: {data.get("official_name", folder_name)}')

    



# if __name__ == "__main__":  
#     #测试
#     input_file = r'E:\视频\Anime'

#     a=load_data()

#     print('------------------------------------------------------------------------------------------------')

#     if not a:   
#         data = scan_file(input_file)
#         a= save_data(data)
#         print('---                                  已扫描并加载                                          ---')
        
#     else:
#         print('---                                    已加载                                          ---')

#     print('------------------------------------------------------------------------------------------------')


        
#     for folder_name,data in a.items():
#         print(f'番名: {data.get("official_name", folder_name)}')  #优先显示官方名称，如果没有就显示文件夹名称

#         # print(f'封面URL: {data.get("cover_url", "")}')
#         # print(f'视频集数： {len(data.get("videos", []))}')   
