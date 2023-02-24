from data_base.sqlite3_class import DataBase
from bot_trading_class import RunBot

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    TextSendMessage, TemplateSendMessage, CarouselTemplate,
    CarouselColumn,  MessageAction, ConfirmTemplate
)

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = 'rtFZESyqSd0SH9OfGoa4KSWEu61LzpcgZcrSAUEsEKp3WdEJx7ajtmWMZMhVp0/f3UzBwqN8d0+VSntWTUIZVf4xglGc2j5NhuUvQiJ6eHlbMmQoP984ywbOpkOEz5n1ksZa1Ut2MSLBODLSI4TQAwdB04t89/1O/w1cDnyilFU='
YOUR_CHANNEL_SECRET = '996a6ec0b9f820399b13d29f3fb79a91'

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route('/')
def hello():
    return 'Hello, World', 200

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'POST':
        req = request.json
        message = req['events'][0]['message']['text']
        reply_token = req['events'][0]['replyToken']
        reply_message(message, reply_token)
        return req, 200

    elif request.method == 'GET':
        return 'Web hook', 200

def reply_message(message, reply_token):
    db = DataBase('users.db')
    users = db.fetch_all()
    print(message)

    # Manual trading carousel template message
    if message == 'Manual':
        carousel_template_message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=user[2],
                    title=user[3],
                    text=user[1],
                    actions=[
                        MessageAction(
                            label='Trade',
                            text= user[3] + '-Trade'
                        ), 
                        MessageAction(
                            label='Cancel',
                            text= user[3] + '-Cancel'
                        ), 
                    ]
                ) for user in users
            ]
        )
    )
        line_bot_api.reply_message(reply_token, carousel_template_message)
    
    # Fire sell carousel template message 
    elif message == 'Fire':
        carousel_template_message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=user[2],
                    title=user[3],
                    text=user[1],
                    actions=[
                        MessageAction(
                            label='Fire sale',
                            text= user[3] + '-Fire'
                        ), 
                    ]
                ) for user in users
            ]
        )
    )
        line_bot_api.reply_message(reply_token, carousel_template_message)
    
    # Summary report carousel template message 
    elif message == 'Report':
        carousel_template_message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url=user[2],
                    title=user[3],
                    text=user[1],
                    actions=[
                        MessageAction(
                            label='Report',
                            text= user[3] + '-Report'
                        ), 
                        MessageAction(
                            label='Details',
                            text= user[3] + '-Details'
                        ), 
                    ]
                ) for user in users
            ]
        )
    )
        line_bot_api.reply_message(reply_token, carousel_template_message)
    
    elif '-' in message:
        subaccount = message.split('-')[0]
        action = message.split('-')[1]

        select_user = db.select_data('subaccount', subaccount)[0]
        
        bot = RunBot(
                    api_key = select_user[5], 
                    api_secret = select_user[6], 
                    subaccount = select_user[3], 
                    symbol = select_user[4], 
                    postOnly = int(select_user[7]),
                    capital = select_user[8], 
                    leverage = select_user[9],
                    up_zone = select_user[10], 
                    down_zone = select_user[11], 
                    min_delta = select_user[12], 
                    min_pct = select_user[13],
                    allow_live_trading = int(select_user[14])
                )

        if action == 'Report':
            text_message = TextSendMessage(text=bot.send_report())
            line_bot_api.reply_message(reply_token, text_message)
        
        elif action == 'Details':
            text_message = TextSendMessage(text=bot.send_lev_details())
            line_bot_api.reply_message(reply_token, text_message)

        elif action == 'Trade':
            text_message = TextSendMessage(text=bot.trade())
            line_bot_api.reply_message(reply_token, text_message)

        elif action == 'Cancel':
            text_message = TextSendMessage(text=bot.cancel_orders())
            line_bot_api.reply_message(reply_token, text_message)
        
        elif action == 'Fire': 
            confirm_template_message = TemplateSendMessage(
                alt_text='Confirm template',
                template=ConfirmTemplate(
                    text='{}; Are you sure to fire sale?'.format(select_user[3]),
                    actions=[
                        MessageAction(
                            label='Yes',
                            text=select_user[3] + '-Confirm'
                        ),
                        MessageAction(
                            label='No',
                            text='Fire'
                        )
                    ]
                )
            )
            line_bot_api.reply_message(reply_token, confirm_template_message)

        elif action == 'Confirm':
            text_message = TextSendMessage(text=bot.fire_sale())
            line_bot_api.reply_message(reply_token, text_message)


if __name__ == '__main__':

    app.run(debug=True, port=1997)
