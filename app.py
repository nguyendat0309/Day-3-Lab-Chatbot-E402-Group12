from llm.chatbotEasy import chatbot
from data.loadData import MyData
from llm.agent import chatBotAgent
from tools.searchPrice import  searchPrice
from tools.searchDistrict import searchDistrict
from llm.promtForAgent import PromtForAgent

if __name__ == '__main__':
    # dung cho model thong thuong
    data_fake = "Gia đình nọ có hai anh em, cha mẹ mất sớm và để lại cho anh em một khối gia tài. Vợ chồng người anh tham lam giành hết chỉ chừa lại cho người em một túp lều lụp xụp, trước cửa có một cây khế ngọt. Vợ chồng người em chăm chỉ làm ăn và chăm sóc cây khế chu đáo. Đến mùa khế ra rất nhiều quả. Bỗng một hôm có con chim lạ đến ăn khế. Vợ người em than khóc, chim lạ liền bảo may túi ba gang để chim trả ơn. Chim đưa người em ra đảo lấy vàng và từ đó gia đình người em trở nên giàu có nhất vùng. Người anh hay tin, lân la đến dò hỏi và đổi cả gia tài của mình để lấy túp lều và cây khế. Đến mùa khế chín, chim đại bàng lại đến và cũng ngỏ ý sẽ trả ơn. Người anh vì tham lam nên đã may túi to để dựng được nhiều vàng. Trên đường đi lấy vàng về vì quá nặng nên người anh đã bị rơi xuống biển và chết."
    
    #Agent
    data = MyData(path="data/restaurants_hanoi.json")
    # question = "Cho biết quán nào nhiều rating nhất"
    # res = chatbot(data, question)
    # print(res)
    ques = "tìm quán ăn ở Cầu Giấy"
    # print(data)
    chat = chatBotAgent(searchP=searchPrice, searchD=searchDistrict, sentence=ques, data=data, promtForAgent=PromtForAgent)
    reason = chat.reasoning()
    print(reason)
