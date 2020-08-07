import pymysql
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import sys
import collections
import urllib
import requests

if len(sys.argv) != 2:
    sys.exit("Tidak ada argument, (siang, malam, all)")

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='skripsi_reporting',
)

def send_message(text, chat_id,token="tokenhere"):
    TOKEN = token
    URL = "https://api.telegram.org/bot{}/".format(TOKEN)
    text = text.replace('`','')
    if sys.version[0] == '3':
        text = urllib.parse.quote_plus(text.encode('utf-8', 'strict'))
    else:
        text = urllib.quote_plus(text.encode('utf-8', 'strict'))        
    url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
    requests.get(url)


def save_report(connection, data):
    with connection.cursor() as cursor:
        cursor.executemany("insert into report_sales(sales_name,tanggal_report,period,prospek,psb2p,psb3p,datel_id,sto_id) values (%s, %s, %s,%s,%s,%s,%s,%s)", data)
        connection.commit()

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open("Report Striker GO").worksheet("Form Responses 1")

#date = datetime.now().strftime("%m/%d/%Y").split('/')
#today = ""
#for i in range(len(date)):
#    if i == 0:
#        today += date[i].lstrip("0")
#    else:
#        today += "/{}".format(date[i].lstrip('0'))

# today = "1/22/2019"
today = datetime.now().strftime("%#m/%#d/%#Y)
records_per_today = sheet.findall(today)
tanggal = datetime.now().strftime("%Y-%m-%d")

distinct_data = []
temp_name_siang = set()
temp_name_malam = set()
for records in records_per_today:
    rows = list(filter(None,sheet.row_values(records.row)))
    print(rows)
    rows.pop(0)
    data = []
    if rows[2].split()[1].lower() == "siang":
        if rows[0] not in temp_name_siang:
            temp_name_siang.add(rows[0])
            siang = [
                rows[0],tanggal,rows[2],rows[3],rows[4],rows[5],rows[6],rows[7]
            ]
            data.append(siang)
    elif rows[2].split()[1].lower() == "malam":
        if rows[0] not in temp_name_malam:
            temp_name_malam.add(rows[0])
            malam = [rows[0],tanggal,rows[2],rows[3],rows[4],rows[5],rows[6],rows[7]]
            data.append(malam)

    distinct_data.append(data)


collect_data = []
bjm, bjb, blc, tjg = [], [], [], []
for data in distinct_data:
    for each in data:
        if sys.argv[1] == "siang":
            if each[2] == "12 Siang":
                if each[6] == "BANJARMASIN":
                    bjm.append(each)
                elif each[6] == "BANJARBARU":
                    bjb.append(each)
                elif each[6] == "TANJUNG":
                    tjg.append(each)
                elif each[6] == "BATULICIN":
                    blc.append(each)
        if sys.argv[1] == "malam":
            if each[2] == "7 Malam":
                if each[6] == "BANJARMASIN":
                    bjm.append(each)
                elif each[6] == "BANJARBARU":
                    bjb.append(each)
                elif each[6] == "TANJUNG":
                    tjg.append(each)
                elif each[6] == "BATULICIN":
                    blc.append(each)
        elif sys.argv[1] == "all":
            if each[6] == "BANJARMASIN":
                each[6] = 1
                if each[7] == 'KYG':
                    each[7] = 1
                elif each[7] == 'BJM':
                    each[7] = 2
                elif each[7] == 'GMB':
                    each[7] = 3
                elif each[7] == 'ULI':
                    each[7] = 4
                else:
                    each[7] = None
                bjm.append(each)
            elif each[6] == "BANJARBARU":
                each[6] = 2
                if each[7] == 'BBR':
                    each[7] = 5
                elif each[7] == 'LUL':
                    each[7] = 6
                elif each[7] == 'MTP':
                    each[7] = 7
                elif each[7] == 'MRB':
                    each[7] = 8
                else:
                    each[7] = None
                bjb.append(each)
            elif each[6] == "BATULICIN":
                each[6] = 3
                if each[7] == 'BLC':
                    each[7] = 9
                elif each[7] == 'KPL':
                    each[7] = 10
                elif each[7] == 'PGT':
                    each[7] = 11
                elif each[7] == 'BTB':
                    each[7] = 12
                elif each[7] == 'TKI':
                    each[7] = 13
                elif each[7] == 'PLE':
                    each[7] = 14
                elif each[7] == 'STI':
                    each[7] = 15
                else:
                    each[7] = None
                blc.append(each)
            elif each[6] == "TANJUNG":
                each[6] = 4
                if each[7] == 'AMT':
                    each[7] = 16
                elif each[7] == 'BRI':
                    each[7] = 17
                elif each[7] == 'KDG':
                    each[7] = 18
                elif each[7] == 'NEG':
                    each[7] = 19
                elif each[7] == 'RTA':
                    each[7] = 20
                elif each[7] == 'PGN':
                    each[7] = 21
                elif each[7] == 'TJL':
                    each[7] = 22
                else:
                    each[7] = None
                tjg.append(each)

if sys.argv[1] == "all":
    save_report(connection,bjm)
    save_report(connection,bjb)
    save_report(connection,blc)
    save_report(connection,tjg)
text = "*REPORT PEROLEHAN SALES {}*".format(sys.argv[1].upper())
text += "\nper tanggal : {}\n".format(today)
sales_agen = set()
jumlah_prospek = 0
jumlah_deal_2p = 0 
jumlah_deal_3p = 0
total_deal_bjm = 0
total_deal_bjb = 0
total_deal_blc = 0
total_deal_tjg = 0
text += "\nNama -- prospek / 2p / 3p / total\n"

text += "\n*BANJARMASIN*"

for banjar in bjm:
    if banjar[0] not in sales_agen:
        sales_agen.add(banjar[0])

    total_deal = int(banjar[4]) + int(banjar[5])
    text += "\n{} -- {} / {} / {} / {}".format(banjar[0],banjar[3],banjar[4],banjar[5],total_deal)
    jumlah_prospek += int(banjar[3])
    jumlah_deal_2p += int(banjar[4])
    jumlah_deal_3p += int(banjar[5])
    total_deal_bjm += total_deal

text += "\n\n*BANJARBARU*"
for banjarbaru in bjb:
    if banjarbaru[0] not in sales_agen:
        sales_agen.add(banjarbaru[0])

    total_deal = int(banjarbaru[4]) + int(banjarbaru[5])
    text += "\n{} -- {} / {} / {} / {}".format(banjarbaru[0],banjarbaru[3],banjarbaru[4],banjarbaru[5],total_deal)
    jumlah_prospek += int(banjarbaru[3])
    jumlah_deal_2p += int(banjarbaru[4])
    jumlah_deal_3p += int(banjarbaru[5])
    total_deal_bjb += total_deal


text += "\n\n*BATULICIN*"
for batulicin in blc:
    if batulicin[0] not in sales_agen:
        sales_agen.add(batulicin[0])

    total_deal = int(batulicin[4]) + int(batulicin[5])
    text += "\n{} -- {} / {} / {} / {}".format(batulicin[0],batulicin[3],batulicin[4],batulicin[5],total_deal)
    jumlah_prospek += int(batulicin[3])
    jumlah_deal_2p += int(batulicin[4])
    jumlah_deal_3p += int(batulicin[5])
    total_deal_blc += total_deal

text += "\n\n*TANJUNG*"
for tanjung in tjg:
    if tanjung[0] not in sales_agen:
        sales_agen.add(tanjung[0])

    total_deal = int(tanjung[4]) + int(tanjung[5])
    text += "\n{} -- {} / {} / {} / {}".format(tanjung[0],tanjung[3],tanjung[4],tanjung[5],total_deal)
    jumlah_prospek += int(tanjung[3])
    jumlah_deal_2p += int(tanjung[4])
    jumlah_deal_3p += int(tanjung[5])
    total_deal_tjg += total_deal

text += "\n\n\njumlah sales agen : {}".format(len(sales_agen))
text += "\njumlah prospek : {}".format(jumlah_prospek)
text += "\njumlah deal 2p : {}".format(jumlah_deal_2p)
text += "\njumlah deal 3p : {}".format(jumlah_deal_3p)
text += "\ntotal deal bjm : {}".format(total_deal_bjm)
text += "\ntotal deal bjb : {}".format(total_deal_bjb)
text += "\ntotal deal blc : {}".format(total_deal_blc)
text += "\ntotal deal tjl : {}".format(total_deal_tjg)
text += "\n*total deal kalsel : {}*".format(total_deal_bjm + total_deal_bjb + total_deal_blc + total_deal_tjg)

# send_message(text, -191557249)
send_message(text, 453727557)
# send_message(text,-1001178384595)
