import requests
import json
import difflib


def bgm_api(keyword):
    #联网调用bangumi的api，获取动画信息，返回最相似的一条数据
    url = f"https://api.bgm.tv/search/subject/{keyword}?type=2"     #拼装请求URL，只要动画的接口type2

    headers = {                                                     #模拟浏览器请求，避免被拒绝访问
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }

    response = requests.get(url, headers=headers)                   #发送GET请求获取数据

    if response.status_code == 200:                                 #检查请求是否成功
        data = response.json()                                      #解析返回的JSON数据        
        if 'list' in data and len(data['list']) > 0:                #再一次检查看看有没有想要的数据
          
          best_like = data['list'][0]                               #先默认第一条数据是最相似的
          max_score = 0                                             #设定个分数变量来比较相似度    
        
          clean_keyword = keyword.replace(" ", "").lower()         #清掉掉空格和转换为小写，提高匹配的准确性

          for i in data['list']:                                    #遍历返回的动画列表，开始匹对
              
              name = i.get('name', '')                              #获取动画的原名      -用于后续
              name_cn = i.get('name_cn', '')                        #获取动画的中文名      匹对对比-

              clean_name = name.replace(" ", "").lower()            #清理空格和转换为小写，提高匹配的准确性
              clean_name_cn = name_cn.replace(" ", "").lower()

              score1 = difflib.SequenceMatcher(None, clean_keyword, clean_name).ratio()      #计算输入关键词与动画原名的相似度
              score2 = difflib.SequenceMatcher(None, clean_keyword, clean_name_cn).ratio()    
              whomax = max(score1, score2)                          #取两者中最高的相似度作为最终得分

              if whomax > max_score:                               #对比得分来找出最相似的动画
                  max_score = whomax
                  best_like = i

          get_name = best_like.get('name_cn', '')                     #最终选定的动画的中文名
          if get_name == '':
            get_name = best_like.get('name', '')                      #如果没有中文名，就用原名

          image = best_like.get('images',{})                         #获取动画封面
          get_cover = ""
          if image and 'large' in image:
              get_cover = image['large']                    

          return {
                'official_name': get_name,
                'cover_url': get_cover
          }
            

    else:
       return None



#测试
if __name__ == "__main__":
    print(bgm_api("Watashi ga Koibito ni Nareru Wakenaijan, Muri Muri"))