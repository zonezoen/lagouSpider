# 数据分析，数据可视化
from os import path
from wordcloud import WordCloud, ImageColorGenerator
import jieba.analyse
import matplotlib.pyplot as plt
from scipy.misc import imread
import os
import time
from pymongo import MongoClient


class Analycis:
    def __init__(self):
        self.client = MongoClient('mongodb://localhost:27017/')
        self.zfdb = self.client.zfdb
        self.zfdb.authenticate("mongodbUser", "yourpassward")

    def getCity(self):
        return [
            "全国",
            "北京",
            "上海",
            "深圳",
            "广州",
        ]

    def getLanguage(self):
        return [
            "Java",
            "Python",
            "C",
            "机器学习",
            "图像识别",
            "自然语言",
            "区块链",
            "Go",
            "Php",
            # ".NET",
            "Android",
            "iOS",
            "web前端",
            "精准推荐",
            # "Node.js",
            # "Hadoop",

        ]

    # 统计的数据量
    # 各语言平均工资
    # 各语言学历要求
    # 各语言工作年限要求
    #

    # 福利词云
    # 公司级别排行（A轮、B轮）
    # 公司类型排行

    # 获取各语言样本数量
    def getLanguageNum(self):
        analycisList = []
        for index, language in enumerate(self.getLanguage()):
            collection = self.zfdb["z_" + language]
            totalNum = collection.aggregate([{'$group': {'_id': '', 'total_num': {'$sum': 1}}}])
            totalNum2 = list(totalNum)[0]["total_num"]
            analycisList.append(totalNum2)
        return (self.getLanguage(), analycisList)

    # 获取各语言的平均工资
    def getLanguageAvgSalary(self):
        analycisList = []
        for index, language in enumerate(self.getLanguage()):
            collection = self.zfdb["z_" + language]
            totalSalary = collection.aggregate([{'$group': {'_id': '', 'total_salary': {'$sum': '$salaryMid'}}}])
            totalNum = collection.aggregate([{'$group': {'_id': '', 'total_num': {'$sum': 1}}}])
            totalNum2 = list(totalNum)[0]["total_num"]
            totalSalary2 = list(totalSalary)[0]["total_salary"]
            analycisList.append(round(totalSalary2 / totalNum2, 2))
        return (self.getLanguage(), analycisList)

    # 获取一门语言的学历要求（用于 pyecharts 的词云）
    def getEducation(self, language):
        results = self.zfdb["z_" + language].aggregate([{'$group': {'_id': '$education', 'weight': {'$sum': 1}}}])
        educationList = []
        weightList = []
        for result in results:
            educationList.append(result["_id"])
            weightList.append(result["weight"])
        # print(list(result))
        return (educationList, weightList)

    # 获取一门语言的工作年限要求（用于 pyecharts 的词云）
    def getExperience(self, language):
        results = self.zfdb["z_" + language].aggregate([{'$group': {'_id': '$experience', 'weight': {'$sum': 1}}}])
        totalAvgPriceDirList = []
        for result in results:
            totalAvgPriceDirList.append(
                {"value": result["weight"], "name": result["_id"] + "  " + str(result["weight"])})
        return totalAvgPriceDirList

    # 获取 welfare 数据，用于构建福利词云
    def getWelfare(self):
        content = ''
        queryArgs = {}
        projectionFields = {'_id': False, 'welfare': True}  # 用字典指定
        for language in self.getLanguage():

            collection = self.zfdb["z_" + language]
            searchRes = collection.find(queryArgs, projection=projectionFields).limit(1000)
            for result in searchRes:
                print(result["welfare"])
                content += result["welfare"]
        return content

    # 获取公司级别排行（用于条形图）
    def getAllCompanyLevel(self):
        levelList = []
        weightList = []
        newWeightList = []
        attrList = ["A轮", "B轮", "C轮", "D轮及以上", "不需要融资", "上市公司"]
        for language in self.getLanguage():
            collection = self.zfdb["z_" + language]
            # searchRes = collection.find(queryArgs, projection=projectionFields).limit(1000)
            results = collection.aggregate([{'$group': {'_id': '$companyLevel', 'weight': {'$sum': 1}}}])
            for result in results:
                levelList.append(result["_id"])
                weightList.append(result["weight"])
        for index, attr in enumerate(attrList):
            newWeight = 0
            for index2, level in enumerate(levelList):
                if attr == level:
                    newWeight += weightList[index2]
            newWeightList.append(newWeight)
        return (attrList, newWeightList)



    # ========================================================

    # 展示饼图
    def showPie(self, title, attr, value):
        from pyecharts import Pie
        pie = Pie(title)
        # pie.add("aa", attr, value, is_label_show=True, title_pos='center')
        pie.add("",
                attr,
                value,
                radius=[40, 75],
                label_text_color=None,
                is_label_show=True,
                legend_orient="vertical",
                legend_pos="left", )
        pie.render()

    # 展示矩形树图
    def showTreeMap(self, title, data):
        from pyecharts import TreeMap
        data = data
        treemap = TreeMap(title, width=1200, height=600)
        treemap.add("深圳", data, is_label_show=True, label_pos='inside', label_text_size=19)
        treemap.render()

    # 展示条形图
    def showLine(self, title, attr, value):
        from pyecharts import Bar
        bar = Bar(title)
        bar.add("深圳", attr, value, is_convert=False, is_label_show=True, label_text_size=18, is_random=True,
                xaxis_interval=0,
                # xaxis_label_textsize=9,
                legend_text_size=18, label_text_color=["#000"])
        bar.render()

    # 展示词云
    def showWorkCloud(self, content, image_filename, font_filename, out_filename):
        d = path.dirname(__name__)
        # content = open(path.join(d, filename), 'rb').read()
        # 基于TF-IDF算法的关键字抽取, topK返回频率最高的几项, 默认值为20, withWeight
        # 为是否返回关键字的权重
        tags = jieba.analyse.extract_tags(content, topK=100, withWeight=False)
        text = " ".join(tags)
        # 需要显示的背景图片
        img = imread(path.join(d, image_filename))
        # 指定中文字体, 不然会乱码的
        wc = WordCloud(font_path=font_filename,
                       background_color='black',
                       # 词云形状，
                       mask=img,
                       # 允许最大词汇
                       max_words=500,
                       # 最大号字体，如果不指定则为图像高度
                       max_font_size=130,
                       # 画布宽度和高度，如果设置了msak则不会生效
                       # width=600,
                       # height=400,
                       margin=2,
                       # 词语水平摆放的频率，默认为0.9.即竖直摆放的频率为0.1
                       prefer_horizontal=0.9
                       )
        wc.generate(text)
        img_color = ImageColorGenerator(img)
        plt.imshow(wc.recolor(color_func=img_color))
        wc.to_file("loutput.jpeg")
        plt.axis("off")
        plt.show()
        wc.to_file(path.join(d, out_filename))

    # 展示 pyecharts 的词云
    def showPyechartsWordCloud(self, attr, value):
        from pyecharts import WordCloud
        wordcloud = WordCloud(width=1300, height=620)
        wordcloud.add("", attr, value, word_size_range=[20, 100])
        wordcloud.render()


analycis = Analycis()


# 计算样本数量
(attr, value) = analycis.getLanguageNum()
analycis.showLine("样本数量", attr, value)
os.rename("render.html","sampleNum.html")

# 计算样本数量
(attr, value) = analycis.getLanguageAvgSalary()
analycis.showLine("各语言平均工资", attr, value)
os.rename("render.html","languageAvgSalary.html")


# 语言学历要求
for language in analycis.getLanguage():
    (attr, value) = analycis.getEducation(language)
    print(attr, value)
    analycis.showPie("                       "+language + " 工作年限", attr, value)
    os.rename("render.html", "./languageEducation/" + language + "Education.html")
#


#  语言工作年限要求要求
for language in analycis.getLanguage():
    data = analycis.getExperience(language)
    print(data)
    analycis.showTreeMap("                       "+language+"工作学历要求", data)
    os.rename("render.html", "./languageExperience/" + language + "Experience.html")

#  福利词云
analycis.showWorkCloud(analycis.getWelfare(), "docker.jpeg", "kh.ttf", out_filename="loutput.jpeg")

# 公司级别（A轮、B轮） pyechart 词云
(attr, value) = analycis.getAllCompanyLevel()
print(attr, value)
analycis.showLine("公司级别", attr, value)
os.rename("render.html", "companyLevel.html")

