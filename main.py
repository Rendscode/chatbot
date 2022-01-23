from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from pymongo import MongoClient
from datetime import datetime
import re

websiteurl = "www.heise.de"
telefonnummer_muster = r'\+?[\d]{5,12}'

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
    'text_abbruch_nutzer': f'Der virtuelle Assistent wurde auf deinen Wunsch beendet - alle über dich gespeicherten '
                           f'Daten wurden gelöscht. \n Du kannst uns auch eine Nachricht an <e-Mail> schicken oder '
                           f'uns zu unseren Öffnungszeiten (9.00 - 18:00) telefonisch erreichen.\nFür mehr '
                           f'Informationen besuche unsere Website {websiteurl}.',
    'text_ungueltige_auswahl': 'Bitte gib eine gültige Auswahl ein!',
    'text_anliegen_art': 'Was möchtest du? \n1⃣ eine *Wertermittlung* oder \n2⃣ eine *Schadenfeststellung* \ndeines '
                    'Fahrzeugs? \nOder willst du 0⃣ *abbrechen?* ',
    'text_baustelle': f'Der virtuelle Assistent wurde wegen einer Programmbaustelle beendet - alle über dich '
                      f'gespeicherten Daten wurden gelöscht. \n Du kannst uns auch eine Nachricht an <e-Mail> '
                      f'schicken oder uns zu unseren Öffnungszeiten (9.00 - 18:00) telefonisch erreichen.\n Für mehr '
                      f'Informationen besuche unsere Website {websiteurl}. ',
    'text_wertermittlung': 'Du möchtest eine Wertermittlung durchführen lassen. Für eine Bearbeitung auf der '
                           '*Fastlane*, teile uns bitte einige Daten mit:\n Dürfen wir dich unter dieser Nummer '
                           'kontaktieren: <telnum>?\n Wähle 1⃣ für ja oder \ngib eine andere Telefonnummer oder '
                           'eine e-Mail Adresse ein!\n Oder wähle 0⃣ zum *abbrechen*.',
    'text_telefonnummer_erkannt': 'Wir haben diese Nummer erkannt für eine Kontaktaufnahme gespeichert: ',
    'text_telefonnummer_wie_im_messenger': 'Wir haben deine Nummer für eine Kontaktaufnahme gespeichert!',
    'text_abschluss': '\nWir werden dich umgehend kontaktieren und freuen uns, dich und dein Fahrzeug kennenzulernen! '
                      '\n\nWenn du alle über dich gespeicherten Daten wieder löschen möchtest, wähle 0⃣!\nWir werden '
                      'dich dann nicht kontaktieren, sondern warten auf deine Meldung. '
        }


@app.route('/', methods=['GET', 'POST'])
def reply(nummer_referenz=None):
    def dialog_abbruch():
        res.message(texte['text_abbruch_nutzer'])
        users.delete_one({"number": number})

    # if (users.find_one() == True):  ## for testing purposes: delete all database entries
    #     users.delete_many()
    if (orders.find_one() == True):  ## for testing purposes: delete all database entries
        orders.delete_many()

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
            users.update_one({"number": number}, {"$set": {"status": "anliegen_art"}})
        elif option == 0:
            dialog_abbruch()
        else:
            res.message(texte['text_ungueltige_auswahl'])
        return str(res)
    elif user["status"] == "anliegen_art":
        try:
            option = int(text)
        except:
            res.message('text_ungueltige_auswahl')
            return str(res)
        if option == 0:
            # users.update_one({"number": number}, {"$set": {"status": "main"}})
            dialog_abbruch()
        elif option == 1:
            res.message(texte['text_wertermittlung'].replace('<telnum>', str(number)))
            users.update_one({"number": number}, {"$set": {"status": "wertermittlung"}})
        elif option <= 2:
            res.message(texte['text_baustelle'])
            users.delete_one({"number": number})
    elif user['status'] == 'wertermittlung':
        nummer_eingegeben = re.findall(telefonnummer_muster, text)
        if nummer_eingegeben:
            nummer_referenz = nummer_eingegeben[0]
            res.message(texte['text_telefonnummer_erkannt'] + str(nummer_referenz) + texte['text_abschluss'])
            orders.insert_one({"number": number, "nummer_referenz": nummer_referenz, "status": "wertermittlung", "messages": []})
            users.update_one({"number": number}, {"$set": {"status": "abschluss"}})
            return str(res)
        try:
            option = int(text)
        except:
            res.message('text_ungueltige_auswahl')
            return str(res)
        if option == 0:
            dialog_abbruch()
        elif option == 1:
            res.message(texte['text_telefonnummer_wie_im_messenger'] + texte['text_abschluss'])
            orders.insert_one({"number": number, "status": "wertermittlung", "messages": []})
            users.update_one({"number": number}, {"$set": {"status": "abschluss"}})
        else:
            res.message(texte['text_ungueltige_auswahl'])
            # users.update_one({"number": number}, {"$set": {"status": "kontaktdateneingabe"}})
        return str(res)
            # users.delete_one({"number": number})
    elif user['status'] == 'abschluss':
        # users.update_one({"number": number}, {"$set": {"status": "fertig"}})
        res.message(texte['text_abschluss'])
    # elif user['status'] == 'fertig':
        try:
            option = int(text)
        except:
            res.message(texte['text_ungueltige_auswahl'])
            return str(res)
        if option == 0:
            orders.delete_one({"number": number})
            dialog_abbruch()
        else:
            res.message(texte['text_ungueltige_auswahl'])
        return str(res)
    else:
        res.message(texte['text_ungueltige_auswahl'])
    users.update_one({"number": number}, {"$push": {"messages": {"text": text, "date": datetime.now()}}})
    return str(res)


if __name__ == '__main__':
    app.run(port=5000)