from telegram.ext import Updater, InlineQueryHandler, CommandHandler, RegexHandler
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
import pymysql
from datetime import datetime
import calendar
import matplotlib.pyplot as plt
import math

Connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='skripsi_reporting',
)

def find_user(username):
    global Connection
    with Connection.cursor() as cursor:
        cursor.execute("select * from users where telegram_username = %s and is_approved = 1 limit 1", username)
        data = cursor.fetchone()
        cursor.close()
    return data

def is_accessed_bot(user_id):
    global Connection
    with Connection.cursor() as cursor:
        cursor.execute("select * from user_access_bot where user_id = %s limit 1",user_id)
        data = cursor.fetchone()
        cursor.close()
    if data is not None:
        return True
    return False

def user_access(user_id,chat_id,text,is_accessed_bot):
    global Connection
    try:
        if is_accessed_bot:
            query = "update user_access_bot set last_command = %s, last_accessed_at = now() where user_id = %s"
            params = (text, user_id)
        else:
            query = "insert into user_access_bot (chat_id, user_id,last_command) values (%s,%s,%s)"
            params = (chat_id,user_id,text)
        with Connection.cursor() as cursor:
            cursor.execute(query,params)
    finally:
        Connection.commit()

def get_paid_a_day(date):
    global Connection
    with Connection.cursor() as cursor:
        cursor.execute("\
            select ifnull(count(id),0) as total \
            from bilper \
            where tanggal_bayar = date(%s)\
            and status_pembayaran = 'LUNAS'\
            group by tanggal_report\
            order by tanggal_report desc limit 1\
        ",date)
        data = cursor.fetchone()
        cursor.close()
    if data is None:
        return (0,)
    return data

def set_month(text):
    switcher = {
        "januari": "01",
        "februari": "02",
        "maret": "03",
        "april": "04",
        "mei": "05",
        "juni": "06",
        "juli": "07",
        "agustus": "08",
        "september": "09",
        "oktober": "10",
        "november": "11",
        "desember": "12"
    }
    return switcher.get(text, "nothing")


def show_cluster(bot, update):
    username = update.message.chat.username
    chat_id = update.message.chat.id
    text = update.message.text
    user = find_user(username)
    if user is not None:
        is_used_bot = is_accessed_bot(user[0])
        user_access(user[0],chat_id,text,is_used_bot)
        splitted_input = text.split("_")
        month = set_month(splitted_input[1].lower())
        if month == "nothing" or len(splitted_input) > 2:
            bot.send_message(chat_id = chat_id,text = 'Input yang kamu masukkan tidak valid.')
        else:
            year = datetime.now().strftime("%Y")
            last_day = calendar.monthrange(int(year), int(month))[1]
            dataset = []
            for i in range(1,last_day+1):
                day = str(i) if len(str(i)) > 1 else "0" + str(i)
                date = year + "-" + month + "-" + day
                paid_a_day = get_paid_a_day(date)[0]
                dataset.append((i,paid_a_day))

            #initials centroid
            n = len(dataset)
            centroids = [dataset[0],dataset[round(n/2)+1],dataset[n-3]]
            print(centroids)
            
            #start calculating
            total_iteration = 0
            while True:
                clusters = []
                for i in range(len(dataset)):
                    x1, y1 = dataset[i][0], dataset[i][1]
                    number, distance = 1, {}
                    for j in range(len(centroids)):
                        x2, y2 = centroids[j][0], centroids[j][1]
                        euclidean_distance = math.sqrt( math.pow(x2 - x1, 2) + math.pow(y2 - y1,2))
                        key = 'c' + str(number)
                        distance[key] = euclidean_distance
                        number += 1
                    cluster = min(distance,key=distance.get)
                    clusters.append(dict(data = (x1,y1), cluster = cluster))

                initialize_cluster, new_centroids = ['c1', 'c2', 'c3'], []

                for clstr in initialize_cluster:
                    r = list(filter(lambda x: x['cluster'] == clstr, clusters))
                    xsum, ysum, total = 0, 0, 0
                    for p in r:
                        xsum += p['data'][0]
                        ysum += p['data'][1]
                        total += 1
                    centroid = (xsum/total,ysum/total)
                    print(clstr + ":" + str(total))
                    new_centroids.append(centroid)
                for k in clusters:
                    print(k['cluster'] + "|", end="")
                print("\n")

                #new centroids
                print(new_centroids)
                total_iteration += 1
                if centroids[0] == new_centroids[0] and centroids[1] == new_centroids[1] and centroids[2] == new_centroids[2]:
                    break
                centroids[0], centroids[1], centroids[2] = new_centroids[0], new_centroids[1], new_centroids[2]

            text = "c1 = biru | c2 = hijau | c3 = kuning | kluster means = merah \n"
            text += f"total iterasi {total_iteration}\n"
            text += f"nilai centroid terakhir\n"
            text += f"c1 = {centroids[0][0],centroids[0][1]}\n"
            text += f"c2 = {centroids[1][0],centroids[1][1]}\n"
            text += f"c3 = {centroids[2][0],centroids[2][1]}\n"
            for data_cluster in clusters:
                x, y = data_cluster['data'][0], data_cluster['data'][1]
                if data_cluster['cluster'] == 'c1':
                    color="blue"
                elif data_cluster['cluster'] == 'c2':
                    color="green"
                elif data_cluster['cluster'] == 'c3':
                    color="yellow"
                plt.scatter(x,y,color=color)
                text += f"({x},{y}) = {data_cluster['cluster']}\n"

            for centroid in centroids:
                x, y = centroid[0], centroid[1]
                color = "red"
                plt.scatter(x,y,color=color)

            plt.savefig('clusterplot.png')
            plt.cla()
            bot.send_photo(chat_id = chat_id,photo = open('./clusterplot.png','rb'), caption=text)

    else:
        update.message.reply_text('Kamu belum boleh akses.')

def main():
    updater = Updater('tokenhere')
    dp = updater.dispatcher
    dp.add_handler(RegexHandler('^TampilKluster_',show_cluster))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    print('Listening..')
    main()