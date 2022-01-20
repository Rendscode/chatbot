from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
from datetime import datetime

websiteurl = "www.heise.de"
file = open("mongocredentials.txt")
mongoclient_credentials = file.readline()

mongoconnectionstring = f"mongodb+srv://{mongoclient_credentials}?retryWrites=true&w=majority"

cluster = MongoClient(mongoconnectionstring)

db = cluster["dienstleistung"]
users = db["kunden"]
orders = db["anfragen"]

app = Flask(__name__)

texte = {
    'text_begruessung_neu': 'Servus!\nSchön, dass du die Experten für PKW, Motorrad, Wohnwagen und -mobil kontaktiert '
                       'hast! Mit unserem virtuellen WhatsApp Assistenten kannst du uns alle wichtigen Informationen '
                       'zu deinem Anliegen mitteilen. \n Willst du \n 1⃣ *fortfahren* oder \n 0⃣ *abbrechen?*',
    'text_ungueltige_auswahl': 'Bitte gib eine gültige Auswahl ein!',
    'text_anliegen_art': 'Was möchtest du? \n1⃣ eine *Wertermittlung* oder \n2⃣ eine *Schadenfeststellung* \ndeines '
                    'Fahrzeugs? \nOder willst du 0⃣ *abbrechen?* '
        }


@app.route('/', methods=['GET', 'POST'])
def reply():
    if (users.find_one() == True):
        users.delete_many()
    text = request.form.get("Body")
    number = request.form.get("From")
    number = number.replace("whatsapp:", "")[:-2]  #truncate last two digits to protect privacy for this demo
    res = MessagingResponse()
    user = users.find_one({"number": number})
    if bool(user) == False:
        res.message(texte['text_begruessung_neu'])
        users.insert_one({"number": number, "status": "start", "messages": []})
    elif user["status"] == "start":
        try:
            option = int(text)
        except:
            res.message(texte['text_ungueltige_auswahl'])
            return str(res)
        if option == 1:
            res.message(texte['text_anliegen_art'])
            users.update_one(
                {"number": number}, {"$set": {"status": "anliegen_art"}})
        elif option == 0:
            res.message(f"Der virtuelle Assistent wurde auf deinen Wunsch beendet - alle über dich gespeicherten Daten wurden gelöscht. \n Du kannst uns auch eine Nachricht an <e-Mail> schicken oder uns zu unseren Öffnungszeiten (9.00 - 18:00) telefonisch erreichen.\n Für mehr Informationen besuche unsere Website {websiteurl}.")
            users.delete_one({"number": number})
        else:
            res.message(texte['text_ungueltige_auswahl'])
        return str(res)
    elif user["status"] == "anliegen_art":
        try:
            option = int(text)
        except:
            res.message("Bitte gib eine gültige Auswahl ein!")
            return str(res)
        if option == 0:
            users.update_one(
                {"number": number}, {"$set": {"status": "main"}})
            res.message(f"Der virtuelle Assistent wurde auf deinen Wunsch beendet - alle über dich gespeicherten Daten wurden gelöscht. \n Du kannst uns auch eine Nachricht an <e-Mail> schicken oder uns zu unseren Öffnungszeiten (9.00 - 18:00) telefonisch erreichen.\n Für mehr Informationen besuche unsere Website {websiteurl}.")
            users.delete_one({"number": number})
        elif 1 <= option <= 2:
            res.message(f"Der virtuelle Assistent wurde wegen einer Programmbaustelle - alle über dich gespeicherten Daten wurden gelöscht. \n Du kannst uns auch eine Nachricht an <e-Mail> schicken oder uns zu unseren Öffnungszeiten (9.00 - 18:00) telefonisch erreichen.\n Für mehr Informationen besuche unsere Website {websiteurl}.")
            users.delete_one({"number": number})
    else:
        res.message("Die letzte Eingabe kann nicht interpretiert werden.")
    users.update_one({"number": number}, {"$push": {"messages": {"text": text, "date": datetime.now()}}})

    return str(res)

if __name__ == '__main__':
    app.run(port=5000)