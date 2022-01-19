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

# from twilio.rest import Client
# import time
#
# client = Client('YOUR_ACCOUNT_SID', 'YOUR_AUTH_TOKEN')
# client = Client('YOUR_ACCOUNT_SID', 'YOUR_AUTH_TOKEN')

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def reply():
    text = request.form.get("Body")
    number = request.form.get("From")
    number = number.replace("whatsapp:", "")
    res = MessagingResponse()
    user = users.find_one({"number": number})
    if bool(user) == False:
        res.message("Servus!\nSchön, dass du die Experten für PKW, Motorrad, Wohnwagen und -mobil kontaktiert hast! Mit unserem virtuellen WhatsApp Assistenten kannst du uns alle wichtigen Informationen zu deinem Anliegen mitteilen. \n Willst du \n 1⃣ fortfahren oder \n 0⃣ abbrechen?")
        users.insert_one({"number": number, "status": "main", "messages": []})
    elif user["status"] == "main":
        try:
            option = int(text)
        except:
            res.message("Bitte gib eine gültige Antwort ein!")
            return str(res)
        if option == 1:
            #res.message(f"Für mehr Informationen besuche unsere Website {websiteurl}.")
            res.message(f"Für mehr Informationen besuche unsere Website {websiteurl}.")
        elif option == 0:
            res.message(f"Der virtuelle Assistent wurde auf deinen Wunsch beendet - alle über dich gespeicherten Daten wurden gelöscht. \n Du kannst uns auch eine Nachricht an <e-Mail> schicken oder uns zu unseren Öffnungszeiten (9.00 - 18:00) telefonisch erreichen.\n Für mehr Informationen besuche unsere Website {websiteurl}.")
            users.delete_one({"number": number})
        else:
            res.message(
                f"Bitte gibt eine gültige Auswahl ein!")
        return str(res)

    else:
        res.message("Die letzte Eingabe kann nicht interpretiert werden.")
    users.update_one({"number": number}, {"$push": {"messages": {"text": text, "date": datetime.now()}}})



    # msg = res.message(f"Danke für die Nachricht. Deine Nachricht '{text}' von der Nummer {number}")
    # res.message("Willkommen beim virtuellen Assisteten von deinen Experten für PKW, Motorrad, Wohnwagen und -mobil!")
    # if text == "Hi":
    #     res.message("Holla")
    # else:
    #     res.message("Was soll man dazu sagen?")

    # number = request.form.get('From')
    # minute = 0
    # # run loop for 10 minutes
    #
    # while True:
    #     client.messages.create(body=f"{minute} minutes have passed since you've messaged me!", from_='whatsapp:+14155238886', to=number)
    #     # Let's wait for 1 minute
    #     time.sleep(60)
    #     minute += 1
    #     # If 10 minutes have passed then quit
    #     if minute == 10:
    #         break
    return str(res)

if __name__ == '__main__':
    app.run(port=5000)